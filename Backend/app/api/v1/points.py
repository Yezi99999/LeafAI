from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.db.session import get_db
from app.db.models import User, PointsTransaction
from app.schemas.common import BaseResponse
from app.api.v1.deps import get_current_user

router = APIRouter(prefix="/points", tags=["积分"])


@router.get("/records", response_model=BaseResponse)
async def my_points_records(
    direction: str = "out",  # out=消耗(负变动) / in=充值(正变动)
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """C 端只读：当前用户的积分流水。direction=out 返回消费记录，in 返回充值/返还记录。"""
    query = select(PointsTransaction).where(PointsTransaction.user_id == current_user.id)
    if direction == "out":
        query = query.where(PointsTransaction.points_delta < 0)
    else:
        query = query.where(PointsTransaction.points_delta > 0)
    page = max(1, page)
    page_size = min(max(1, page_size), 100)

    total = (await db.execute(
        select(func.count()).select_from(query.subquery())
    )).scalar_one()

    rows = (await db.execute(
        query.order_by(PointsTransaction.id.desc()).offset((page - 1) * page_size).limit(page_size)
    )).scalars().all()

    from app.schemas.admin import TransactionResponse
    items = [TransactionResponse.model_validate(t) for t in rows]
    return BaseResponse(data={
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
    })