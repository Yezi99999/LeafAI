import asyncio
import json
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.db.models import AITask, TaskStatus, User
from app.schemas.task import TaskStatusResponse, TaskListResponse
from app.schemas.common import BaseResponse
from app.api.v1.deps import get_current_user

router = APIRouter(prefix="/task", tags=["任务查询"])


@router.get("/{task_id}", response_model=BaseResponse)
async def get_task_status(
    task_id: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(AITask).where(AITask.task_id == task_id))
    task = result.scalar_one_or_none()
    if task is None:
        raise HTTPException(status_code=404, detail="任务不存在")

    return BaseResponse(data=TaskStatusResponse(
        task_id=task.task_id,
        category=task.category,
        status=task.status.value,
        input_params=task.input_params,
        result=task.result,
        error_msg=task.error_msg,
        create_time=task.create_time,
        update_time=task.update_time,
    ))


@router.get("/{task_id}/stream")
async def stream_task_status(task_id: str):
    async def event_generator():
        from app.db.session import async_session_factory
        last_status = None
        last_progress = -1

        while True:
            await asyncio.sleep(1)
            async with async_session_factory() as db:
                result = await db.execute(select(AITask).where(AITask.task_id == task_id))
                task = result.scalar_one_or_none()
                if task is None:
                    yield f"event: error\ndata: {json.dumps({'error': '任务不存在'}, ensure_ascii=False)}\n\n"
                    return

                current_status = task.status.value
                progress = (task.result or {}).get("progress", 0)

                if current_status != last_status or progress != last_progress:
                    last_status = current_status
                    last_progress = progress
                    payload = {
                        "task_id": task.task_id,
                        "status": current_status,
                        "progress": progress,
                        "result": task.result,
                        "error_msg": task.error_msg,
                    }
                    yield f"event: status\ndata: {json.dumps(payload, ensure_ascii=False, default=str)}\n\n"

                if current_status in ("success", "failed"):
                    return

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/", response_model=BaseResponse)
async def list_tasks(
    status: str = None,
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(AITask).where(AITask.user_id == current_user.id)
    if status:
        query = query.where(AITask.status == status)

    query = query.order_by(AITask.create_time.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    tasks = result.scalars().all()

    count_query = select(AITask).where(AITask.user_id == current_user.id)
    if status:
        count_query = count_query.where(AITask.status == status)
    count_result = await db.execute(count_query)
    total = len(count_result.scalars().all())

    return BaseResponse(data={
        "tasks": [TaskStatusResponse(
            task_id=t.task_id,
            category=t.category,
            status=t.status.value,
            input_params=t.input_params,
            result=t.result,
            error_msg=t.error_msg,
            create_time=t.create_time,
            update_time=t.update_time,
        ) for t in tasks],
        "total": total,
    })