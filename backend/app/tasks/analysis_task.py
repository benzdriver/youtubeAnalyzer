import asyncio
import logging

from app.api.v1.websocket import (
    send_progress_update,
    send_task_completed,
    send_task_failed,
)
from app.core.database import AsyncSessionLocal
from app.models.task import TaskStatus
from app.services.task_service import TaskService


async def run_analysis(task_id: str):
    async with AsyncSessionLocal() as db:
        task_service = TaskService(db)

        try:
            await task_service.update_task_status(
                task_id,
                TaskStatus.PROCESSING,
                current_step="Initializing analysis",
                progress=0,
            )

            await send_progress_update(
                task_id, 0, "Starting analysis", "Initializing analysis"
            )

            await task_service.update_task_status(
                task_id,
                TaskStatus.PROCESSING,
                current_step="Extracting video data",
                progress=25,
            )

            await send_progress_update(
                task_id, 25, "Extracting video data", "Extracting video data"
            )

            await asyncio.sleep(2)

            await task_service.update_task_status(
                task_id,
                TaskStatus.PROCESSING,
                current_step="Processing audio",
                progress=50,
            )

            await send_progress_update(
                task_id, 50, "Processing audio", "Processing audio"
            )

            await asyncio.sleep(2)

            await task_service.update_task_status(
                task_id,
                TaskStatus.PROCESSING,
                current_step="Analyzing content",
                progress=75,
            )

            await send_progress_update(
                task_id, 75, "Analyzing content", "Analyzing content"
            )

            await asyncio.sleep(2)

            result_data = {
                "summary": "Analysis completed successfully",
                "key_points": ["Point 1", "Point 2", "Point 3"],
                "sentiment": "positive",
                "topics": ["technology", "education"],
            }

            task = await task_service.get_task(task_id)
            if task:
                task.result_data = result_data
                await db.commit()

            await task_service.update_task_status(
                task_id,
                TaskStatus.COMPLETED,
                current_step="Analysis complete",
                progress=100,
            )

            await send_task_completed(task_id, result_data)

        except Exception as e:
            logging.error(f"Analysis failed for task {task_id}: {str(e)}")

            await task_service.update_task_status(
                task_id, TaskStatus.FAILED, error_message=str(e)
            )

            await send_task_failed(task_id, {"message": str(e)})
