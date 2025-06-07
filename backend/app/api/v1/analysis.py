from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.models.schemas import (
    AnalysisResult,
    AnalysisTaskCreate,
    AnalysisTaskResponse,
    TaskStatusUpdate,
)
from app.models.task import TaskStatus
from app.services.task_service import TaskService

router = APIRouter()


@router.post("/tasks", response_model=AnalysisTaskResponse)
async def create_analysis_task(
    task_data: AnalysisTaskCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db_session),
):
    task_service = TaskService(db)
    task = await task_service.create_task(task_data)

    background_tasks.add_task(task_service.start_analysis, task.id)

    return AnalysisTaskResponse(
        id=task.id,
        video_url=task.video_url,
        analysis_type=task.analysis_type.value,
        status=task.status,
        current_step=task.current_step,
        progress=task.progress,
        options=task.options,
        created_at=task.created_at,
        updated_at=task.updated_at,
        completed_at=task.completed_at,
        result_data=task.result_data,
        error_message=task.error_message,
    )


@router.get("/tasks", response_model=List[AnalysisTaskResponse])
async def list_analysis_tasks(
    status: Optional[TaskStatus] = None,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db_session),
):
    task_service = TaskService(db)
    tasks = await task_service.list_tasks(status=status, limit=limit, offset=offset)

    return [
        AnalysisTaskResponse(
            id=task.id,
            video_url=task.video_url,
            analysis_type=task.analysis_type.value,
            status=task.status,
            current_step=task.current_step,
            progress=task.progress,
            options=task.options,
            created_at=task.created_at,
            updated_at=task.updated_at,
            completed_at=task.completed_at,
        )
        for task in tasks
    ]


@router.get("/tasks/{task_id}", response_model=AnalysisTaskResponse)
async def get_analysis_task(task_id: str, db: AsyncSession = Depends(get_db_session)):
    task_service = TaskService(db)
    task = await task_service.get_task(task_id)

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return AnalysisTaskResponse(
        id=task.id,
        video_url=task.video_url,
        analysis_type=task.analysis_type.value,
        status=task.status,
        current_step=task.current_step,
        progress=task.progress,
        options=task.options,
        created_at=task.created_at,
        updated_at=task.updated_at,
        completed_at=task.completed_at,
        result_data=task.result_data,
        error_message=task.error_message,
    )


@router.get("/tasks/{task_id}/result", response_model=AnalysisResult)
async def get_analysis_result(task_id: str, db: AsyncSession = Depends(get_db_session)):
    task_service = TaskService(db)
    task = await task_service.get_task(task_id)

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if task.status != TaskStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Task not completed yet")

    return AnalysisResult(
        task_id=task.id,
        result=task.result_data or {},
        metadata={
            "created_at": task.created_at.isoformat(),
            "completed_at": (
                task.completed_at.isoformat() if task.completed_at else None
            ),
            "video_url": task.video_url,
        },
    )


@router.patch("/tasks/{task_id}/status", response_model=AnalysisTaskResponse)
async def update_task_status(
    task_id: str,
    status_update: TaskStatusUpdate,
    db: AsyncSession = Depends(get_db_session),
):
    task_service = TaskService(db)
    task = await task_service.update_task_status(
        task_id=task_id,
        status=status_update.status,
        current_step=status_update.current_step,
        progress=status_update.progress,
        error_message=status_update.error_message,
    )

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return AnalysisTaskResponse(
        id=task.id,
        video_url=task.video_url,
        analysis_type=task.analysis_type.value,
        status=task.status,
        current_step=task.current_step,
        progress=task.progress,
        options=task.options,
        created_at=task.created_at,
        updated_at=task.updated_at,
        completed_at=task.completed_at,
        result_data=task.result_data,
        error_message=task.error_message,
    )


@router.delete("/tasks/{task_id}")
async def cancel_analysis_task(
    task_id: str, db: AsyncSession = Depends(get_db_session)
):
    task_service = TaskService(db)
    success = await task_service.cancel_task(task_id)

    if not success:
        raise HTTPException(status_code=404, detail="Task not found")

    return {"message": "Task cancelled successfully"}
