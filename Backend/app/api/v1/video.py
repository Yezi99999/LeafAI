from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.db.models import AITask, TaskStatus
from app.schemas.video import VideoGenerateRequest, VideoGenerateResponse
from app.schemas.common import BaseResponse
from app.services.ai_scheduler import get_scheduler, AIScheduler
import uuid

router = APIRouter(prefix="/video", tags=["视频生成"])


@router.post("/generate", response_model=BaseResponse)
async def generate_video(
    req: VideoGenerateRequest,
    db: AsyncSession = Depends(get_db),
    scheduler: AIScheduler = Depends(get_scheduler),
):
    task_id = uuid.uuid4().hex[:16]

    task = AITask(
        task_id=task_id,
        user_id=1,
        category="video_generate",
        model_id=req.model_id,
        status=TaskStatus.PENDING,
        input_params=req.model_dump(),
    )
    db.add(task)

    return BaseResponse(data=VideoGenerateResponse(task_id=task_id))