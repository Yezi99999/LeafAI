"""图片上传服务：读取上传限制配置（SystemConfig），提供默认值兜底。"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models import SystemConfig

DEFAULT_MAX_SIZE_MB = 5
DEFAULT_MAX_COUNT = 6

_UPLOAD_KEYS = ("upload_max_size_mb", "upload_max_count")


def _to_int(value, default: int) -> int:
    try:
        v = int(value)
        return v if v > 0 else default
    except (TypeError, ValueError):
        return default


async def get_upload_config(db: AsyncSession) -> dict:
    """读取图片上传限制；后台未配置时使用默认值。"""
    rows = (
        await db.execute(
            select(SystemConfig).where(SystemConfig.key.in_(_UPLOAD_KEYS))
        )
    ).scalars().all()
    cfg = {r.key: r.value for r in rows}
    return {
        "max_size_mb": _to_int(cfg.get("upload_max_size_mb"), DEFAULT_MAX_SIZE_MB),
        "max_count": _to_int(cfg.get("upload_max_count"), DEFAULT_MAX_COUNT),
    }