import asyncio
import logging
from typing import Optional

from app.api.v1.websocket import (
    send_progress_update,
    send_task_completed,
    send_task_failed,
)
from app.core.database import AsyncSessionLocal
from app.models.task import TaskStatus
from app.services.task_service import TaskService
from app.services.youtube_extractor import YouTubeExtractor
from app.utils.storage import storage_manager
from app.utils.exceptions import ValidationError, ExternalServiceError


async def run_analysis(task_id: str):
    """运行YouTube视频分析任务"""
    async with AsyncSessionLocal() as db:
        task_service = TaskService(db)
        extractor = None
        video_id = None
        audio_file_path = None

        try:
            task = await task_service.get_task(task_id)
            if not task:
                raise ValidationError(f"Task not found: {task_id}")

            youtube_url = task.youtube_url
            
            await task_service.update_task_status(
                task_id,
                TaskStatus.PROCESSING,
                current_step="初始化YouTube提取器",
                progress=0,
            )

            await send_progress_update(
                task_id, 0, "初始化YouTube数据提取", "初始化YouTube提取器"
            )

            extractor = YouTubeExtractor()
            
            video_id = extractor.extract_video_id(youtube_url)
            
            await task_service.update_task_status(
                task_id,
                TaskStatus.PROCESSING,
                current_step="获取视频信息",
                progress=10,
            )

            await send_progress_update(
                task_id, 10, "获取视频基本信息", "获取视频信息"
            )

            video_info = await extractor.get_video_info(video_id)

            await task_service.update_task_status(
                task_id,
                TaskStatus.PROCESSING,
                current_step="下载音频文件",
                progress=30,
            )

            await send_progress_update(
                task_id, 30, "下载视频音频文件", "下载音频文件"
            )

            audio_file_path = await extractor.download_audio(video_id)

            await task_service.update_task_status(
                task_id,
                TaskStatus.PROCESSING,
                current_step="获取评论数据",
                progress=60,
            )

            await send_progress_update(
                task_id, 60, "提取视频评论数据", "获取评论数据"
            )

            comments = await extractor.get_comments(video_id, max_results=1000)

            await task_service.update_task_status(
                task_id,
                TaskStatus.PROCESSING,
                current_step="整理提取结果",
                progress=90,
            )

            await send_progress_update(
                task_id, 90, "整理和验证提取的数据", "整理提取结果"
            )

            extraction_result = {
                'video_info': {
                    'id': video_info.id,
                    'title': video_info.title,
                    'description': video_info.description,
                    'duration': video_info.duration,
                    'view_count': video_info.view_count,
                    'like_count': video_info.like_count,
                    'channel_id': video_info.channel_id,
                    'channel_title': video_info.channel_title,
                    'upload_date': video_info.upload_date,
                    'thumbnail_url': video_info.thumbnail_url,
                    'language': video_info.language
                },
                'audio_file_path': audio_file_path,
                'comments': [
                    {
                        'id': comment.id,
                        'text': comment.text,
                        'author': comment.author,
                        'author_channel_id': comment.author_channel_id,
                        'like_count': comment.like_count,
                        'reply_count': comment.reply_count,
                        'published_at': comment.published_at,
                        'is_author_reply': comment.is_author_reply,
                        'parent_id': comment.parent_id
                    }
                    for comment in comments
                ],
                'extraction_metadata': {
                    'total_comments': len(comments),
                    'author_replies': len([c for c in comments if c.is_author_reply]),
                    'extraction_timestamp': task.created_at.isoformat() if task.created_at else None
                }
            }

            task = await task_service.get_task(task_id)
            if task:
                task.result_data = extraction_result
                await db.commit()

            await task_service.update_task_status(
                task_id,
                TaskStatus.COMPLETED,
                current_step="数据提取完成",
                progress=100,
            )

            await send_task_completed(task_id, extraction_result)

        except ValidationError as e:
            logging.error(f"Validation error for task {task_id}: {str(e)}")
            
            await task_service.update_task_status(
                task_id, TaskStatus.FAILED, error_message=f"输入验证失败: {str(e)}"
            )
            
            await send_task_failed(task_id, {"message": f"输入验证失败: {str(e)}"})

        except ExternalServiceError as e:
            logging.error(f"External service error for task {task_id}: {str(e)}")
            
            await task_service.update_task_status(
                task_id, TaskStatus.FAILED, error_message=f"外部服务错误: {str(e)}"
            )
            
            await send_task_failed(task_id, {"message": f"外部服务错误: {str(e)}"})

        except Exception as e:
            logging.error(f"Analysis failed for task {task_id}: {str(e)}")

            await task_service.update_task_status(
                task_id, TaskStatus.FAILED, error_message=f"数据提取失败: {str(e)}"
            )

            await send_task_failed(task_id, {"message": f"数据提取失败: {str(e)}"})

        finally:
            #     storage_manager.cleanup_audio_file(video_id)
            pass
