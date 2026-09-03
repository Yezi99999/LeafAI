import uuid
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON, Enum as SAEnum, Float, Date, UniqueConstraint
)
from sqlalchemy.orm import relationship
from app.db.session import Base
import enum


class ProviderCategory(str, enum.Enum):
    CHAT = "chat"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"


class TaskStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"


class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(32), unique=True, nullable=False, default=lambda: uuid.uuid4().hex[:16], comment="对外用户标识")
    username = Column(String(64), unique=True, nullable=False, index=True)
    email = Column(String(128), unique=True, nullable=True)
    hashed_password = Column(String(256), nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    role = Column(String(32), default="user", comment="角色：user/admin")
    points_balance = Column(Integer, default=0, comment="积分余额")
    free_quota = Column(JSON, nullable=True, default=dict, comment="各能力剩余免费次数{chat,image,video,audio};-1不限不扣积分,0消耗积分")
    create_time = Column(DateTime, default=datetime.utcnow)
    update_time = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class OperationLog(Base):
    __tablename__ = "operation_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    admin_user_id = Column(Integer, ForeignKey("user.id"), nullable=False, index=True, comment="操作者")
    module = Column(String(64), nullable=False, comment="模块：users/models/...")
    action = Column(String(64), nullable=False, comment="动作：create/update/delete/...")
    target_id = Column(String(128), nullable=True, comment="目标对象标识")
    detail = Column(JSON, nullable=True, default=dict, comment="变更详情")
    ip = Column(String(64), nullable=True)
    user_agent = Column(String(256), nullable=True)
    create_time = Column(DateTime, default=datetime.utcnow)


class AIProvider(Base):
    __tablename__ = "ai_provider"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(128), unique=True, nullable=False, comment="服务商名称")
    category = Column(SAEnum(ProviderCategory), nullable=False, index=True, comment="能力分类")
    api_key = Column(String(512), nullable=True, default="", comment="服务商API密钥")
    base_url = Column(String(512), nullable=True, default="", comment="自定义请求地址")
    timeout = Column(Integer, default=60, comment="接口超时秒数")
    extra_config = Column(JSON, nullable=True, default=dict, comment="厂商特殊参数")
    is_enabled = Column(Boolean, default=True, index=True, comment="是否启用")
    priority = Column(Integer, default=1, comment="调度权重")
    create_time = Column(DateTime, default=datetime.utcnow)
    update_time = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    models = relationship("AIModel", back_populates="provider", cascade="all, delete-orphan")


class AIModel(Base):
    __tablename__ = "ai_model"

    id = Column(Integer, primary_key=True, autoincrement=True)
    display_name = Column(String(128), nullable=False, comment="页面展示名称")
    provider_id = Column(Integer, ForeignKey("ai_provider.id", ondelete="CASCADE"), nullable=False, index=True)
    category = Column(SAEnum(ProviderCategory), nullable=False, index=True, comment="能力分类")
    model_name = Column(String(128), nullable=False, comment="服务商侧真实模型名称")
    is_default = Column(Boolean, default=False, comment="是否默认模型")
    is_enabled = Column(Boolean, default=True)
    prompt_max_length = Column(Integer, default=5000, comment="提示词最大字符数")
    version = Column(String(64), nullable=True, default="", comment="模型版本号")
    deploy_env = Column(String(20), default="prod", comment="部署环境：prod/sandbox")
    deploy_status = Column(String(20), default="running", comment="部署状态：running/maintaining/down")
    unit_points = Column(Integer, default=0, comment="单次调用基础积分")
    avg_latency_ms = Column(Float, nullable=True, comment="平均耗时ms")
    success_count = Column(Integer, default=0, comment="成功次数")
    fail_count = Column(Integer, default=0, comment="失败次数")
    last_deploy_time = Column(DateTime, nullable=True, comment="最近部署时间")
    create_time = Column(DateTime, default=datetime.utcnow)
    update_time = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    provider = relationship("AIProvider", back_populates="models")


