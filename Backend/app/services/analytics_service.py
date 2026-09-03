"""报表聚合服务。

为降低复杂度并保证准确性，仪表盘一律基于业务源表实时聚合（不依赖离线任务）：
- 用户/任务/积分流水/聊天消息均为增量小表，聚合成本可控。
- `BusinessDailyStats` 作为可选预聚合表保留命名与建表（尚无 Celery 离线任务）；接口不强制依赖它。

统一返回 `{ dates: [...], series: {...} }`，前端用 ECharts 渲染。
"""

from datetime import date, datetime, timedelta
from sqlalchemy import select, func, distinct, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import User, AITask, AIChatSession, AIChatMessage, PointsTransaction, AIModel, AIProvider, TaskStatus


def _date_list(days: int) -> list[str]:
    today = date.today()
    return [(today - timedelta(days=days - 1 - i)).isoformat() for i in range(days)]


def _d0() -> datetime:
    return datetime.combine(date.today(), datetime.min.time())


async def _task_counts_day(db: AsyncSession, days: int):
    """返回 {day: {"success": n, "failed": n, "running": n}}。"""
    start = _d0() - timedelta(days=days - 1)
    rows = (await db.execute(
        select(
            func.date(AITask.update_time).label("day"),
            AITask.status,
            func.count().label("c"),
        ).where(AITask.update_time >= start)
        .group_by("day", AITask.status)
    )).all()
    out: dict[str, dict] = {}
    for day, status, c in rows:
        d = day.strftime("%Y-%m-%d") if day else ""
        d = d or _date_list(1)[-1]
        out.setdefault(d, {"success": 0, "failed": 0, "running": 0})
        if status == TaskStatus.SUCCESS:
            out[d]["success"] = c
        elif status == TaskStatus.FAILED:
            out[d]["failed"] = c
        else:
            out[d]["running"] = c
    return out


async def overview(db: AsyncSession) -> dict:
    total_users = (await db.execute(select(func.count()).select_from(User))).scalar_one()
    today_start = _d0()
    dau = 0
    # 今日活跃：今天有任务/聊天/积分变动/新建的用户数
    for model, col in ((AITask, AITask.update_time), (User, User.create_time),
                       (PointsTransaction, PointsTransaction.create_time)):
        q = select(func.count(distinct(model.user_id))).where(col >= today_start)
        dai = (await db.execute(q)).scalar_one()
        dau = max(dau, dai)
    # 累计积分消耗（consume 负值取绝对值的和）
    consumed = (await db.execute(
        select(func.coalesce(func.sum(-PointsTransaction.points_delta), 0)).where(
            PointsTransaction.points_delta < 0)
    )).scalar_one()
    # 7 日任务成功率
    tc = await _task_counts_day(db, 7)
    s = sum(v["success"] for v in tc.values())
    f = sum(v["failed"] for v in tc.values())
    success_rate = (s / (s + f) * 100) if (s + f) > 0 else 0.0
    return {
        "total_users": total_users,
        "today_active_users": dau,
        "cumulative_points_consumed": int(consumed),
        "weekly_success_rate": round(success_rate, 1),
    }


async def users_trend(db: AsyncSession, days: int = 30) -> dict:
    days = max(1, min(days, 90))
    start = _d0() - timedelta(days=days - 1)
    reg_rows = (await db.execute(
        select(func.date(User.create_time).label("day"), func.count().label("c"))
        .where(User.create_time >= start).group_by("day")
    )).all()
    reg_map = {d.strftime("%Y-%m-%d"): c for d, c in reg_rows if d}
    dts = _date_list(days)
    new_users = [reg_map.get(d, 0) for d in dts]
    # DAU：每日有动作的去重用户数（任务/聊天/积分；用户ID来自各自 user 字段）
    active: dict[str, set] = {d: set() for d in dts}
    # 任务：AITask.user_id
    task_rows = (await db.execute(
        select(func.date(AITask.update_time).label("day"), AITask.user_id).where(AITask.update_time >= start)
    )).all()
    for day, uid in task_rows:
        if day:
            active.setdefault(day.strftime("%Y-%m-%d"), set()).add(uid)
    # 聊天：AIChatMessage -> AIChatSession.user_id
    chat_rows = (await db.execute(
        select(func.date(AIChatMessage.create_time).label("day"), AIChatSession.user_id)
        .join(AIChatSession, AIChatSession.id == AIChatMessage.session_id)
        .where(AIChatMessage.create_time >= start)
    )).all()
    for day, uid in chat_rows:
        if day:
            active.setdefault(day.strftime("%Y-%m-%d"), set()).add(uid)
    # 积分：PointsTransaction.user_id
    points_rows = (await db.execute(
        select(func.date(PointsTransaction.create_time).label("day"), PointsTransaction.user_id)
        .where(PointsTransaction.create_time >= start)
    )).all()
    for day, uid in points_rows:
        if day:
            active.setdefault(day.strftime("%Y-%m-%d"), set()).add(uid)
    dau = [len(active.get(d, set())) for d in dts]
    return {"dates": dts, "series": {"new_users": new_users, "dau": dau}}


