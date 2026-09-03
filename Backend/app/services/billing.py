"""积分/免费次数配额结算服务。

语义（`user.free_quota[category]`）：
- `-1`：不限制次数、不消耗积分
- `>0`：拥有 N 次免费额度，成功后剩余次数减一；减到 0 后转为消耗积分
- `0`：普通账户，消耗积分（校验余额 >= unit_points，成功后扣减）

结算计划在任务提交时确定（避免超扣），成功后由 worker 结算。
"""

QUOTA_UNLIMITED = -1

# 记录在 task.input_params 内的预留键
CHARGE_PLAN_KEY = "_charge_plan"
CHARGE_POINTS_KEY = "_charge_points"

PLAN_FREE = "free"          # -1：不限次不扣积分
PLAN_QUOTA = "quota"        # >0：消耗免费次数
PLAN_POINTS = "points"      # 0：消耗积分


def get_quota(user, category: str) -> int:
    """读取某能力剩余免费次数，缺省为 0（消耗积分）。"""
    quota = (user.free_quota or {}) if hasattr(user, "free_quota") else {}
    if not isinstance(quota, dict):
        quota = {}
    return quota.get(category, 0)


def resolve_charge(user, category: str, unit_points: int):
    """提交时判定结算计划，返回 (plan, error)。

    - 返回 `plan` 为 PLAN_FREE / PLAN_QUOTA / PLAN_POINTS；
    - 余额不足返回 (None, error_msg)，调用方应拒绝该请求。
    """
    quota = get_quota(user, category)
    if quota == QUOTA_UNLIMITED:
        return PLAN_FREE, None
    if quota and quota > 0:
        return PLAN_QUOTA, None
    # quota <= 0 且 != -1（即 0）→ 消耗积分
    need = max(0, unit_points or 0)
    if user.points_balance < need:
        return None, f"积分不足，当前余额 {user.points_balance} 积分，本次需要 {need} 积分"
    return PLAN_POINTS, None


def settle_success(user, category: str, unit_points: int, plan: str):
    """任务成功后结算：扣除免费次数或积分。"""
    if plan == PLAN_QUOTA:
        quota = (user.free_quota or {}) if hasattr(user, "free_quota") else {}
        if not isinstance(quota, dict):
            quota = {}
        cur = quota.get(category, 0)
        # 极端并发下可能已为 0 甚至负数，仅当仍为正值时减一
        if cur and cur > 0:
            quota[category] = cur - 1
            user.free_quota = quota
    elif plan == PLAN_POINTS:
        need = max(0, unit_points or 0)
        user.points_balance = max(0, user.points_balance - need)
    # PLAN_FREE：不处理