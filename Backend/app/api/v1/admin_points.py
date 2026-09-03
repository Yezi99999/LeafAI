from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.db.session import get_db
from app.db.models import PointsConsumptionRate, PointsTransaction, User, AIModel, OperationLog
from app.schemas.admin import (
    RateCreate, RateUpdate, RateResponse,
    RechargeRequest, TransactionResponse,
    ModelPointsUpdate, ModelPointsResponse, TransactionWithUser,
)
from app.schemas.common import BaseResponse
from app.api.v1.deps import get_current_superuser
from app.services import points_service


router = APIRouter(
    prefix="/admin/points",
    tags=["管理后台-积分"],
    dependencies=[Depends(get_current_superuser)],
)


async def _write_log(db: AsyncSession, admin: User, action: str, target_id: str, detail: dict = None, request: Request = None):
    db.add(OperationLog(
        admin_user_id=admin.id,
        module="points",
        action=action,
        target_id=target_id,
        detail=detail or {},
        ip=request.client.host if request and request.client else None,
        user_agent=request.headers.get("user-agent") if request else None,
    ))
    await db.flush()


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


@router.get("/rates", response_model=BaseResponse)
async def list_rates(
    service_code: str = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(PointsConsumptionRate).order_by(PointsConsumptionRate.id)
    if service_code:
        query = query.where(PointsConsumptionRate.service_code == service_code)
    result = await db.execute(query)
    rates = result.scalars().all()

    # 模型显示名（FeeRate for 模型级）
    model_names = {}
    if any(r.model_id for r in rates):
        mids = [r.model_id for r in rates if r.model_id]
        mrows = (await db.execute(select(AIModel.id, AIModel.display_name, AIModel.model_name)
                                  .where(AIModel.id.in_(mids)))).all()
        model_names = {mid: (dn, mn) for mid, dn, mn in mrows}

    items = []
    for r in rates:
        d = RateResponse.model_validate(r)
        items.append({
            **d.model_dump(),
            "service_label": SERVICE_LABELS.get(r.service_code, r.service_code),
            "unit_label": UNIT_LABELS.get(r.rate_unit, r.rate_unit),
            "model_display": model_names.get(r.model_id, (None, None))[0] if r.model_id else None,
        })
    return BaseResponse(data={"items": items, "total": len(rates)})


SERVICE_LABELS = {
    "image_generate": "图片生成",
    "chat": "对话",
    "video_generate": "视频生成",
    "audio": "语音",
}
UNIT_LABELS = {
    "per_call": "次",
    "per_token": "token",
    "per_image": "张",
}


@router.post("/rates", response_model=BaseResponse)
async def create_rate(
    req: RateCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_superuser),
):
    # 同一 (service_code, model_id) 唯一（model_id 为空表服务默认）
    dup = await db.execute(
        select(PointsConsumptionRate).where(
            PointsConsumptionRate.service_code == req.service_code,
            PointsConsumptionRate.model_id == req.model_id,
        )
    )
    if dup.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="该服务已存在相同定价（服务默认或同一模型）")

    rate = PointsConsumptionRate(
        service_code=req.service_code,
        multiplier=req.multiplier,
        rate_unit=req.rate_unit,
        model_id=req.model_id,
        enabled=req.enabled,
    )
    db.add(rate)
    await db.flush()
    await _write_log(db, admin, "create", str(rate.id),
                     {"service_code": rate.service_code, "multiplier": rate.multiplier}, request)
    await db.commit()
    return BaseResponse(data=RateResponse.model_validate(rate))


@router.put("/rates/{rate_id}", response_model=BaseResponse)
async def update_rate(
    rate_id: int,
    req: RateUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_superuser),
):
    result = await db.execute(select(PointsConsumptionRate).where(PointsConsumptionRate.id == rate_id))
    rate = result.scalar_one_or_none()
    if rate is None:
        raise HTTPException(status_code=404, detail="费率不存在")

    changes = req.model_dump(exclude_unset=True)
    for key, value in changes.items():
        setattr(rate, key, value)

    await db.flush()
    await _write_log(db, admin, "update", str(rate.id), changes, request)
    await db.commit()
    return BaseResponse(data=RateResponse.model_validate(rate))


@router.delete("/rates/{rate_id}", response_model=BaseResponse)
async def delete_rate(
    rate_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_superuser),
):
    result = await db.execute(select(PointsConsumptionRate).where(PointsConsumptionRate.id == rate_id))
    rate = result.scalar_one_or_none()
    if rate is None:
        raise HTTPException(status_code=404, detail="费率不存在")
    await db.delete(rate)
    await _write_log(db, admin, "delete", str(rate_id), {}, request)
    await db.commit()
    return BaseResponse(msg="费率已删除")


