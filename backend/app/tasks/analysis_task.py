import logging

from app.api.v1.websocket import send_task_failed
from app.core.database import AsyncSessionLocal
from app.models.task import TaskStatus
from app.services.task_service import TaskService
from app.services.analysis_orchestrator import analysis_orchestrator
from app.utils.exceptions import ValidationError, ExternalServiceError


async def run_analysis(task_id: str):
    """运行YouTube视频分析任务"""
    try:
        async with AsyncSessionLocal() as db:
            task_service = TaskService(db)
            task = await task_service.get_task(task_id)
            if not task:
                raise ValidationError(f"Task not found: {task_id}")
            
            youtube_url = task.youtube_url
            options = task.options or {}
        
        await analysis_orchestrator.run_analysis(task_id, youtube_url, options)
        
    except ValidationError as e:
        logging.error(f"Validation error for task {task_id}: {str(e)}")
        
        async with AsyncSessionLocal() as db:
            task_service = TaskService(db)
            await task_service.update_task_status(
                task_id, TaskStatus.FAILED, error_message=f"输入验证失败: {str(e)}"
            )
        
        await send_task_failed(task_id, {"message": f"输入验证失败: {str(e)}"})

    except ExternalServiceError as e:
        logging.error(f"External service error for task {task_id}: {str(e)}")
        
        async with AsyncSessionLocal() as db:
            task_service = TaskService(db)
            await task_service.update_task_status(
                task_id, TaskStatus.FAILED, error_message=f"外部服务错误: {str(e)}"
            )
        
        await send_task_failed(task_id, {"message": f"外部服务错误: {str(e)}"})

    except Exception as e:
        logging.error(f"Analysis orchestration failed for task {task_id}: {str(e)}")
        
        async with AsyncSessionLocal() as db:
            task_service = TaskService(db)
            await task_service.update_task_status(
                task_id, TaskStatus.FAILED, error_message=f"分析失败: {str(e)}"
            )
        
        await send_task_failed(task_id, {"message": f"分析失败: {str(e)}"})
