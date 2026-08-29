import asyncio
import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import async_session_factory
from app.db.models import AITask, TaskStatus
from app.services.ai_scheduler import AIScheduler

logger = logging.getLogger(__name__)

MAX_POLL_ATTEMPTS = 120
POLL_INTERVAL = 5


async def execute_image_task(task_id: str):
    async with async_session_factory() as db:
        try:
            result = await db.execute(select(AITask).where(AITask.task_id == task_id))
            task = result.scalar_one_or_none()
            if task is None:
                return

            task.status = TaskStatus.RUNNING
            await db.commit()

            scheduler = AIScheduler()
            client = await scheduler.get_image_client(db, task.model_id)
            model = await scheduler._get_model(db, task.model_id)

            params = task.input_params or {}
            api_result = await client.generate(
                prompt=params.get("prompt", ""),
                model_name=model.model_name,
                size=params.get("size", "1024x1024"),
                quality=params.get("quality"),
                image=params.get("image"),
                callback_url=params.get("callback_url"),
            )

            remote_task_id = api_result.get("id", "")
            if not remote_task_id:
                raise ValueError("远程服务未返回任务ID")

            task.result = {"remote_task_id": remote_task_id}
            await db.commit()

            for attempt in range(MAX_POLL_ATTEMPTS):
                await asyncio.sleep(POLL_INTERVAL)

                try:
                    remote_result = await client.query_task(remote_task_id)
                except Exception as poll_err:
                    logger.warning(f"轮询远程任务 {remote_task_id} 第{attempt+1}次失败: {poll_err}")
                    continue

                state = remote_result.get("state", "")
                progress = remote_result.get("progress", 0)

                logger.info(f"远程任务 {remote_task_id}: state={state}, progress={progress}%")

                if state == "succeeded":
                    images = remote_result.get("data", {}).get("images", [])
                    image_urls = [img.get("url", "") for img in images if img.get("url")]

                    task.status = TaskStatus.SUCCESS
                    task.result = {
                        "remote_task_id": remote_task_id,
                        "images": image_urls,
                        "description": remote_result.get("data", {}).get("description", ""),
                        "progress": 100,
                    }
                    await db.commit()
                    return

                elif state == "error":
                    task.status = TaskStatus.FAILED
                    task.error_msg = remote_result.get("data", {}).get("description", "远程任务失败")
                    task.result = {"remote_task_id": remote_task_id, "raw_response": remote_result}
                    await db.commit()
                    return

                elif state in ("pending", "running"):
                    task.result = {
                        "remote_task_id": remote_task_id,
                        "progress": progress,
                        "state": state,
                    }
                    await db.commit()

            raise TimeoutError(f"任务轮询超时({MAX_POLL_ATTEMPTS * POLL_INTERVAL}秒)")

        except Exception as e:
            async with async_session_factory() as db:
                result = await db.execute(select(AITask).where(AITask.task_id == task_id))
                task = result.scalar_one_or_none()
                if task:
                    task.status = TaskStatus.FAILED
                    task.error_msg = str(e)
                    task.retry_count += 1
                    await db.commit()


async def execute_video_task(task_id: str):
    async with async_session_factory() as db:
        try:
            result = await db.execute(select(AITask).where(AITask.task_id == task_id))
            task = result.scalar_one_or_none()
            if task is None:
                return

            task.status = TaskStatus.RUNNING
            await db.flush()

            scheduler = AIScheduler()
            client = await scheduler.get_video_client(db, task.model_id)
            model = await scheduler._get_model(db, task.model_id)

            params = task.input_params or {}
            api_result = await client.generate(
                prompt=params.get("prompt", ""),
                model_name=model.model_name,
                image_url=params.get("image_url"),
                duration=params.get("duration", 5),
                resolution=params.get("resolution", "1080p"),
                fps=params.get("fps", 24),
            )

            task.status = TaskStatus.SUCCESS
            task.result = api_result
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error_msg = str(e)
            task.retry_count += 1


def execute_image_task_sync(task_id: str):
    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(execute_image_task(task_id))
    finally:
        loop.close()


def execute_video_task_sync(task_id: str):
    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(execute_video_task(task_id))
    finally:
        loop.close()