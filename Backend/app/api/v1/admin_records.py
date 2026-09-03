from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.db.session import get_db
from app.db.models import AITask, AIChatSession, AIChatMessage, User, AIModel
from app.schemas.common import BaseResponse
from app.api.v1.deps import get_current_superuser

router = APIRouter(
    prefix="/admin/records",
    tags=["管理后台-调用记录"],
    dependencies=[Depends(get_current_superuser)],
)

SERVICE_LABELS = {
    "image_generate": "图片生成",
    "video_generate": "视频生成",
    "audio": "语音生成",
    "chat": "对话",
}


def _parse_date(value: str = None, end: bool = False):
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(value)
    except ValueError:
        return None
    if end:
        return dt.replace(hour=23, minute=59, second=59, microsecond=999999)
    return dt.replace(hour=0, minute=0, second=0, microsecond=0)


@router.get("", response_model=BaseResponse)
async def list_call_records(
    user_id: int = None,
    username: str = None,
    service_code: str = None,
    start: str = None,
    end: str = None,
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
):
    """统一调用记录：合并图片/视频/语音任务(AITask)与对话会话(AIChatSession)，
    只要发生过调用即展示，无论是否消耗积分。"""
    s = _parse_date(start)
    e = _parse_date(end, end=True)

    # 用户名 → user_id 解析（用于按用户名过滤）
    username_ids: list[int] = []
    if username:
        rows = (await db.execute(select(User.id).where(User.username.like(f"%{username}%")))).scalars().all()
        username_ids = list(rows)
        if not username_ids:
            return BaseResponse(data={"items": [], "total": 0, "page": page, "page_size": page_size})

    def _uid_filter(uid_col):
        conds = []
        if user_id:
            conds.append(uid_col == user_id)
        if username_ids:
            conds.append(uid_col.in_(username_ids))
        return conds

    records = []

    # 1) 图片/视频/语音任务
    task_q = select(AITask, User.username, AIModel.display_name, AIModel.model_name).join(
        User, User.id == AITask.user_id
    ).outerjoin(AIModel, AIModel.id == AITask.model_id)
    for cond in _uid_filter(AITask.user_id):
        task_q = task_q.where(cond)
    if s:
        task_q = task_q.where(AITask.create_time >= s)
    if e:
        task_q = task_q.where(AITask.create_time <= e)
    task_rows = (await db.execute(task_q)).all()
    for task, uname, m_display, m_name in task_rows:
        records.append({
            "service_code": task.category or "image_generate",
            "kind": "task",
            "ref_id": task.task_id,
            "user_id": task.user_id,
            "username": uname,
            "model_name": m_display or m_name,
            "title": (task.input_params or {}).get("prompt", "") or "",
            "status": str(task.status.value) if hasattr(task.status, "value") else str(task.status),
            "message_count": None,
            "points": None,
            "create_time": task.create_time,
        })

    # 2) 对话会话（一次会话视为一次调用）
    ses_q = select(AIChatSession, User.username, AIModel.display_name, AIModel.model_name).join(
        User, User.id == AIChatSession.user_id
    ).outerjoin(AIModel, AIModel.id == AIChatSession.model_id)
    for cond in _uid_filter(AIChatSession.user_id):
        ses_q = ses_q.where(cond)
    if s:
        ses_q = ses_q.where(AIChatSession.create_time >= s)
    if e:
        ses_q = ses_q.where(AIChatSession.create_time <= e)
    ses_rows = (await db.execute(ses_q)).all()
    session_ids = [row[0].id for row in ses_rows]
    # 会话消息条数
    msg_counts: dict[str, int] = {}
    if session_ids:
        msgs = (await db.execute(
            select(AIChatMessage.session_id, func.count(AIChatMessage.id))
            .where(AIChatMessage.session_id.in_(session_ids))
            .group_by(AIChatMessage.session_id)
        )).all()
        msg_counts = {sid: cnt for sid, cnt in msgs}

    for ses, uname, m_display, m_name in ses_rows:
        records.append({
            "service_code": "chat",
            "kind": "chat",
            "ref_id": ses.id,
            "user_id": ses.user_id,
            "username": uname,
            "model_name": m_display or m_name,
            "title": ses.title or "对话",
            "status": "success",
            "message_count": msg_counts.get(ses.id, 0),
            "points": None,
            "create_time": ses.create_time,
        })

    # 按 service_code 过滤（chat / image_generate ...）
    if service_code:
        records = [r for r in records if r["service_code"] == service_code]

    records.sort(key=lambda r: r["create_time"] or datetime.min, reverse=True)

    total = len(records)
    items = records[(page - 1) * page_size: page * page_size]
    for it in items:
        if it["create_time"]:
            it["create_time"] = it["create_time"].isoformat() if hasattr(it["create_time"], "isoformat") else str(it["create_time"])
    return BaseResponse(data={
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
    })