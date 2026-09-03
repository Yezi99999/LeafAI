from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.db.models import User
from app.schemas.common import BaseResponse
from app.api.v1.deps import get_current_superuser
from app.services import analytics_service

router = APIRouter(
    prefix="/admin/analytics",
    tags=["管理后台-报表"],
    dependencies=[Depends(get_current_superuser)],
)


@router.get("/overview", response_model=BaseResponse)
async def analytics_overview(db: AsyncSession = Depends(get_db)):
    return BaseResponse(data=await analytics_service.overview(db))


@router.get("/users", response_model=BaseResponse)
async def analytics_users(days: int = 30, db: AsyncSession = Depends(get_db)):
    return BaseResponse(data=await analytics_service.users_trend(db, days))


@router.get("/usage", response_model=BaseResponse)
async def analytics_usage(db: AsyncSession = Depends(get_db)):
    return BaseResponse(data=await analytics_service.usage(db))


@router.get("/points", response_model=BaseResponse)
async def analytics_points(days: int = 30, service_code: str | None = None, db: AsyncSession = Depends(get_db)):
    return BaseResponse(data=await analytics_service.points_trend(db, days, service_code))


@router.get("/performance", response_model=BaseResponse)
async def analytics_performance(db: AsyncSession = Depends(get_db)):
    return BaseResponse(data=await analytics_service.performance(db))


@router.get("/services", response_model=BaseResponse)
async def analytics_services(db: AsyncSession = Depends(get_db)):
    return BaseResponse(data=await analytics_service.services(db))