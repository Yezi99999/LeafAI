import json
from pathlib import Path
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.db.models import AIModel, User
from app.schemas.admin import ModelResponse
from app.schemas.common import BaseResponse
from app.api.v1.deps import get_current_user
from app.db.models import FeatureToggle, SystemConfig, _DEFAULT_API_DOCS

router = APIRouter(prefix="/config", tags=["配置"])

_RESOLUTION_CONFIG_PATH = Path(__file__).parent.parent.parent.parent / "分辨率.json"


@router.get("/resolutions", response_model=BaseResponse)
async def get_resolutions():
    if _RESOLUTION_CONFIG_PATH.exists():
        with open(_RESOLUTION_CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = {"aspect_ratios": []}

    return BaseResponse(data=data)


@router.get("/models", response_model=BaseResponse)
async def list_enabled_models(
    category: str = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """C 端公开只读：返回已启用模型，供模型选择器使用（不暴露管理字段）。"""
    query = select(AIModel).where(AIModel.is_enabled == True)  # noqa: E712
    if category:
        query = query.where(AIModel.category == category)
    query = query.order_by(AIModel.id)
    result = await db.execute(query)
    models = result.scalars().all()
    return BaseResponse(data={
        "items": [ModelResponse.model_validate(m) for m in models],
        "total": len(models),
    })


@router.get("/features", response_model=BaseResponse)
async def list_available_features(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """C 端只读：返回当前用户可用的功能代码（总开关+白名单共同决定）。

    对应 relation: 能力标识 image_generate / video_generate / chat / audio 等。
    """
    result = await db.execute(select(FeatureToggle).where(FeatureToggle.enabled == True))  # noqa: E712
    toggles = result.scalars().all()
    codes = []
    for t in toggles:
        wl = t.whitelist_user_ids or []
        if not wl or current_user.id in wl:
            codes.append(t.code)
    return BaseResponse(data={"items": codes, "total": len(codes)})


@router.get("/item", response_model=BaseResponse)
async def get_config_item(
    key: str,
    db: AsyncSession = Depends(get_db),
):
    """C 端只读：读取后台配置的站点内容（如 api-docs）。未配置时返回内置默认值。"""
    defaults = {"api-docs": _DEFAULT_API_DOCS}
    result = await db.execute(select(SystemConfig).where(SystemConfig.key == key))
    cfg = result.scalar_one_or_none()
    if cfg is not None:
        value = cfg.value
    else:
        value = defaults.get(key)
    return BaseResponse(data={"key": key, "value": value})