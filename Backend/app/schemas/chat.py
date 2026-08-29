from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class ChatMessage(BaseModel):
    role: str = Field(..., description="system/user/assistant")
    content: str = Field(..., description="消息内容")


class ChatCompletionRequest(BaseModel):
    model_id: int = Field(..., description="模型ID")
    messages: List[ChatMessage] = Field(..., description="对话消息列表")
    session_id: Optional[str] = Field(None, description="会话ID，用于多轮对话")
    stream: bool = Field(False, description="是否流式输出")
    temperature: Optional[float] = Field(None, ge=0, le=2)
    max_tokens: Optional[int] = Field(None, ge=1)


class ChatCompletionChoice(BaseModel):
    index: int = 0
    message: ChatMessage


class ChatUsage(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class ChatCompletionResponse(BaseModel):
    id: str
    model: str
    choices: List[ChatCompletionChoice]
    usage: Optional[ChatUsage] = None


class ChatSessionResponse(BaseModel):
    id: str
    title: str
    model_id: int
    create_time: datetime
    update_time: datetime

    model_config = {"from_attributes": True}


class ChatSessionListResponse(BaseModel):
    sessions: List[ChatSessionResponse]
    total: int


class ChatMessageResponse(BaseModel):
    id: int
    session_id: str
    role: str
    content: str
    create_time: datetime

    model_config = {"from_attributes": True}