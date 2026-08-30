from celery import Celery  # type: ignore[import-untyped]
from nutritwin_api.config import get_settings

settings = get_settings()
celery_app = Celery(
    "nutritwin",
    broker=settings.redis_url or "redis://localhost:6379/0",
    backend=settings.redis_url or "redis://localhost:6379/0",
    include=["nutritwin_worker.tasks"],
)
celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    timezone="UTC",
)
