from celery import Celery
from typing import Optional

from app.core.config import settings

celery_app = Celery(
    "youtube_analyzer",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["app.tasks", "app.tasks.transcription"],
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
        "app.core.celery_app.analyze_video_task": {"queue": "analysis"},
        "app.tasks.transcription.transcribe_audio_task": {"queue": "transcription"},
    },
    task_default_retry_delay=60,
    task_max_retries=3,
)


@celery_app.task(bind=True)
def analyze_video_task(self, task_id: str):
    import asyncio
    from app.tasks.analysis_task import run_analysis

    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(run_analysis(task_id))
        loop.close()
        return result
    except Exception as e:
        import logging
        logging.error(f"Celery task failed for {task_id}: {str(e)}")
        raise


@celery_app.task(bind=True)
def transcribe_audio_celery_task(self, task_id: str, audio_file_path: str, language: Optional[str] = None):
    import asyncio
    from app.tasks.transcription import transcribe_audio_task

    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(transcribe_audio_task(task_id, audio_file_path, language))
        loop.close()
        return result
    except Exception as e:
        import logging
        logging.error(f"Transcription task failed for {task_id}: {str(e)}")
        raise
