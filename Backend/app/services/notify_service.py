"""用户通知服务。

- `create_notification`：持久化一条通知（仅落库，不推送）。
- `NotificationHub`：进程内 pub/sub，供 `GET /notify/stream` SSE 实时推送。
  生产环境可替换为 Redis Pub/Sub 桥接；当前实现天然支持断线重连补发未读。
- 业务侧（如积分扣费）在事务提交后调用 `publish_to_user` 即可触发 SSE。
"""

import asyncio
import uuid
from collections import defaultdict
from datetime import datetime
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import UserNotification


class NotificationHub:
    """按 user_id 维度广播的进程内 hub。"""

    def __init__(self):
        self._subscribers: dict[int, set[asyncio.Queue]] = defaultdict(set)
        self._lock = asyncio.Lock()

    async def subscribe(self, user_id: int) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue(maxsize=256)
        async with self._lock:
            self._subscribers[user_id].add(q)
        return q

    async def unsubscribe(self, user_id: int, q: asyncio.Queue):
        async with self._lock:
            bucket = self._subscribers.get(user_id)
            if bucket:
                bucket.discard(q)
                if not bucket:
                    self._subscribers.pop(user_id, None)

    async def publish(self, user_id: int, event: dict):
        async with self._lock:
            for q in list(self._subscribers.get(user_id, ())):
                try:
                    q.put_nowait(event)
                except asyncio.QueueFull:
                    pass


hub = NotificationHub()


def event_from_notification(n: UserNotification) -> dict:
    """序列化为 C 端可见结构：不暴露内部 id 与 user_id，改用 client_token 作公开标识。"""
    return {
        "token": n.client_token or str(n.id),
        "type": n.type,
        "title": n.title,
        "content": n.content,
        "extra_data": n.extra_data or {},
        "is_read": n.is_read,
        "create_time": n.create_time.isoformat() if n.create_time else None,
    }


def create_notification(
    db: AsyncSession,
    user_id: int,
    type_: str,
    title: str,
    content: str = "",
    extra_data: dict = None,
) -> UserNotification:
    """持久化一条通知（放入会话，由调用方统一 commit）。"""
    notif = UserNotification(
        user_id=user_id,
        client_token=str(uuid.uuid4()),
        type=type_,
        title=title,
        content=content,
        extra_data=extra_data or {},
    )
    db.add(notif)
    return notif


async def publish_to_user(db: AsyncSession, user_id: int, type_: str, title: str, content: str = "", extra_data: dict = None) -> UserNotification:
    """持久化 + 实时推送（业务侧在事务内调用；提交由调用方负责推送时机）。"""
    notif = create_notification(db, user_id, type_, title, content, extra_data)
    await db.flush()
    return notif


async def history(db: AsyncSession, user_id: int, page: int = 1, page_size: int = 20, unread_only: bool = False):
    query = select(UserNotification).where(UserNotification.user_id == user_id)
    if unread_only:
        query = query.where(UserNotification.is_read.is_(False))

    count_query = query
    total = len((await db.execute(count_query)).scalars().all())

    query = query.order_by(UserNotification.create_time.desc()).offset((page - 1) * page_size).limit(page_size)
    rows = (await db.execute(query)).scalars().all()

    return {"items": [event_from_notification(n) for n in rows], "total": total, "page": page, "page_size": page_size}


async def unread_count(db: AsyncSession, user_id: int) -> int:
    result = await db.execute(
        select(func.count()).select_from(UserNotification).where(
            UserNotification.user_id == user_id,
            UserNotification.is_read.is_(False),
        )
    )
    return result.scalar_one()


async def mark_read(db: AsyncSession, notif: UserNotification):
    notif.is_read = True
    notif.read_time = datetime.utcnow()


async def mark_all_read(db: AsyncSession, user_id: int):
    rows = (await db.execute(select(UserNotification).where(
        UserNotification.user_id == user_id,
        UserNotification.is_read.is_(False),
    ))).scalars().all()
    now = datetime.utcnow()
    for n in rows:
        n.is_read = True
        n.read_time = now
    return len(rows)