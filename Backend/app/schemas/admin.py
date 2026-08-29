from pydantic import BaseModel, Field
from typing import Optional, Any
from datetime import datetime


class ProviderCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    category: str = Field(..., pattern="^(chat|image|video|audio)$")
    api_key: str = Field("", max_length=512)
    base_url: str = Field("", max_length=512)
    timeout: int = Field(60, ge=1, le=600)
    extra_config: Optional[dict] = Field(default_factory=dict)
    is_enabled: bool = True
    priority: int = Field(1, ge=1, le=100)


class ProviderUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=128)
    api_key: Optional[str] = Field(None, max_length=512)
    base_url: Optional[str] = Field(None, max_length=512)
    timeout: Optional[int] = Field(None, ge=1, le=600)
    extra_config: Optional[dict] = None
    is_enabled: Optional[bool] = None
    priority: Optional[int] = Field(None, ge=1, le=100)


class ProviderResponse(BaseModel):
    id: int
    name: str
    category: str
    api_key: str
    base_url: str
    timeout: int
    extra_config: Optional[dict]
    is_enabled: bool
    priority: int
    create_time: datetime
    update_time: datetime

    model_config = {"from_attributes": True}


class ModelCreate(BaseModel):
    display_name: str = Field(..., min_length=1, max_length=128)
    provider_id: int = Field(...)
    category: str = Field(..., pattern="^(chat|image|video|audio)$")
    model_name: str = Field(..., min_length=1, max_length=128)
    is_default: bool = False
    is_enabled: bool = True
    prompt_max_length: int = Field(5000, ge=1, description="提示词最大字符数")


class ModelUpdate(BaseModel):
    display_name: Optional[str] = Field(None, max_length=128)
    model_name: Optional[str] = Field(None, max_length=128)
    is_default: Optional[bool] = None
    is_enabled: Optional[bool] = None
    prompt_max_length: Optional[int] = Field(None, ge=1, description="提示词最大字符数")


class ModelResponse(BaseModel):
    id: int
    display_name: str
    provider_id: int
    category: str
    model_name: str
    is_default: bool
    is_enabled: bool
    prompt_max_length: int
    create_time: datetime
    update_time: datetime

    model_config = {"from_attributes": True}