async def usage(db: AsyncSession) -> dict:
    # 按能力分类的任务量 + 聊天消息量
    task_rows = (await db.execute(
        select(AITask.category, func.count().label("c")).group_by(AITask.category)
    )).all()
    chat_msgs = (await db.execute(select(func.count()).select_from(AIChatMessage))).scalar_one()
    chat_tokens_row = await db.execute(select(func.coalesce(func.sum(AIChatMessage.token_count), 0)))
    chat_tokens = chat_tokens_row.scalar_one()
    usage_map = {cat: c for cat, c in task_rows}
    return {
        "dates": [_date_list(1)[-1]],
        "series": {
            "chat_messages": chat_msgs,
            "chat_tokens": chat_tokens,
            "image_tasks": usage_map.get("image_generate", 0),
            "video_tasks": usage_map.get("video_generate", 0),
        },
    }


async def points_trend(db: AsyncSession, days: int = 30, service_code: str | None = None) -> dict:
    days = max(1, min(days, 90))
    start = _d0() - timedelta(days=days - 1)
    q = select(
        func.date(PointsTransaction.create_time).label("day"),
        func.coalesce(func.sum(-PointsTransaction.points_delta), 0).label("v"),
    ).where(PointsTransaction.points_delta < 0, PointsTransaction.create_time >= start)
    if service_code:
        q = q.where(PointsTransaction.service_code == service_code)
    q = q.group_by("day")
    rows = (await db.execute(q)).all()
    pmap = {d.strftime("%Y-%m-%d"): v for d, v in rows if d}
    dts = _date_list(days)
    return {"dates": dts, "series": {"points_consumed": [float(pmap.get(d, 0)) for d in dts]}}


async def performance(db: AsyncSession) -> dict:
    """平均延迟（模型 avg_latency_ms 加权）与 7 日成功率/失败率折线。"""
    lm = (await db.execute(select(
        func.avg(AIModel.avg_latency_ms),
        func.coalesce(func.sum(AIModel.success_count), 0),
        func.coalesce(func.sum(AIModel.fail_count), 0),
    ))).one()
    avg_latency = lm[0] if lm[0] is not None else 0.0
    tc = await _task_counts_day(db, 7)
    dts = _date_list(7)
    success, failed = [], []
    for d in dts:
        c = tc.get(d, {"success": 0, "failed": 0})
        success.append(c["success"])
        failed.append(c["failed"])
    return {
        "dates": dts,
        "series": {
            "avg_latency_ms": round(float(avg_latency), 1),
            "task_success": success,
            "task_failed": failed,
        },
    }


async def services(db: AsyncSession) -> dict:
    rows = (await db.execute(
        select(AIProvider.name, AIModel.display_name, AIModel.success_count, AIModel.fail_count, AIModel.deploy_status, AIModel.avg_latency_ms)
        .join(AIModel, AIModel.provider_id == AIProvider.id)
    )).all()
    services_list = []
    for pname, mname, succ, fail, deploy, latency in rows:
        services_list.append({
            "provider": pname,
            "model": mname,
            "success_count": succ,
            "fail_count": fail,
            "success_rate": round(succ / (succ + fail) * 100, 1) if (succ + fail) > 0 else 100.0,
            "deploy_status": deploy,
            "avg_latency_ms": latency,
        })
    return {"dates": [], "series": {"services": services_list}}