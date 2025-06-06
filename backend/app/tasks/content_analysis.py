import logging
from typing import Dict, Any

from sqlalchemy import select, update

from app.core.database import AsyncSessionLocal
from app.models.task import AnalysisTask, TaskStatus
from app.services.content_analyzer import content_analyzer
from app.api.v1.websocket import send_progress_update, send_task_failed
from app.utils.exceptions import ValidationError, ExternalServiceError


async def analyze_content_task(task_id: str, transcript_data: Dict[str, Any],
                              video_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Celery task for content analysis

    Args:
        task_id: The analysis task ID
        transcript_data: Transcription results from previous step
        video_info: Video metadata

    Returns:
        Dict containing content analysis results
    """
    async with AsyncSessionLocal() as db:
        try:
            logging.info(f"Starting content analysis for task {task_id}")

            result = await db.execute(
                select(AnalysisTask).where(AnalysisTask.id == task_id)
            )
            task = result.scalar_one_or_none()

            if not task:
                raise ValidationError(f"Task {task_id} not found")

            await db.execute(
                update(AnalysisTask)
                .where(AnalysisTask.id == task_id)
                .values(
                    status=TaskStatus.PROCESSING,
                    current_step="content_analysis",
                    progress=85
                )
            )
            await db.commit()

            await send_progress_update(
                task_id=task_id,
                progress=85,
                message="Starting content analysis...",
                current_step="content_analysis"
            )

            if not transcript_data or not transcript_data.get('full_text'):
                raise ValidationError("Transcript data is required for content analysis")

            if not video_info:
                raise ValidationError("Video info is required for content analysis")

            logging.info(f"Analyzing content for video: {video_info.get('title', 'Unknown')}")

            content_insights = await content_analyzer.analyze(transcript_data, video_info)
            analysis_result = {
                'key_points': [
                    {
                        'text': kp.text,
                        'importance': kp.importance,
                        'timestamp_start': kp.timestamp_start,
                        'timestamp_end': kp.timestamp_end,
                        'category': kp.category
                    }
                    for kp in content_insights.key_points
                ],
                'topic_analysis': {
                    'main_topic': content_insights.topic_analysis.main_topic,
                    'sub_topics': content_insights.topic_analysis.sub_topics,
                    'keywords': content_insights.topic_analysis.keywords,
                    'content_type': content_insights.topic_analysis.content_type.value,
                    'confidence': content_insights.topic_analysis.confidence
                },
                'sentiment_analysis': {
                    'overall_sentiment': content_insights.sentiment_analysis.overall_sentiment.value,
                    'sentiment_score': content_insights.sentiment_analysis.sentiment_score,
                    'emotional_tone': content_insights.sentiment_analysis.emotional_tone,
                    'sentiment_progression': content_insights.sentiment_analysis.sentiment_progression
                },
                'content_structure': {
                    'introduction_end': content_insights.content_structure.introduction_end,
                    'main_content_segments': content_insights.content_structure.main_content_segments,
                    'conclusion_start': content_insights.content_structure.conclusion_start,
                    'call_to_action': content_insights.content_structure.call_to_action
                },
                'summary': content_insights.summary,
                'recommendations': content_insights.recommendations,
                'quality_score': content_insights.quality_score
            }

            current_result_data = task.result_data or {}
            current_result_data['content_analysis'] = analysis_result

            await db.execute(
                update(AnalysisTask)
                .where(AnalysisTask.id == task_id)
                .values(
                    result_data=current_result_data,
                    progress=95
                )
            )
            await db.commit()

            await send_progress_update(
                task_id=task_id,
                progress=95,
                message="Content analysis completed successfully",
                current_step="content_analysis"
            )

            logging.info(f"Content analysis completed for task {task_id}")
            return analysis_result

        except ValidationError as e:
            logging.error(f"Validation error in content analysis for task {task_id}: {e}")

            await db.execute(
                update(AnalysisTask)
                .where(AnalysisTask.id == task_id)
                .values(
                    status=TaskStatus.FAILED,
                    error_message=str(e),
                    current_step="content_analysis"
                )
            )
            await db.commit()

            await send_task_failed(task_id, {"error": str(e)})
            raise

        except ExternalServiceError as e:
            logging.error(f"External service error in content analysis for task {task_id}: {e}")

            await db.execute(
                update(AnalysisTask)
                .where(AnalysisTask.id == task_id)
                .values(
                    status=TaskStatus.FAILED,
                    error_message=f"Content analysis failed: {e}",
                    current_step="content_analysis"
                )
            )
            await db.commit()

            await send_task_failed(task_id, {"error": f"Content analysis failed: {e}"})
            raise

        except Exception as e:
            logging.error(f"Unexpected error in content analysis for task {task_id}: {e}")

            await db.execute(
                update(AnalysisTask)
                .where(AnalysisTask.id == task_id)
                .values(
                    status=TaskStatus.FAILED,
                    error_message=f"Content analysis failed: {e}",
                    current_step="content_analysis"
                )
            )
            await db.commit()

            await send_task_failed(task_id, {"error": f"Content analysis failed: {e}"})
            raise
