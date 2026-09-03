from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.db.session import get_db
from app.db.models import OperationLog, User
from app.schemas.common import BaseResponse
from app.api.v1.deps import get_current_superuser

router = APIRouter(
    prefix="/admin/audit-logs",
    tags=["管理后台-操作审计"],
    dependencies=[Depends(get_current_superuser)],
)


@router.get("", response_model=BaseResponse)
async def list_audit_logs(
    page: int = 1,
    page_size: int = 20,
    module: str | None = Query(None, description="模块筛选"),
    operator: str | None = Query(None, description="操作者用户名筛选"),
    db: AsyncSession = Depends(get_db),
):
    query = select(OperationLog, User.username).join(User, User.id == OperationLog.admin_user_id)
    if module:
        query = query.where(OperationLog.module == module)
    if operator:
        query = query.where(User.username.like(f"%{operator}%"))

    total = (await db.execute(
        select(func.count()).select_from(query.subquery())
    )).scalar_one()

    rows = (await db.execute(
        query.order_by(OperationLog.id.desc())
        .offset((page - 1) * page_size).limit(page_size)
    )).all()

    items = [
        {
            "id": log.id,
            "operator": username,
            "admin_user_id": log.admin_user_id,
            "module": log.module,
            "action": log.action,
            "target_id": log.target_id,
            "detail": log.detail,
            "ip": log.ip,
            "user_agent": log.user_agent,
            "create_time": log.create_time.isoformat() if log.create_time else None,
        }
        for log, username in rows
    ]
    return BaseResponse(data={"items": items, "total": total, "page": page, "page_size": page_size})