import asyncio
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.db.models import AITask, TaskStatus, User, AIModel
from app.schemas.image import ImageGenerateRequest, ImageGenerateResponse
from app.schemas.common import BaseResponse
from app.services.ai_scheduler import get_scheduler, AIScheduler
from app.tasks.workers import execute_image_task
from app.api.v1.deps import get_current_user
from app.services.toggle_service import ensure_enabled
from app.services.billing import resolve_charge, PLAN_FREE, PLAN_QUOTA, PLAN_POINTS, CHARGE_PLAN_KEY, CHARGE_POINTS_KEY
from app.services import points_service, upload_service
import uuid

router = APIRouter(prefix="/image", tags=["图片生成"])


@router.post("/generate", response_model=BaseResponse)
async def generate_image(
    req: ImageGenerateRequest,
    db: AsyncSession = Depends(get_db),
    scheduler: AIScheduler = Depends(get_scheduler),
    current_user: User = Depends(get_current_user),
):
    await ensure_enabled(db, "image_generate", current_user)
    req.validate_size()
    task_id = uuid.uuid4().hex[:16]
    size = req.get_size()

    # 参考图数量上限（后台可配）
    upload_cfg = await upload_service.get_upload_config(db)
    if req.image and len(req.image) > upload_cfg["max_count"]:
        raise HTTPException(status_code=400, detail=f"参考图数量超过限制({upload_cfg['max_count']}张)")

    model = await db.get(AIModel, req.model_id)
    if model is None or not model.is_enabled:
        raise HTTPException(status_code=400, detail="图片模型不可用或不存在")
    if model.prompt_max_length and len(req.prompt) > model.prompt_max_length:
        raise HTTPException(status_code=422, detail=f"提示词长度超过模型限制({model.prompt_max_length}字符)")

    # 提交时判定免费次数配额/积分（不足则直接拒绝）；实际消耗按费率倍率计算
    cost = await points_service.effective_unit_points(db, "image", model)
    plan, err = resolve_charge(current_user, "image", cost)
    if err:
        raise HTTPException(status_code=400, detail=err)

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
            CHARGE_PLAN_KEY: plan,
            CHARGE_POINTS_KEY: cost if plan in (PLAN_POINTS, PLAN_QUOTA) else 0,
        },
    )
    db.add(task)
    await db.flush()
    await db.commit()

    asyncio.create_task(execute_image_task(task_id))

    return BaseResponse(data=ImageGenerateResponse(task_id=task_id))