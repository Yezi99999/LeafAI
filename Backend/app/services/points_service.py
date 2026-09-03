"""积分费率与流水服务。

- 费率表 `points_consumption_rate`：按 `service_code` 默认定价，可按 `model_id` 覆盖。
- 流水表 `points_transaction`：只追加，记录每次积分/免费额度变动快照。
- 汇总：按服务 / 按日消费统计。
"""

from sqlalchemy import select, func, case
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import PointsConsumptionRate, PointsTransaction, User, AIModel


# 流水类型
TX_RECHARGE = "recharge"        # 充值
TX_CONSUME = "consume"          # 消费
TX_REFUND = "refund"            # 返还
TX_ADJUST = "admin_adjust"      # 人工调整

# 能力分类 -> 计费服务代码
CATEGORY_SERVICE = {
    "image": "image_generate",
    "chat": "chat",
    "video": "video_generate",
    "audio": "audio",
}


async def effective_unit_points(db: AsyncSession, category: str, model: AIModel) -> int:
    """按费率倍率计算单次实际消耗积分 = 模型 unit_points × 倍率。

    找到对应模型级或服务默认的启用费率则相乘，否则退回模型 unit_points。
    """
    service_code = CATEGORY_SERVICE.get(category)
    unit = max(0, model.unit_points or 0)
    if not service_code:
        return unit
    rate = await active_rate(db, service_code, model.id)
    if rate is None:
        return unit
    multiplier = max(0.0, rate.multiplier or 1.0)
    return round(unit * multiplier)


async def active_rate(db: AsyncSession, service_code: str, model_id: int = None):
    """查询某服务（可选按模型覆盖）的启用费率。返回费率对象或 None。"""
    query = select(PointsConsumptionRate).where(
        PointsConsumptionRate.service_code == service_code,
        PointsConsumptionRate.enabled.is_(True),
    )
    if model_id is not None:
        # 先找模型级定价，找不到退回服务默认
        query_model = query.where(PointsConsumptionRate.model_id == model_id)
        row = (await db.execute(query_model)).scalar_one_or_none()
        if row is not None:
            return row
        query = query.where(PointsConsumptionRate.model_id.is_(None))
    result = await db.execute(query)
    return result.scalars().first()


async def record_transaction(
    db: AsyncSession,
    user_id: int,
    tx_type: str,
    points_delta: int,
    balance_after: int,
    service_code: str = None,
    task_id: str = None,
    model_id: int = None,
    remark: str = None,
):
    """追加一条积分流水（只追加，不修改余额）。"""
    db.add(PointsTransaction(
        user_id=user_id,
        tx_type=tx_type,
        points_delta=points_delta,
        service_code=service_code,
        task_id=task_id,
        model_id=model_id,
        balance_after=balance_after,
        remark=remark,
    ))
    await db.flush()


async def adjust_balance(db: AsyncSession, user: User, points_delta: int, remark: str = ""):
    """人工充值/扣回：调整余额并落流水（tx_type=admin_adjust）。"""
    new_balance = max(0, (user.points_balance or 0) + points_delta)
    user.points_balance = new_balance
    await record_transaction(
        db, user.id, TX_ADJUST, points_delta,
        new_balance, remark=remark,
    )
    return new_balance


async def grant_recharge(db: AsyncSession, user: User, points_delta: int, remark: str = ""):
    """正式充值（tx_type=recharge）：仅允许正值加分。"""
    if points_delta <= 0:
        raise ValueError("充值积分必须大于 0")
    new_balance = (user.points_balance or 0) + points_delta
    user.points_balance = new_balance
    await record_transaction(
        db, user.id, TX_RECHARGE, points_delta,
        new_balance, remark=remark,
    )
    return new_balance


async def service_summary(db: AsyncSession, start=None, end=None):
    """按服务汇总：consume/recharge/refund 总额与笔数。"""
    q = select(
        PointsTransaction.service_code,
        func.sum(case((PointsTransaction.tx_type == TX_CONSUME, PointsTransaction.points_delta), else_=0)).label("consume"),
        func.sum(case((PointsTransaction.tx_type == TX_RECHARGE, PointsTransaction.points_delta), else_=0)).label("recharge"),
        func.sum(case((PointsTransaction.tx_type == TX_REFUND, PointsTransaction.points_delta), else_=0)).label("refund"),
        func.sum(case((PointsTransaction.tx_type == TX_ADJUST, PointsTransaction.points_delta), else_=0)).label("adjust"),
        func.count().label("tx_count"),
    ).group_by(PointsTransaction.service_code)
    if start is not None:
        q = q.where(PointsTransaction.create_time >= start)
    if end is not None:
        q = q.where(PointsTransaction.create_time <= end)
    rows = (await db.execute(q)).all()
    return [
        {
            "service_code": r.service_code or "system",
            "consume": r.consume or 0,
            "recharge": r.recharge or 0,
            "refund": r.refund or 0,
            "adjust": r.adjust or 0,
            "tx_count": r.tx_count or 0,
        }
        for r in rows
    ]


async def daily_summary(db: AsyncSession, start=None, end=None):
    """按日汇总：每日 recharge/consume/refund 变动。"""
    q = select(
        func.date(PointsTransaction.create_time).label("date"),
        func.sum(case((PointsTransaction.tx_type == TX_CONSUME, PointsTransaction.points_delta), else_=0)).label("consume"),
        func.sum(case((PointsTransaction.tx_type == TX_RECHARGE, PointsTransaction.points_delta), else_=0)).label("recharge"),
        func.sum(case((PointsTransaction.tx_type == TX_REFUND, PointsTransaction.points_delta), else_=0)).label("refund"),
        func.sum(case((PointsTransaction.tx_type == TX_ADJUST, PointsTransaction.points_delta), else_=0)).label("adjust"),
    ).group_by("date").order_by("date")
    if start is not None:
        q = q.where(PointsTransaction.create_time >= start)
    if end is not None:
        q = q.where(PointsTransaction.create_time <= end)
    rows = (await db.execute(q)).all()
    return [
        {
            "date": str(r.date),
            "consume": r.consume or 0,
            "recharge": r.recharge or 0,
            "refund": r.refund or 0,
            "adjust": r.adjust or 0,
        }
        for r in rows
    ]