@router.post("/recharge", response_model=BaseResponse)
async def recharge(
    req: RechargeRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_superuser),
):
    result = await db.execute(select(User).where(User.id == req.user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="用户不存在")

    if req.points_delta > 0:
        new_balance = await points_service.grant_recharge(db, user, req.points_delta, req.remark)
        tx_type = points_service.TX_RECHARGE
    elif req.points_delta < 0:
        new_balance = await points_service.adjust_balance(db, user, req.points_delta, req.remark)
        tx_type = points_service.TX_ADJUST
    else:
        raise HTTPException(status_code=400, detail="积分增减不能为 0")

    await _write_log(db, admin, "recharge", str(user.id), {"points_delta": req.points_delta, "balance_after": new_balance}, request)
    await db.commit()
    return BaseResponse(data={
        "user_id": user.id,
        "username": user.username,
        "points_delta": req.points_delta,
        "tx_type": tx_type,
        "balance_after": new_balance,
    })


@router.get("/transactions", response_model=BaseResponse)
async def list_transactions(
    user_id: int = None,
    service_code: str = None,
    tx_type: str = None,
    start: str = None,
    end: str = None,
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
):
    query = select(PointsTransaction)
    if user_id:
        query = query.where(PointsTransaction.user_id == user_id)
    if service_code:
        query = query.where(PointsTransaction.service_code == service_code)
    if tx_type:
        query = query.where(PointsTransaction.tx_type == tx_type)
    if start:
        query = query.where(PointsTransaction.create_time >= _parse_date(start))
    if end:
        query = query.where(PointsTransaction.create_time <= _parse_date(end, end=True))

    count_query = query
    total = (await db.execute(count_query)).scalars().all()

    query = query.order_by(PointsTransaction.id.desc()).offset((page - 1) * page_size).limit(page_size)
    rows = (await db.execute(query)).scalars().all()

    return BaseResponse(data={
        "items": [TransactionResponse.model_validate(t) for t in rows],
        "total": len(total),
        "page": page,
        "page_size": page_size,
    })


@router.get("/summary", response_model=BaseResponse)
async def summary(
    start: str = None,
    end: str = None,
    db: AsyncSession = Depends(get_db),
):
    s = _parse_date(start)
    e = _parse_date(end, end=True)
    service = await points_service.service_summary(db, s, e)
    daily = await points_service.daily_summary(db, s, e)
    return BaseResponse(data={"service": service, "daily": daily})


@router.get("/orders", response_model=BaseResponse)
async def list_records(
    user_id: int = None,
    username: str = None,
    service_code: str = None,
    tx_type: str = None,
    start: str = None,
    end: str = None,
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
):
    """仿订单的积分流水列表（含用户名，可按用户名/服务/类型/时间筛选）。"""
    query = select(PointsTransaction, User.username).join(User, User.id == PointsTransaction.user_id)
    if user_id:
        query = query.where(PointsTransaction.user_id == user_id)
    if username:
        query = query.where(User.username.like(f"%{username}%"))
    if service_code:
        query = query.where(PointsTransaction.service_code == service_code)
    if tx_type:
        query = query.where(PointsTransaction.tx_type == tx_type)
    if start:
        query = query.where(PointsTransaction.create_time >= _parse_date(start))
    if end:
        query = query.where(PointsTransaction.create_time <= _parse_date(end, end=True))

    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar_one()

    rows = (await db.execute(
        query.order_by(PointsTransaction.id.desc()).offset((page - 1) * page_size).limit(page_size)
    )).all()

    items = [
        TransactionWithUser(
            id=t.id, user_id=t.user_id, username=username_row,
            tx_type=t.tx_type, points_delta=t.points_delta, service_code=t.service_code,
            task_id=t.task_id, model_id=t.model_id, balance_after=t.balance_after,
            remark=t.remark, create_time=t.create_time,
        )
        for t, username_row in rows
    ]
    return BaseResponse(data={"items": items, "total": total, "page": page, "page_size": page_size})


@router.get("/models", response_model=BaseResponse)
async def list_model_points(db: AsyncSession = Depends(get_db)):
    """列出已有模型及其当前积分消耗，供管理端修改。"""
    rows = (await db.execute(
        select(AIModel).order_by(AIModel.category, AIModel.id)
    )).scalars().all()
    return BaseResponse(data={
        "items": [ModelPointsResponse.model_validate(m) for m in rows],
        "total": len(rows),
    })


@router.put("/models/{model_id}", response_model=BaseResponse)
async def update_model_points(
    model_id: int,
    req: ModelPointsUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_superuser),
):
    """修改已有模型单次调用消耗积分。"""
    model = await db.get(AIModel, model_id)
    if model is None:
        raise HTTPException(status_code=404, detail="模型不存在")
    old = model.unit_points
    model.unit_points = req.unit_points
    await db.flush()
    await _write_log(db, admin, "update_model_points", str(model.id),
                     {"model": model.display_name, "unit_points": {"old": old, "new": req.unit_points}}, request)
    await db.commit()
    return BaseResponse(data={"id": model.id, "display_name": model.display_name, "unit_points": model.unit_points})