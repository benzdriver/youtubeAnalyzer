import logging
from typing import Any, Dict, List, Optional

from sqlalchemy import select, update

from app.api.v1.websocket import send_progress_update
from app.core.database import AsyncSessionLocal
from app.models.task import AnalysisTask, TaskStatus
from app.services.comment_analyzer import CommentAnalyzer
from app.services.youtube_extractor import YouTubeExtractor
from app.utils.exceptions import AnalysisError, ValidationError


async def analyze_comments_task(
    task_id: str,
    video_id: str,
    comments_data: Optional[List[Dict[str, Any]]] = None,
):
    """分析评论的异步任务"""

    async def _analyze():
        nonlocal comments_data
        async with AsyncSessionLocal() as db:
            comment_analyzer = CommentAnalyzer()
            youtube_extractor = YouTubeExtractor()

            try:
                result = await db.execute(
                    select(AnalysisTask).where(AnalysisTask.id == task_id)
                )
                task = result.scalar_one_or_none()

                if not task:
                    raise ValidationError(f"Task not found: {task_id}")

                await send_progress_update(
                    task_id, 10, "初始化评论分析服务", "初始化评论分析"
                )

                await send_progress_update(task_id, 20, "获取视频信息", "视频信息获取")

                video_info = await youtube_extractor.get_video_info(video_id)
                video_info_dict = {
                    "id": video_info.id,
                    "title": video_info.title,
                    "channel_id": video_info.channel_id,
                    "channel_title": video_info.channel_title,
                    "view_count": video_info.view_count,
                    "like_count": video_info.like_count,
                    "duration": video_info.duration,
                }

                if not comments_data:
                    await send_progress_update(
                        task_id, 30, "提取评论数据", "评论数据提取"
                    )

                    comments_list = await youtube_extractor.get_comments(
                        video_id, max_results=1000
                    )

                    comments_data = []
                    for comment in comments_list:
                        comment_dict = {
                            "id": comment.id,
                            "text": comment.text,
                            "author": comment.author,
                            "author_channel_id": comment.author_channel_id,
                            "like_count": comment.like_count,
                            "reply_count": comment.reply_count,
                            "published_at": comment.published_at,
                            "is_author_reply": comment.is_author_reply,
                            "parent_id": comment.parent_id,
                        }
                        comments_data.append(comment_dict)

                await send_progress_update(
                    task_id, 40, f"开始分析 {len(comments_data)} 条评论", "评论分析"
                )

                comment_insights = await comment_analyzer.analyze_comments(
                    comments_data, video_info_dict
                )

                await send_progress_update(task_id, 80, "处理分析结果", "结果处理")

                analysis_result = {
                    "total_comments": comment_insights.total_comments,
                    "sentiment_distribution": comment_insights.sentiment_distribution,
                    "main_themes": [
                        {
                            "theme": theme.theme,
                            "keywords": theme.keywords,
                            "comment_count": theme.comment_count,
                            "sentiment_distribution": theme.sentiment_distribution,
                        }
                        for theme in comment_insights.main_themes
                    ],
                    "author_engagement": {
                        "total_replies": (
                            comment_insights.author_engagement.total_replies
                        ),
                        "reply_rate": comment_insights.author_engagement.reply_rate,
                        "avg_response_time": (
                            comment_insights.author_engagement.avg_response_time
                        ),
                        "sentiment_in_replies": (
                            comment_insights.author_engagement.sentiment_in_replies
                        ),
                        "engagement_quality": (
                            comment_insights.author_engagement.engagement_quality
                        ),
                    },
                    "top_comments": comment_insights.top_comments,
                    "spam_detection": comment_insights.spam_detection,
                    "engagement_metrics": comment_insights.engagement_metrics,
                    "recommendations": comment_insights.recommendations,
                }

                result = await db.execute(
                    select(AnalysisTask).where(AnalysisTask.id == task_id)
                )
                task = result.scalar_one()

                current_result = task.result_data or {}
                current_result["comment_analysis"] = analysis_result

                await db.execute(
                    update(AnalysisTask)
                    .where(AnalysisTask.id == task_id)
                    .values(result_data=current_result)
                )
                await db.commit()

                await send_progress_update(task_id, 100, "评论分析完成", "分析完成")

                logging.info(f"Comment analysis completed for task {task_id}")
                return analysis_result

            except Exception as e:
                logging.error(f"Comment analysis failed for task {task_id}: {e}")

                try:
                    await db.execute(
                        update(AnalysisTask)
                        .where(AnalysisTask.id == task_id)
                        .values(
                            status=TaskStatus.FAILED,
                            error_message=f"评论分析失败: {str(e)}",
                        )
                    )
                    await db.commit()
                except Exception as db_error:
                    logging.error(f"Failed to update task status: {db_error}")

                try:
                    await send_progress_update(
                        task_id, 0, f"评论分析失败: {str(e)}", "分析失败"
                    )
                except Exception as ws_error:
                    logging.error(f"Failed to send failure notification: {ws_error}")

                raise AnalysisError(f"评论分析失败: {str(e)}")

    return await _analyze()


async def get_db_session():
    """获取数据库会话的辅助函数"""
    return AsyncSessionLocal()
