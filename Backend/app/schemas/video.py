from pydantic import BaseModel, Field
from typing import Optional


class VideoGenerateRequest(BaseModel):
    model_id: int = Field(..., description="模型ID")
    prompt: str = Field(..., min_length=1, max_length=4000, description="视频生成提示词")
    image_url: Optional[str] = Field(None, description="图生视频的参考图URL")
    duration: Optional[int] = Field(5, ge=1, le=60, description="视频时长(秒)")
    resolution: Optional[str] = Field("1080p", description="视频分辨率")
    fps: Optional[int] = Field(24, ge=1, le=60, description="帧率")


class VideoGenerateResponse(BaseModel):
    task_id: str
    status: str = "pending"
    message: str = "任务已提交，请轮询查询结果"