class AIChatSession(Base):
    __tablename__ = "ai_chat_session"

    id = Column(String(64), primary_key=True, default=lambda: uuid.uuid4().hex[:16])
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False, index=True)
    model_id = Column(Integer, ForeignKey("ai_model.id"), nullable=False)
    title = Column(String(256), nullable=True, default="新对话")
    create_time = Column(DateTime, default=datetime.utcnow)
    update_time = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    messages = relationship("AIChatMessage", back_populates="session", cascade="all, delete-orphan")


class AIChatMessage(Base):
    __tablename__ = "ai_chat_message"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(64), ForeignKey("ai_chat_session.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(16), nullable=False, comment="system/user/assistant")
    content = Column(Text, nullable=False, comment="消息内容")
    token_count = Column(Integer, nullable=True, comment="token消耗数")
    create_time = Column(DateTime, default=datetime.utcnow)

    session = relationship("AIChatSession", back_populates="messages")


class AITask(Base):
    __tablename__ = "ai_task"

    task_id = Column(String(64), primary_key=True, default=lambda: uuid.uuid4().hex[:16])
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False, index=True)
    category = Column(String(32), nullable=False, index=True, comment="image_generate/video_generate")
    model_id = Column(Integer, ForeignKey("ai_model.id"), nullable=False)
    status = Column(SAEnum(TaskStatus), default=TaskStatus.PENDING, index=True)
    input_params = Column(JSON, nullable=True, default=dict)
    result = Column(JSON, nullable=True, default=dict)
    error_msg = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    create_time = Column(DateTime, default=datetime.utcnow)
    update_time = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class FeatureToggle(Base):
    __tablename__ = "feature_toggle"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(64), unique=True, nullable=False, index=True, comment="能力标识 image_generate/video_generate/chat")
    name = Column(String(128), nullable=False, comment="展示名")
    enabled = Column(Boolean, default=True, comment="总开关")
    whitelist_user_ids = Column(JSON, nullable=True, default=list, comment="灰度白名单用户id，空=全量")
    description = Column(Text, nullable=True, default="")
    create_time = Column(DateTime, default=datetime.utcnow)
    update_time = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class PointsConsumptionRate(Base):
    __tablename__ = "points_consumption_rate"

    id = Column(Integer, primary_key=True, autoincrement=True)
    service_code = Column(String(64), nullable=False, index=True, comment="服务代码 image_generate/video_generate/chat")
    multiplier = Column(Float, default=1.0, comment="倍率：实际消耗 = 模型unit_points × 倍率")
    rate_unit = Column(String(20), default="per_call", comment="计费单位 per_call(次)/per_token(token)/per_image(张)")
    model_id = Column(Integer, ForeignKey("ai_model.id"), nullable=True, comment="按模型定价，NULL=服务默认")
    enabled = Column(Boolean, default=True)
    create_time = Column(DateTime, default=datetime.utcnow)
    update_time = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class PointsTransaction(Base):
    __tablename__ = "points_transaction"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False, index=True, comment="归属用户")
    tx_type = Column(String(20), nullable=False, comment="recharge/consume/refund/admin_adjust")
    points_delta = Column(Integer, nullable=False, comment="变动量，消费为负")
    service_code = Column(String(64), nullable=True, index=True)
    task_id = Column(String(64), nullable=True, comment="关联任务")
    model_id = Column(Integer, nullable=True, comment="关联模型")
    balance_after = Column(Integer, nullable=False, comment="变动后余额快照")
    remark = Column(String(256), nullable=True)
    create_time = Column(DateTime, default=datetime.utcnow, index=True)


class UserNotification(Base):
    __tablename__ = "user_notification"

    id = Column(Integer, primary_key=True, autoincrement=True)
    client_token = Column(String(36), unique=True, index=True, default=lambda: str(uuid.uuid4()),
                          comment="面向客户端的公开标识（不暴露内部 id）")
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False, index=True, comment="接收者")
    type = Column(String(20), default="system", index=True, comment="points/task/system")
    title = Column(String(128), nullable=False)
    content = Column(Text, nullable=True, default="")
    extra_data = Column(JSON, nullable=True, default=dict)
    is_read = Column(Boolean, default=False, index=True)
    read_time = Column(DateTime, nullable=True)
    create_time = Column(DateTime, default=datetime.utcnow, index=True)


