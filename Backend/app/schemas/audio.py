from pydantic import BaseModel, Field
from typing import Optional


class TTSRequest(BaseModel):
    model_id: int = Field(..., description="模型ID")
    text: str = Field(..., min_length=1, max_length=5000, description="要转换的文本")
    voice: Optional[str] = Field("default", description="语音风格")
    speed: Optional[float] = Field(1.0, ge=0.25, le=4.0, description="语速")
    response_format: Optional[str] = Field("mp3", description="音频格式")


class ASRResponse(BaseModel):
    text: str = Field(..., description="识别文本")
    language: Optional[str] = Field(None, description="识别语言")
    duration: Optional[float] = Field(None, description="音频时长(秒)")