"""功能开关服务：集中启停对话/图片/视频等多模态能力。

- 数据源：`feature_toggle` 表。
- 语义：`enabled` 总开关；`whitelist_user_ids` 灰度白名单（空=全量，列表则仅名单内 + 超管可用）。
- 缓存：进程内 TTL 缓存（默认 30s），写操作主动失效，避免热路径每次查库。
"""

import time
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models import FeatureToggle, User

CACHE_TTL = 30  # 秒

_cache: dict = {}


def _cache_get(code: str):
    item = _cache.get(code)
    if not item:
        return None
    if item["expire_at"] < time.time():
        _cache.pop(code, None)
        return None
    return item["value"]


def _cache_set(code: str, value):
    _cache[code] = {"value": value, "expire_at": time.time() + CACHE_TTL}


def invalidate(code: str):
    _cache.pop(code, None)


async def get_toggle(db: AsyncSession, code: str) -> Optional[FeatureToggle]:
    """查询开关（带进程内缓存；缓存未命中时 it TTL）。"""
    cached = _cache_get(code)
    if cached is not None:
        return cached
    result = await db.execute(select(FeatureToggle).where(FeatureToggle.code == code))
    toggle = result.scalar_one_or_none()
    _cache_set(code, toggle)
    return toggle


def _whitelist_ok(toggle: FeatureToggle, user: User) -> bool:
    if user.is_superuser:
        return True
    whitelist = toggle.whitelist_user_ids or []
    if not whitelist:
        return True
    return user.id in whitelist


async def is_enabled(db: AsyncSession, code: str, user: User) -> bool:
    """某能力对当前用户是否可用。

    未配置开关 → 默认开启。
    开关关闭 → 仅超管可用。
    开关开启 → 白名单为空=全量；否则仅白名单（或超管）。
    """
    toggle = await get_toggle(db, code)
    if toggle is None:
        return True
    if not toggle.enabled:
        return user.is_superuser
    return _whitelist_ok(toggle, user)


async def ensure_enabled(db: AsyncSession, code: str, user: User):
    """拦截入口：不可用时抛出 AppException(403)。"""
    if not await is_enabled(db, code, user):
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="该功能暂未开放")


async def list_toggles(db: AsyncSession):
    result = await db.execute(select(FeatureToggle).order_by(FeatureToggle.id))
    return result.scalars().all()


DEFAULT_TOGGLES = [
    ("chat", "智能对话", "控制对话聊天能力的启停"),
    ("image_generate", "图片生成", "控制图片生成能力的启停"),
    ("video_generate", "视频生成", "控制视频生成能力的启停"),
    ("audio_tts", "语音合成", "控制文本转语音(TTS)能力的启停"),
    ("audio_asr", "语音识别", "控制语音转文字(ASR)能力的启停"),
    ("points", "积分体系", "开关积分计费模式的启停"),
]


async def ensure_defaults(db: AsyncSession):
    """确保核心能力已预置开关，避免管理员手动逐个创建。"""
    for code, name, desc in DEFAULT_TOGGLES:
        result = await db.execute(select(FeatureToggle).where(FeatureToggle.code == code))
        if result.scalar_one_or_none() is None:
            db.add(FeatureToggle(code=code, name=name, description=desc, enabled=True))
    await db.flush()


async def set_toggle(db: AsyncSession, toggle: FeatureToggle):
    await db.flush()
    invalidate(toggle.code)