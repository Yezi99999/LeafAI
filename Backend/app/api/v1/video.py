from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.db.models import AITask, TaskStatus, User
from app.schemas.video import VideoGenerateRequest, VideoGenerateResponse
from app.schemas.common import BaseResponse
from app.services.ai_scheduler import get_scheduler, AIScheduler
from app.api.v1.deps import get_current_user
from app.services.toggle_service import ensure_enabled
import uuid

router = APIRouter(prefix="/video", tags=["视频生成"])


@router.post("/generate", response_model=BaseResponse)
async def generate_video(
    req: VideoGenerateRequest,
    db: AsyncSession = Depends(get_db),
    scheduler: AIScheduler = Depends(get_scheduler),
    current_user: User = Depends(get_current_user),
):
    await ensure_enabled(db, "video_generate", current_user)
    task_id = uuid.uuid4().hex[:16]

    task = AITask(
        task_id=task_id,
        user_id=current_user.id,
        category="video_generate",
        model_id=req.model_id,
        status=TaskStatus.PENDING,
        input_params=req.model_dump(),
    )
    db.add(task)

    return BaseResponse(data=VideoGenerateResponse(task_id=task_id))