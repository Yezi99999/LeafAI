import uuid
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON, Enum as SAEnum, Float
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
    create_time = Column(DateTime, default=datetime.utcnow)
    update_time = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


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