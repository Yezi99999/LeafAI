from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class AdminUserCreateRequest(BaseModel):
    username: str = Field(..., min_length=2, max_length=64)
    password: str = Field(..., min_length=6, max_length=128)
    email: Optional[str] = Field(None, max_length=128)
    role: str = Field("user", pattern="^(user|admin)$")
    points_balance: int = Field(0, ge=0)
    free_quota: Optional[dict] = None


class AdminUserUpdateRequest(BaseModel):
    email: Optional[str] = Field(None, max_length=128)
    password: Optional[str] = Field(None, min_length=6, max_length=128)
    role: Optional[str] = Field(None, pattern="^(user|admin)$")
    points_balance: Optional[int] = Field(None, ge=0)
    free_quota: Optional[dict] = None
    is_active: Optional[bool] = None


class AdminUserResponse(BaseModel):
    id: int
    user_id: str
    username: str
    email: Optional[str] = None
    role: str
    is_active: bool
    is_superuser: bool
    points_balance: int
    free_quota: dict = Field(default_factory=dict)
    create_time: datetime
    update_time: datetime

    model_config = {"from_attributes": True}