class BusinessDailyStats(Base):
    """报表预聚合表：每个 (stat_date, metric) 一行，供仪表盘高性能读取。"""
    __tablename__ = "business_daily_stats"
    __table_args__ = (UniqueConstraint("stat_date", "metric", name="uq_business_daily_stats_date_metric"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    stat_date = Column(Date, nullable=False, index=True, comment="统计日期")
    metric = Column(String(64), nullable=False, comment="指标键：active_users/chat_calls/...")
    value = Column(Float, default=0, comment="聚合值")
    create_time = Column(DateTime, default=datetime.utcnow)


class SystemConfig(Base):
    """系统配置键值表：后台可编辑的站点配置（如 API 接入文档）。"""
    __tablename__ = "system_config"

    key = Column(String(64), primary_key=True, comment="配置键")
    value = Column(JSON, nullable=True, comment="配置值（JSON）")
    update_time = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")


_DEFAULT_API_DOCS = {
    "title": "LeafAI API 接入文档",
    "content": (
        "<div class='api-doc'>"
        "<h1>LeafAI API 接入文档</h1>"
        "<p>本文档面向第三方开发者，介绍如何调用 LeafAI 开放能力接口（图片生成、对话等）。接口统一走 <code>Bearer</code> JWT 鉴权，返回统一的 JSON 信封。</p>"

        "<h2>1. 基础说明</h2>"
        "<table><thead><tr><th>项目</th><th>说明</th></tr></thead><tbody>"
        "<tr><td><strong>Base URL</strong></td><td><code>http://&lt;host&gt;:8000</code></td></tr>"
        "<tr><td><strong>API 前缀</strong></td><td><code>/api/v1</code></td></tr>"
        "<tr><td><strong>数据格式</strong></td><td><code>application/json</code>，UTF-8</td></tr>"
        "<tr><td><strong>鉴权</strong></td><td><code>Authorization: Bearer &lt;token&gt;</code></td></tr>"
        "</tbody></table>"

        "<h2>2. 认证接口</h2>"
        "<h3>登录</h3>"
        "<p><code>POST /api/v1/auth/login</code></p>"
        "<pre><code>{ \"username\": \"demo\", \"password\": \"123456\" }</code></pre>"
        "<p>响应返回 <code>access_token</code>，用于后续接口鉴权。</p>"

        "<h2>3. 对话</h2>"
        "<p><code>POST /api/v1/chat/completions</code>，支持非流式与流式（<code>stream: true</code>）两种。</p>"
        "<pre><code>{ \"model_id\": 1, \"messages\": [{\"role\":\"user\",\"content\":\"你好\"}] }</code></pre>"

        "<h2>4. 图片生成（异步）</h2>"
        "<p>先提交任务拿到 <code>task_id</code>，再轮询或 SSE 获取结果：</p>"
        "<p><code>POST /api/v1/image/generate</code></p>"
        "<pre><code>{ \"model_id\": 1, \"prompt\": \"一只柴犬\", \"resolution\": \"1K\", \"aspect_ratio\": \"1:1\" }</code></pre>"
        "<p>查询状态：<code>GET /api/v1/task/{task_id}</code></p>"

        "<h2>5. 常见状态码</h2>"
        "<table><thead><tr><th>状态码</th><th>含义</th></tr></thead><tbody>"
        "<tr><td>400</td><td>参数错误 / 业务校验失败（如积分不足）</td></tr>"
        "<tr><td>401</td><td>未认证或令牌无效</td></tr>"
        "<tr><td>404</td><td>资源不存在</td></tr>"
        "<tr><td>422</td><td>参数校验失败</td></tr>"
        "</tbody></table>"

        "<h2>6. 调用示例（curl）</h2>"
        "<pre><code>curl -X POST http://localhost:8000/api/v1/auth/login \\\n"
        "  -H \"Content-Type: application/json\" \\\n"
        "  -d '{\"username\":\"demo\",\"password\":\"123456\"}'</code></pre>"
        "</div>"
    ),
}