from celery import current_app as celery_app

@celery_app.task
def sample_task(name: str):
    return f"Hello {name}!"

@celery_app.task
def analyze_video_task(video_url: str):
    return {"status": "completed", "video_url": video_url}
