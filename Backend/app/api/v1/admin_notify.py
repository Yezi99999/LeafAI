from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.db.models import User, UserNotification, OperationLog
from app.schemas.admin import NotificationBroadcastRequest
from app.schemas.common import BaseResponse
from app.api.v1.deps import get_current_superuser
from app.services import notify_service

router = APIRouter(
    prefix="/admin/notifications",
    tags=["管理后台-通知"],
    dependencies=[Depends(get_current_superuser)],
)


def _admin_event(n: UserNotification) -> dict:
    """管理端序列化：在 C 端基础上保留内部 id 与 user_id（管理端可见）。"""
    return {**notify_service.event_from_notification(n), "id": n.id, "user_id": n.user_id}


@router.get("", response_model=BaseResponse)
async def list_notifications(
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
):
    query = select(UserNotification).order_by(UserNotification.id.desc()).offset((page - 1) * page_size).limit(page_size)
    rows = (await db.execute(query)).scalars().all()
    total = len((await db.execute(select(UserNotification.id))).scalars().all())
    return BaseResponse(data={
        "items": [_admin_event(n) for n in rows],
        "total": total,
        "page": page,
        "page_size": page_size,
    })


@router.post("/broadcast", response_model=BaseResponse)
async def broadcast_notification(
    req: NotificationBroadcastRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_superuser),
):
    # 解析接收者：指定 user_ids 则按指定，否则全量用户
    if req.user_ids:
        target_ids = sorted(set(req.user_ids))
    else:
        result = await db.execute(select(User.id))
        target_ids = result.scalars().all()

    if not target_ids:
        raise HTTPException(status_code=400, detail="没有可接收通知的用户")

    notifs = [
        notify_service.create_notification(db, uid, req.type, req.title, req.content, req.extra_data)
        for uid in target_ids
    ]
    # 先 flush 拿到自增 id/create_time，再实时推送（否则 SSE 事件缺 id）
    await db.flush()
    for notif in notifs:
        await notify_service.hub.publish(notif.user_id, notify_service.event_from_notification(notif))

    db.add(OperationLog(
        admin_user_id=admin.id,
        module="notifications",
        action="broadcast",
        target_id=str(len(target_ids)),
        detail={"type": req.type, "title": req.title, "recipients": len(target_ids)},
        ip=request.client.host if request and request.client else None,
        user_agent=request.headers.get("user-agent") if request else None,
    ))
    await db.commit()
    return BaseResponse(data={"recipients": len(target_ids)})