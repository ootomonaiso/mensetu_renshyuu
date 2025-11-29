"""Celery application instance for background processing."""

from __future__ import annotations

from celery import Celery

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "mensetu",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Tokyo",
    enable_utc=False,
    task_default_queue="analysis",
    task_routes={"app.tasks.*": {"queue": "analysis"}},
)

celery_app.autodiscover_tasks(["app.tasks"])


@celery_app.task(name="ping")
def ping() -> str:
    """Simple task used for health checks."""

    return "pong"
