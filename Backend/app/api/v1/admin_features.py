from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.db.models import FeatureToggle
from app.schemas.admin import (
    FeatureToggleCreate, FeatureToggleUpdate, FeatureToggleResponse,
)
from app.schemas.common import BaseResponse
from app.api.v1.deps import get_current_superuser, get_current_user_optional
from app.services.toggle_service import set_toggle, is_enabled

admin_router = APIRouter(
    prefix="/admin/features",
    tags=["功能开关"],
    dependencies=[Depends(get_current_superuser)],
)

# C 端校验接口挂在 /features 前缀下供业务入口调用（无需超管）
client_router = APIRouter(prefix="/features", tags=["功能开关"])


@admin_router.get("", response_model=BaseResponse)
async def list_features(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(FeatureToggle).order_by(FeatureToggle.id))
    toggles = result.scalars().all()
    return BaseResponse(data={
        "items": [FeatureToggleResponse.model_validate(t) for t in toggles],
        "total": len(toggles),
    })


@admin_router.post("", response_model=BaseResponse)
async def create_feature(
    req: FeatureToggleCreate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(FeatureToggle).where(FeatureToggle.code == req.code))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="开关标识已存在")

    toggle = FeatureToggle(
        code=req.code,
        name=req.name,
        enabled=req.enabled,
        whitelist_user_ids=req.whitelist_user_ids,
        description=req.description,
    )
    db.add(toggle)
    await db.flush()
    return BaseResponse(data=FeatureToggleResponse.model_validate(toggle))


@admin_router.put("/{code}", response_model=BaseResponse)
async def update_feature(
    code: str,
    req: FeatureToggleUpdate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(FeatureToggle).where(FeatureToggle.code == code))
    toggle = result.scalar_one_or_none()
    if toggle is None:
        raise HTTPException(status_code=404, detail="开关不存在")

    update_data = req.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(toggle, key, value)

    await db.flush()
    set_toggle(db, toggle)
    return BaseResponse(data=FeatureToggleResponse.model_validate(toggle))


@admin_router.delete("/{code}", response_model=BaseResponse)
async def delete_feature(
    code: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(FeatureToggle).where(FeatureToggle.code == code))
    toggle = result.scalar_one_or_none()
    if toggle is None:
        raise HTTPException(status_code=404, detail="开关不存在")
    await db.delete(toggle)
    return BaseResponse(msg="开关已删除")


@client_router.get("/{code}", response_model=BaseResponse)
async def check_feature(
    code: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user_optional),
):
    """C 端：校验某能力对当前用户是否可用（未登录按全量/白名单逻辑处理）。"""
    from app.db.models import User
    user = current_user if isinstance(current_user, User) else None
    enabled = await is_enabled(db, code, user) if user is not None else True
    if user is None:
        # 未登录时不拦截（登录后由各业务接口再次校验）
        enabled = True
    available = enabled
    return BaseResponse(data={"code": code, "enabled": available})