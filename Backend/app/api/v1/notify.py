import asyncio
import json
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db, async_session_factory
from app.db.models import User, UserNotification
from app.schemas.common import BaseResponse
from app.api.v1.deps import get_current_user, get_current_user_sse
from app.services import notify_service
from app.services.notify_service import hub

router = APIRouter(prefix="/notify", tags=["通知"])

SSE_HEADERS = {
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "X-Accel-Buffering": "no",
}


@router.get("/stream")
async def notify_stream(
    current_user: User = Depends(get_current_user_sse),
):
    async def event_generator():
        q = await hub.subscribe(current_user.id)
        try:
            # 断线重连补发未读
            async with async_session_factory() as db:
                hist = await notify_service.history(db, current_user.id, page_size=50, unread_only=True)
                for item in hist["items"]:
                    payload = dict(item)
                    payload["replay"] = True
                    yield f"event: {payload.get('type','message')}\ndata: {json.dumps(payload, ensure_ascii=False, default=str)}\n\n"

            while True:
                try:
                    event = await asyncio.wait_for(q.get(), timeout=25)
                except asyncio.TimeoutError:
                    yield ": keep-alive\n\n"
                    continue
                yield f"event: {event.get('type','message')}\ndata: {json.dumps(event, ensure_ascii=False, default=str)}\n\n"
        finally:
            await hub.unsubscribe(current_user.id, q)

    return StreamingResponse(event_generator(), media_type="text/event-stream", headers=SSE_HEADERS)


@router.get("/history", response_model=BaseResponse)
async def notify_history(
    page: int = 1,
    page_size: int = 20,
    unread_only: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    data = await notify_service.history(db, current_user.id, page=page, page_size=page_size, unread_only=unread_only)
    return BaseResponse(data=data)


@router.get("/unread-count", response_model=BaseResponse)
async def notify_unread_count(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    count = await notify_service.unread_count(db, current_user.id)
    return BaseResponse(data={"count": count})


@router.patch("/read/{token}", response_model=BaseResponse)
async def notify_read(
    token: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(UserNotification).where(UserNotification.client_token == token))
    notif = result.scalar_one_or_none()
    if notif is None or notif.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="通知不存在")
    await notify_service.mark_read(db, notif)
    await db.commit()
    return BaseResponse(data=notify_service.event_from_notification(notif))


@router.patch("/read-all", response_model=BaseResponse)
async def notify_read_all(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    count = await notify_service.mark_all_read(db, current_user.id)
    await db.commit()
    return BaseResponse(data={"mark_read": count})