from typing import Any, Dict, List, Optional

from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "youtube_analyzer",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=[
        "app.tasks",
        "app.tasks.transcription",
        "app.tasks.content_analysis",
        "app.tasks.comment_analysis",
    ],
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
        "app.tasks.content_analysis.analyze_content_task": {
            "queue": "content_analysis"
        },
        "app.core.celery_app.analyze_comments_celery_task": {"queue": "analysis"},
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
def transcribe_audio_celery_task(
    self, task_id: str, audio_file_path: str, language: Optional[str] = None
):
    import asyncio

    from app.tasks.transcription import transcribe_audio_task

    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(
            transcribe_audio_task(task_id, audio_file_path, language)
        )
        loop.close()
        return result
    except Exception as e:
        import logging

        logging.error(f"Transcription task failed for {task_id}: {str(e)}")
        raise


@celery_app.task(bind=True)
def analyze_content_celery_task(
    self, task_id: str, transcript_data: dict, video_info: dict
):
    import asyncio

    from app.tasks.content_analysis import analyze_content_task

    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(
            analyze_content_task(task_id, transcript_data, video_info)
        )
        loop.close()
        return result
    except Exception as e:
        import logging

        logging.error(f"Content analysis task failed for {task_id}: {str(e)}")
        raise


@celery_app.task(bind=True)
def analyze_comments_celery_task(
    self,
    task_id: str,
    video_id: str,
    comments_data: Optional[List[Dict[str, Any]]] = None,
):
    import asyncio

    from app.tasks.comment_analysis import analyze_comments_task

    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(
            analyze_comments_task(task_id, video_id, comments_data)
        )
        loop.close()
        return result
    except Exception as e:
        import logging

        logging.error(f"Comment analysis task failed for {task_id}: {str(e)}")
        raise
