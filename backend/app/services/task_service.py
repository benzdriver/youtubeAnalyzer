import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import AnalysisTask, TaskStatus, AnalysisType
from app.models.schemas import AnalysisTaskCreate


class TaskService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_task(self, task_data: AnalysisTaskCreate) -> AnalysisTask:
        """Create a new analysis task."""
        task = AnalysisTask(
            id=str(uuid.uuid4()),
            youtube_url=str(task_data.video_url),
            status=TaskStatus.PENDING,
            progress=0,
            result_data=task_data.options or {}
        )

        self.db.add(task)
        await self.db.commit()
        await self.db.refresh(task)
        return task

    async def get_task(self, task_id: str) -> Optional[AnalysisTask]:
        result = await self.db.execute(
            select(AnalysisTask).where(AnalysisTask.id == task_id)
        )
        return result.scalar_one_or_none()

    async def get_tasks(
        self, status: Optional[TaskStatus] = None, limit: int = 50, offset: int = 0
    ) -> List[AnalysisTask]:
        """Get tasks with optional filtering."""
        return await self.list_tasks(status, limit, offset)

    async def list_tasks(
        self, status: Optional[TaskStatus] = None, limit: int = 50, offset: int = 0
    ) -> List[AnalysisTask]:
        query = select(AnalysisTask)

        if status:
            query = query.where(AnalysisTask.status == status)

        query = (
            query.order_by(AnalysisTask.created_at.desc()).limit(limit).offset(offset)
        )

        result = await self.db.execute(query)
        return result.scalars().all()

    async def update_task_status(
        self,
        task_id: str,
        status: TaskStatus,
        current_step: Optional[str] = None,
        progress: Optional[int] = None,
        error_message: Optional[str] = None,
    ) -> Optional[AnalysisTask]:
        update_data = {"status": status, "updated_at": datetime.utcnow()}

        if current_step is not None:
            update_data["current_step"] = current_step
        if progress is not None:
            update_data["progress"] = progress
        if error_message is not None:
            update_data["error_message"] = error_message
        if status == TaskStatus.COMPLETED:
            update_data["completed_at"] = datetime.utcnow()

        await self.db.execute(
            update(AnalysisTask).where(AnalysisTask.id == task_id).values(**update_data)
        )
        await self.db.commit()

        return await self.get_task(task_id)

    async def cancel_task(self, task_id: str) -> bool:
        task = await self.get_task(task_id)
        if not task:
            return False

        if task.status in [
            TaskStatus.COMPLETED,
            TaskStatus.FAILED,
            TaskStatus.CANCELLED,
        ]:
            return False

        await self.update_task_status(task_id, TaskStatus.CANCELLED)
        return True

    async def start_analysis(self, task_id: str):
        from app.core.celery_app import analyze_video_task

        analyze_video_task.delay(task_id)
