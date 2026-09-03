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
    version: str = Field("", max_length=64)
    deploy_env: str = Field("prod", pattern="^(prod|sandbox)$")
    deploy_status: str = Field("running", pattern="^(running|maintaining|down)$")
    unit_points: int = Field(0, ge=0)


class ModelUpdate(BaseModel):
    display_name: Optional[str] = Field(None, max_length=128)
    model_name: Optional[str] = Field(None, max_length=128)
    is_default: Optional[bool] = None
    is_enabled: Optional[bool] = None
    prompt_max_length: Optional[int] = Field(None, ge=1, description="提示词最大字符数")
    version: Optional[str] = Field(None, max_length=64)
    deploy_env: Optional[str] = Field(None, pattern="^(prod|sandbox)$")
    unit_points: Optional[int] = Field(None, ge=0)


class ModelDeployRequest(BaseModel):
    deploy_status: str = Field(..., pattern="^(running|maintaining|down)$")


class ModelVersionRequest(BaseModel):
    version: str = Field(..., min_length=1, max_length=64)
    deploy_env: str = Field("prod", pattern="^(prod|sandbox)$")


class ModelMetricsResponse(BaseModel):
    id: int
    model_name: str
    avg_latency_ms: Optional[float] = None
    success_count: int
    fail_count: int
    success_rate: float = 0.0


class ModelResponse(BaseModel):
    id: int
    display_name: str
    provider_id: int
    category: str
    model_name: str
    is_default: bool
    is_enabled: bool
    prompt_max_length: int
    version: Optional[str] = None
    deploy_env: str = "prod"
    deploy_status: str = "running"
    unit_points: int = 0
    avg_latency_ms: Optional[float] = None
    success_count: int = 0
    fail_count: int = 0
    last_deploy_time: Optional[datetime] = None
    create_time: datetime
    update_time: datetime

    model_config = {"from_attributes": True}


class FeatureToggleCreate(BaseModel):
    code: str = Field(..., min_length=1, max_length=64, description="能力标识 image_generate/video_generate/chat")
    name: str = Field(..., min_length=1, max_length=128)
    enabled: bool = True
    whitelist_user_ids: Optional[list[int]] = Field(default_factory=list)
    description: str = Field("", max_length=1000)


class FeatureToggleUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=128)
    enabled: Optional[bool] = None
    whitelist_user_ids: Optional[list[int]] = None
    description: Optional[str] = Field(None, max_length=1000)


class FeatureToggleResponse(BaseModel):
    id: int
    code: str
    name: str
    enabled: bool
    whitelist_user_ids: Optional[list[int]] = None
    description: Optional[str] = None
    create_time: datetime
    update_time: datetime

    model_config = {"from_attributes": True}


class RateCreate(BaseModel):
    service_code: str = Field(..., min_length=1, max_length=64)
    multiplier: float = Field(1.0, ge=0, description="倍率：实际消耗 = 模型unit_points × 倍率")
    rate_unit: str = Field("per_call", pattern="^(per_call|per_token|per_image)$")
    model_id: Optional[int] = None
    enabled: bool = True


class RateUpdate(BaseModel):
    multiplier: Optional[float] = Field(None, ge=0)
    rate_unit: Optional[str] = Field(None, pattern="^(per_call|per_token|per_image)$")
    model_id: Optional[int] = None
    enabled: Optional[bool] = None


class RateResponse(BaseModel):
    id: int
    service_code: str
    multiplier: float
    rate_unit: str
    model_id: Optional[int] = None
    enabled: bool
    create_time: datetime
    update_time: datetime

    model_config = {"from_attributes": True}


class RechargeRequest(BaseModel):
    user_id: int = Field(...)
    points_delta: int = Field(..., description="增减积分，正为充值、负为扣回")
    remark: str = Field("", max_length=256)


class TransactionResponse(BaseModel):
    id: int
    user_id: int
    tx_type: str
    points_delta: int
    service_code: Optional[str] = None
    task_id: Optional[str] = None
    model_id: Optional[int] = None
    balance_after: int
    remark: Optional[str] = None
    create_time: datetime

    model_config = {"from_attributes": True}


class ModelPointsUpdate(BaseModel):
    unit_points: int = Field(..., ge=0, description="单次调用消耗积分")


class ModelPointsResponse(BaseModel):
    id: int
    display_name: str
    category: str
    model_name: str
    unit_points: int
    success_count: int
    fail_count: int
    is_enabled: bool
    deploy_status: str

    model_config = {"from_attributes": True}


class TransactionWithUser(BaseModel):
    """流水 + 归属用户名（仿订单列表）。"""
    id: int
    user_id: int
    username: Optional[str] = None
    tx_type: str
    points_delta: int
    service_code: Optional[str] = None
    task_id: Optional[str] = None
    model_id: Optional[int] = None
    balance_after: int
    remark: Optional[str] = None
    create_time: datetime


class NotificationBroadcastRequest(BaseModel):
    type: str = Field("system", pattern="^(points|task|system)$")
    title: str = Field(..., min_length=1, max_length=128)
    content: str = Field("", max_length=2000)
    user_ids: Optional[list[int]] = Field(default=None, description="指定接收者；为空=全量用户，也可含超管")
    extra_data: Optional[dict] = None