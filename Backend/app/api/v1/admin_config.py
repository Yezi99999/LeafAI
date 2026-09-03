from typing import Any
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.db.models import User, SystemConfig, OperationLog
from app.schemas.common import BaseResponse
from app.api.v1.deps import get_current_superuser

router = APIRouter(prefix="/admin/configs", tags=["管理后台-系统配置"])


class ConfigValue(BaseModel):
    value: Any = Field(..., description="配置值（JSON 等价结构）")


@router.get("", response_model=BaseResponse)
async def list_configs(
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_superuser),
):
    rows = (await db.execute(select(SystemConfig).order_by(SystemConfig.key))).scalars().all()
    return BaseResponse(data={"items": [
        {"key": c.key, "value": c.value, "update_time": c.update_time} for c in rows
    ], "total": len(rows)})


@router.put("/{key}", response_model=BaseResponse)
async def update_config(
    key: str,
    payload: ConfigValue,
    request: Request,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_superuser),
):
    row = (await db.execute(select(SystemConfig).where(SystemConfig.key == key))).scalar_one_or_none()
    if row is None:
        row = SystemConfig(key=key, value=payload.value)
        db.add(row)
    else:
        row.value = payload.value
    await db.flush()
    db.add(OperationLog(
        admin_user_id=admin.id,
        module="config",
        action="update",
        target_id=key,
        detail={"key": key},
        ip=request.client.host if request and request.client else None,
        user_agent=request.headers.get("user-agent") if request else None,
    ))
    await db.flush()
    await db.commit()
    return BaseResponse(data={"key": key, "value": row.value})