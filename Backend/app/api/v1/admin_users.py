from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from app.db.session import get_db
from app.db.models import User, OperationLog
from app.schemas.user_admin import (
    AdminUserCreateRequest, AdminUserUpdateRequest, AdminUserResponse,
)
from app.schemas.common import BaseResponse
from app.api.v1.deps import get_current_superuser
from app.core.security import hash_password

router = APIRouter(prefix="/admin/users", tags=["管理后台-用户"], dependencies=[Depends(get_current_superuser)])


async def _write_log(
    db: AsyncSession,
    admin: User,
    action: str,
    target_id: str,
    detail: dict = None,
    request: Request = None,
):
    log = OperationLog(
        admin_user_id=admin.id,
        module="users",
        action=action,
        target_id=target_id,
        detail=detail or {},
        ip=request.client.host if request and request.client else None,
        user_agent=request.headers.get("user-agent") if request else None,
    )
    db.add(log)
    await db.flush()


def _apply_role(user: User, role: str):
    """同步 role 与 is_superuser，保持既有鉴权字段一致。"""
    user.role = role
    user.is_superuser = (role == "admin")


@router.post("", response_model=BaseResponse)
async def create_user(
    req: AdminUserCreateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_superuser),
):
    existing = await db.execute(select(User).where(User.username == req.username))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="用户名已存在")
    if req.email:
        email_existing = await db.execute(select(User).where(User.email == req.email))
        if email_existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="邮箱已被注册")

    user = User(
        username=req.username,
        email=req.email,
        hashed_password=hash_password(req.password),
        points_balance=req.points_balance,
        free_quota=req.free_quota,
    )
    _apply_role(user, req.role)
    # 后台创建的用户默认启用
    user.is_active = True

    db.add(user)
    await db.flush()
    await _write_log(db, admin, "create", str(user.id), {"username": user.username, "role": user.role}, request)
    await db.commit()
    return BaseResponse(data=AdminUserResponse.model_validate(user))


@router.get("", response_model=BaseResponse)
async def list_users(
    keyword: str = None,
    role: str = None,
    status: str = None,
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_superuser),
):
    query = select(User)
    if keyword:
        query = query.where(or_(User.username.ilike(f"%{keyword}%"), User.email.ilike(f"%{keyword}%")))
    if role:
        query = query.where(User.role == role)
    if status == "active":
        query = query.where(User.is_active == True)  # noqa: E712
    elif status == "disabled":
        query = query.where(User.is_active == False)  # noqa: E712

    count_query = query
    total_result = await db.execute(count_query)
    total = len(total_result.scalars().all())

    query = query.order_by(User.id.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    users = result.scalars().all()

    return BaseResponse(data={
        "items": [AdminUserResponse.model_validate(u) for u in users],
        "total": total,
        "page": page,
        "page_size": page_size,
    })


@router.get("/{user_id}", response_model=BaseResponse)
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_superuser),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    return BaseResponse(data=AdminUserResponse.model_validate(user))


@router.put("/{user_id}", response_model=BaseResponse)
async def update_user(
    user_id: int,
    req: AdminUserUpdateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_superuser),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="用户不存在")

    update_data = req.model_dump(exclude_unset=True)
    changes = {}

    def _set(attr, value):
        old = getattr(user, attr)
        if value is not None and old != value:
            setattr(user, attr, value)
            changes[attr] = {"old": old, "new": value}

    _set("email", update_data.get("email"))
    _set("points_balance", update_data.get("points_balance"))
    if "free_quota" in update_data and update_data["free_quota"] is not None:
        _set("free_quota", update_data["free_quota"])
    if "is_active" in update_data and update_data["is_active"] is not None:
        _set("is_active", update_data["is_active"])
    if "role" in update_data and update_data["role"]:
        role = update_data["role"]
        old_role = user.role
        if old_role != role:
            _apply_role(user, role)
            changes["role"] = {"old": old_role, "new": role}
    if "password" in update_data and update_data["password"]:
        user.hashed_password = hash_password(update_data["password"])
        changes["password"] = {"old": "***", "new": "***"}

    await _write_log(db, admin, "update", str(user.id), changes, request)
    await db.commit()
    return BaseResponse(data=AdminUserResponse.model_validate(user))


@router.patch("/{user_id}/disable", response_model=BaseResponse)
async def disable_user(
    user_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_superuser),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    if user.id == admin.id:
        raise HTTPException(status_code=400, detail="不能停用当前登录的管理员账号")

    user.is_active = False
    await _write_log(db, admin, "disable", str(user.id), {"username": user.username}, request)
    await db.commit()
    return BaseResponse(data=AdminUserResponse.model_validate(user))


@router.patch("/{user_id}/enable", response_model=BaseResponse)
async def enable_user(
    user_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_superuser),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="用户不存在")

    user.is_active = True
    await _write_log(db, admin, "enable", str(user.id), {"username": user.username}, request)
    await db.commit()
    return BaseResponse(data=AdminUserResponse.model_validate(user))