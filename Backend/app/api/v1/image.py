import asyncio
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.db.models import AITask, TaskStatus, User, AIModel
from app.schemas.image import ImageGenerateRequest, ImageGenerateResponse
from app.schemas.common import BaseResponse
from app.services.ai_scheduler import get_scheduler, AIScheduler
from app.tasks.workers import execute_image_task
from app.api.v1.deps import get_current_user
import uuid

router = APIRouter(prefix="/image", tags=["图片生成"])


@router.post("/generate", response_model=BaseResponse)
async def generate_image(
    req: ImageGenerateRequest,
    db: AsyncSession = Depends(get_db),
    scheduler: AIScheduler = Depends(get_scheduler),
    current_user: User = Depends(get_current_user),
):
    req.validate_size()
    task_id = uuid.uuid4().hex[:16]
    size = req.get_size()

    model_result = await db.get(AIModel, req.model_id)
    if model_result and model_result.prompt_max_length and len(req.prompt) > model_result.prompt_max_length:
        from fastapi import HTTPException
        raise HTTPException(status_code=422, detail=f"提示词长度超过模型限制({model_result.prompt_max_length}字符)")

    task = AITask(
        task_id=task_id,
        user_id=current_user.id,
        category="image_generate",
        model_id=req.model_id,
        status=TaskStatus.PENDING,
        input_params={
            "model_id": req.model_id,
            "prompt": req.prompt,
            "size": size,
            "resolution": req.resolution,
            "aspect_ratio": req.aspect_ratio,
            "quality": req.quality,
            "image": req.image,
            "callback_url": req.callback_url,
        },
    )
    db.add(task)
    await db.flush()
    await db.commit()

    asyncio.create_task(execute_image_task(task_id))

    return BaseResponse(data=ImageGenerateResponse(task_id=task_id))