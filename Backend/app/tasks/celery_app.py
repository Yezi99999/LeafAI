from celery import Celery
from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "leafai_tasks",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Shanghai",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,
    task_soft_time_limit=3000,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    imports=["app.tasks.workers"],
)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=30)
def process_image_task(self, task_id: str):
    pass


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def process_video_task(self, task_id: str):
    pass