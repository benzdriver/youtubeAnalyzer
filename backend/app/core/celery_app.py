from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "youtube_analyzer",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["app.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=settings.task_timeout,
    task_soft_time_limit=settings.task_timeout - 300,
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    task_routes={
        "app.tasks.analyze_video_task": {"queue": "analysis"},
    },
)


@celery_app.task(bind=True)
def analyze_video_task(self, task_id: str):
    from app.tasks.analysis_task import run_analysis

    return run_analysis(task_id)
