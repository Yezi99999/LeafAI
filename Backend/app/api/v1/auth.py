from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.db.models import User
from app.schemas.auth import (
    UserRegisterRequest, UserLoginRequest, TokenResponse, UserInfoResponse,
)
from app.schemas.common import BaseResponse
from app.core.security import hash_password, verify_password, create_access_token
from app.api.v1.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/register", response_model=BaseResponse)
async def register(
    req: UserRegisterRequest,
    db: AsyncSession = Depends(get_db),
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
        is_active=True,
        is_superuser=False,
    )
    db.add(user)
    await db.flush()
    await db.commit()

    token = create_access_token(data={"sub": str(user.id)})
    return BaseResponse(data=TokenResponse(
        access_token=token,
        username=user.username,
        user_id=user.user_id,
    ))


@router.post("/login", response_model=BaseResponse)
async def login(
    req: UserLoginRequest,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.username == req.username))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="账户已禁用")

    if not verify_password(req.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    token = create_access_token(data={"sub": str(user.id)})
    return BaseResponse(data=TokenResponse(
        access_token=token,
        username=user.username,
        user_id=user.user_id,
    ))


@router.get("/me", response_model=BaseResponse)
async def get_me(
    current_user: User = Depends(get_current_user),
):
    return BaseResponse(data=UserInfoResponse(
        id=current_user.id,
        user_id=current_user.user_id,
        username=current_user.username,
        email=current_user.email,
        is_active=current_user.is_active,
        is_superuser=current_user.is_superuser,
        role=current_user.role,
        points_balance=current_user.points_balance,
        free_quota=current_user.free_quota or {},
    ))