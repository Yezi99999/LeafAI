from pydantic import BaseModel, Field
from typing import Optional


class UserRegisterRequest(BaseModel):
    username: str = Field(..., min_length=2, max_length=64, description="用户名")
    password: str = Field(..., min_length=6, max_length=128, description="密码")
    email: Optional[str] = Field(None, max_length=128, description="邮箱")


class UserLoginRequest(BaseModel):
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")


class TokenResponse(BaseModel):
    access_token: str = Field(..., description="JWT访问令牌")
    token_type: str = "bearer"
    username: str = Field(..., description="用户名")
    user_id: str = Field(..., description="用户UUID标识")


class UserInfoResponse(BaseModel):
    id: int
    user_id: str
    username: str
    email: Optional[str] = None
    is_active: bool
    is_superuser: bool