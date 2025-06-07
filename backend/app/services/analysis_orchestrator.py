import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

from sqlalchemy import select, update

from app.api.v1.websocket import (
    send_progress_update,
    send_task_completed,
    send_task_failed,
)
from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.models.task import AnalysisTask, TaskStatus
from app.tasks.comment_analysis import analyze_comments_task
from app.tasks.content_analysis import analyze_content_task
from app.tasks.transcription import transcribe_audio_task
from app.utils.exceptions import ExternalServiceError


class AnalysisStep(str, Enum):
    EXTRACTION = "extraction"
    TRANSCRIPTION = "transcription"
    CONTENT_ANALYSIS = "content_analysis"
    COMMENT_ANALYSIS = "comment_analysis"
    FINALIZATION = "finalization"


@dataclass
class StepResult:
    step: AnalysisStep
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    duration: Optional[float] = None


@dataclass
class AnalysisProgress:
    current_step: AnalysisStep
    progress_percentage: int
    estimated_time_remaining: Optional[int] = None
    steps_completed: Optional[List[AnalysisStep]] = None
    steps_failed: Optional[List[AnalysisStep]] = None


class AnalysisOrchestrator:
    """分析编排器"""

    def __init__(self):
        self.step_weights = {
            AnalysisStep.EXTRACTION: 25,
            AnalysisStep.TRANSCRIPTION: 30,
            AnalysisStep.CONTENT_ANALYSIS: 25,
            AnalysisStep.COMMENT_ANALYSIS: 15,
            AnalysisStep.FINALIZATION: 5,
        }

    async def run_analysis(
        self, task_id: str, youtube_url: str, options: Dict[str, Any]
    ):
        """运行完整的分析流程"""
        start_time = datetime.utcnow()
        step_results = {}

        try:
            logging.info(f"Starting analysis for task {task_id}")

            await self._update_task_status(task_id, TaskStatus.PROCESSING, "开始分析")

            extraction_result = await self._run_extraction_step(
                task_id, youtube_url, options
            )
            step_results[AnalysisStep.EXTRACTION] = extraction_result

            if not extraction_result.success:
                raise ExternalServiceError(f"数据提取失败: {extraction_result.error}")

            transcription_result = await self._run_transcription_step(
                task_id, extraction_result.data, options
            )
            step_results[AnalysisStep.TRANSCRIPTION] = transcription_result

            if not transcription_result.success:
                raise ExternalServiceError(f"音频转录失败: {transcription_result.error}")

            content_result, comment_result = await self._run_parallel_analysis_steps(
                task_id, extraction_result.data, transcription_result.data, options
            )

            step_results[AnalysisStep.CONTENT_ANALYSIS] = content_result
            step_results[AnalysisStep.COMMENT_ANALYSIS] = comment_result

            final_result = await self._run_finalization_step(
                task_id, step_results, options
            )
            step_results[AnalysisStep.FINALIZATION] = final_result

            if not final_result.success:
                raise ExternalServiceError(f"报告生成失败: {final_result.error}")

            total_duration = (datetime.utcnow() - start_time).total_seconds()

            await self._update_task_status(
                task_id,
                TaskStatus.COMPLETED,
                "分析完成",
                completed_at=datetime.utcnow(),
            )

            await send_task_completed(task_id, final_result.data or {})

            logging.info(
                f"Analysis completed for task {task_id} in {total_duration:.2f}s"
            )

        except Exception as e:
            logging.error(f"Analysis failed for task {task_id}: {e}")

            await self._update_task_status(
                task_id, TaskStatus.FAILED, f"分析失败: {str(e)}"
            )

            await send_task_failed(
                task_id, {"message": str(e), "step_results": step_results}
            )

            raise

    def _calculate_progress(
        self,
        completed_steps: List[AnalysisStep],
        current_step: AnalysisStep,
        step_progress: int = 50,
    ) -> float:
        """计算总体进度百分比"""
        total_progress = 0.0

        for step in completed_steps:
            total_progress += self.step_weights[step]

        if current_step:
            current_weight = self.step_weights[current_step]
            total_progress += (current_weight * step_progress) / 100

        return min(total_progress, 100.0)

    async def _update_task_status(
        self,
        task_id: str,
        status: TaskStatus,
        current_step: Optional[str] = None,
        completed_at: Optional[datetime] = None,
    ):
        """更新任务状态"""
        update_data = {
            "status": status,
            "current_step": current_step,
            "updated_at": datetime.utcnow(),
        }

        if completed_at:
            update_data["completed_at"] = completed_at

        async with AsyncSessionLocal() as db:
            await db.execute(
                update(AnalysisTask)
                .where(AnalysisTask.id == task_id)
                .values(**update_data)
            )
            await db.commit()

    async def _run_extraction_step(
        self, task_id: str, youtube_url: str, options: Dict[str, Any]
    ) -> StepResult:
        """执行YouTube数据提取步骤"""
        step_start = datetime.utcnow()

        try:
            from app.services.youtube_extractor import YouTubeExtractor

            await send_progress_update(
                task_id, 5, "初始化YouTube提取器", AnalysisStep.EXTRACTION
            )

            youtube_extractor = YouTubeExtractor()
            video_id = youtube_extractor.extract_video_id(youtube_url)

            if not video_id:
                raise ExternalServiceError(f"无效的YouTube URL: {youtube_url}")

            await send_progress_update(task_id, 10, "获取视频信息", AnalysisStep.EXTRACTION)

            video_info = await youtube_extractor.get_video_info(video_id)

            await send_progress_update(task_id, 15, "下载音频文件", AnalysisStep.EXTRACTION)

            audio_file_path = await youtube_extractor.download_audio(video_id)

            await send_progress_update(task_id, 20, "获取评论数据", AnalysisStep.EXTRACTION)

            comments = await youtube_extractor.get_comments(video_id, max_results=1000)

            extraction_data = {
                "video_info": {
                    "id": video_info.id,
                    "title": video_info.title,
                    "description": video_info.description,
                    "channel_id": video_info.channel_id,
                    "channel_title": video_info.channel_title,
                    "duration": video_info.duration,
                    "view_count": video_info.view_count,
                    "like_count": video_info.like_count,
                    "published_at": video_info.upload_date,
                    "thumbnail_url": video_info.thumbnail_url,
                    "language": video_info.language,
                },
                "audio_file_path": audio_file_path,
                "comments": [
                    {
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
                    for comment in comments
                ],
                "video_id": video_id,
            }

            duration = (datetime.utcnow() - step_start).total_seconds()

            await send_progress_update(task_id, 25, "数据提取完成", AnalysisStep.EXTRACTION)

            return StepResult(
                step=AnalysisStep.EXTRACTION,
                success=True,
                data=extraction_data,
                duration=duration,
            )

        except Exception as e:
            duration = (datetime.utcnow() - step_start).total_seconds()
            logging.error(f"Extraction step failed for task {task_id}: {e}")

            return StepResult(
                step=AnalysisStep.EXTRACTION,
                success=False,
                error=str(e),
                duration=duration,
            )

    async def _run_transcription_step(
        self,
        task_id: str,
        extraction_data: Optional[Dict[str, Any]],
        options: Dict[str, Any],
    ) -> StepResult:
        """执行音频转录步骤"""
        step_start = datetime.utcnow()

        try:
            if not extraction_data:
                raise ExternalServiceError("提取数据未找到")

            audio_file_path = extraction_data.get("audio_file_path")
            if not audio_file_path:
                raise ExternalServiceError("音频文件路径未找到")

            language = options.get("language")

            await send_progress_update(
                task_id, 30, "开始音频转录", AnalysisStep.TRANSCRIPTION
            )

            transcription_result = await transcribe_audio_task(
                task_id, audio_file_path, language
            )

            duration = (datetime.utcnow() - step_start).total_seconds()

            await send_progress_update(
                task_id, 55, "音频转录完成", AnalysisStep.TRANSCRIPTION
            )

            return StepResult(
                step=AnalysisStep.TRANSCRIPTION,
                success=True,
                data=transcription_result,
                duration=duration,
            )

        except Exception as e:
            duration = (datetime.utcnow() - step_start).total_seconds()
            logging.error(f"Transcription step failed for task {task_id}: {e}")

            return StepResult(
                step=AnalysisStep.TRANSCRIPTION,
                success=False,
                error=str(e),
                duration=duration,
            )

    async def _run_content_analysis(
        self,
        task_id: str,
        extraction_data: Optional[Dict[str, Any]],
        transcription_data: Optional[Dict[str, Any]],
        options: Dict[str, Any],
    ) -> StepResult:
        """执行内容分析步骤"""
        step_start = datetime.utcnow()

        try:
            if not extraction_data or not transcription_data:
                raise ExternalServiceError("分析数据不完整")

            video_info = extraction_data.get("video_info")
            if not video_info:
                raise ExternalServiceError("视频信息未找到")

            content_result = await analyze_content_task(
                task_id, transcription_data, video_info
            )

            duration = (datetime.utcnow() - step_start).total_seconds()

            return StepResult(
                step=AnalysisStep.CONTENT_ANALYSIS,
                success=True,
                data=content_result,
                duration=duration,
            )

        except Exception as e:
            duration = (datetime.utcnow() - step_start).total_seconds()
            logging.error(f"Content analysis step failed for task {task_id}: {e}")

            return StepResult(
                step=AnalysisStep.CONTENT_ANALYSIS,
                success=False,
                error=str(e),
                duration=duration,
            )

    async def _run_comment_analysis(
        self,
        task_id: str,
        extraction_data: Optional[Dict[str, Any]],
        options: Dict[str, Any],
    ) -> StepResult:
        """执行评论分析步骤"""
        step_start = datetime.utcnow()

        try:
            if not extraction_data:
                raise ExternalServiceError("提取数据未找到")

            video_id = extraction_data.get("video_id")
            comments_data = extraction_data.get("comments")

            if not video_id:
                raise ExternalServiceError("视频ID未找到")

            comment_result = await analyze_comments_task(
                task_id, video_id, comments_data
            )

            duration = (datetime.utcnow() - step_start).total_seconds()

            return StepResult(
                step=AnalysisStep.COMMENT_ANALYSIS,
                success=True,
                data=comment_result,
                duration=duration,
            )

        except Exception as e:
            duration = (datetime.utcnow() - step_start).total_seconds()
            logging.error(f"Comment analysis step failed for task {task_id}: {e}")

            return StepResult(
                step=AnalysisStep.COMMENT_ANALYSIS,
                success=False,
                error=str(e),
                duration=duration,
            )

    async def _run_parallel_analysis_steps(
        self,
        task_id: str,
        extraction_data: Optional[Dict[str, Any]],
        transcription_data: Optional[Dict[str, Any]],
        options: Dict[str, Any],
    ) -> tuple:
        """并行执行内容分析和评论分析"""
        await send_progress_update(task_id, 60, "开始内容和评论分析")

        if not extraction_data or not transcription_data:
            raise ExternalServiceError("分析数据不完整")

        content_task = asyncio.create_task(
            self._run_content_analysis(
                task_id, extraction_data, transcription_data, options
            )
        )

        comment_task = asyncio.create_task(
            self._run_comment_analysis(task_id, extraction_data, options)
        )

        content_result, comment_result = await asyncio.gather(
            content_task, comment_task, return_exceptions=True
        )

        if isinstance(content_result, Exception):
            content_result = StepResult(
                step=AnalysisStep.CONTENT_ANALYSIS,
                success=False,
                error=str(content_result),
            )

        if isinstance(comment_result, Exception):
            comment_result = StepResult(
                step=AnalysisStep.COMMENT_ANALYSIS,
                success=False,
                error=str(comment_result),
            )

        await send_progress_update(task_id, 85, "内容和评论分析完成")

        return content_result, comment_result

    async def _run_finalization_step(
        self,
        task_id: str,
        step_results: Dict[AnalysisStep, StepResult],
        options: Dict[str, Any],
    ) -> StepResult:
        """执行最终报告生成步骤"""
        step_start = datetime.utcnow()

        try:
            await send_progress_update(
                task_id, 90, "生成综合分析报告", AnalysisStep.FINALIZATION
            )

            extraction_result = step_results.get(AnalysisStep.EXTRACTION)
            transcription_result = step_results.get(AnalysisStep.TRANSCRIPTION)
            content_result = step_results.get(AnalysisStep.CONTENT_ANALYSIS)
            comment_result = step_results.get(AnalysisStep.COMMENT_ANALYSIS)

            extraction_data = (
                extraction_result.data
                if extraction_result and extraction_result.data
                else {}
            )
            transcription_data = (
                transcription_result.data
                if transcription_result and transcription_result.data
                else {}
            )
            content_data = (
                content_result.data if content_result and content_result.data else {}
            )
            comment_data = (
                comment_result.data if comment_result and comment_result.data else {}
            )

            comprehensive_report = await self._generate_comprehensive_report(
                extraction_data, transcription_data, content_data, comment_data, options
            )

            duration = (datetime.utcnow() - step_start).total_seconds()

            await send_progress_update(task_id, 100, "分析完成", AnalysisStep.FINALIZATION)

            return StepResult(
                step=AnalysisStep.FINALIZATION,
                success=True,
                data=comprehensive_report,
                duration=duration,
            )

        except Exception as e:
            duration = (datetime.utcnow() - step_start).total_seconds()
            logging.error(f"Finalization step failed for task {task_id}: {e}")

            return StepResult(
                step=AnalysisStep.FINALIZATION,
                success=False,
                error=str(e),
                duration=duration,
            )

    async def _generate_comprehensive_report(
        self,
        extraction_data: Dict[str, Any],
        transcription_data: Dict[str, Any],
        content_data: Dict[str, Any],
        comment_data: Dict[str, Any],
        options: Dict[str, Any],
    ) -> Dict[str, Any]:
        """生成综合分析报告"""

        video_info = extraction_data.get("video_info", {})

        transcript_info = {
            "language": transcription_data.get("language"),
            "duration": transcription_data.get("duration"),
            "full_text": transcription_data.get("full_text", ""),
            "word_count": len(transcription_data.get("full_text", "").split()),
        }

        content_analysis = content_data.get("analysis", {})

        comment_analysis = comment_data.get("analysis", {})

        cross_analysis_insights = self._generate_cross_analysis_insights(
            content_analysis, comment_analysis, video_info, transcript_info
        )

        recommendations = self._generate_recommendations(
            content_analysis, comment_analysis, video_info, transcript_info
        )

        overall_score = self._calculate_overall_score(
            content_analysis, comment_analysis
        )

        comprehensive_report = {
            "summary": {
                "video_title": video_info.get("title"),
                "channel": video_info.get("channel_title"),
                "duration_minutes": round(video_info.get("duration", 0) / 60, 1),
                "view_count": video_info.get("view_count"),
                "like_count": video_info.get("like_count"),
                "comment_count": len(extraction_data.get("comments", [])),
                "overall_score": overall_score,
                "analysis_timestamp": datetime.utcnow().isoformat(),
            },
            "transcript_analysis": {
                "language": transcript_info["language"],
                "word_count": transcript_info["word_count"],
                "duration_seconds": transcript_info["duration"],
                "speaking_rate_wpm": (
                    round(
                        transcript_info["word_count"]
                        / (transcript_info["duration"] / 60),
                        1,
                    )
                    if transcript_info["duration"]
                    else 0
                ),
            },
            "content_insights": content_analysis,
            "audience_feedback": comment_analysis,
            "cross_analysis_insights": cross_analysis_insights,
            "recommendations": recommendations,
            "metadata": {
                "analysis_options": options,
                "processing_timestamp": datetime.utcnow().isoformat(),
                "data_sources": [
                    "youtube_api",
                    "whisper_transcription",
                    "openai_analysis",
                ],
            },
        }

        return comprehensive_report

    def _generate_cross_analysis_insights(
        self,
        content_analysis: Dict[str, Any],
        comment_analysis: Dict[str, Any],
        video_info: Dict[str, Any],
        transcript_info: Dict[str, Any],
    ) -> Dict[str, Any]:
        """生成跨分析洞察"""

        insights = {
            "content_audience_alignment": {},
            "engagement_patterns": {},
            "sentiment_correlation": {},
            "topic_resonance": {},
        }

        content_sentiment = content_analysis.get("sentiment_analysis", {}).get(
            "overall_sentiment"
        )
        comment_sentiment = comment_analysis.get("sentiment_distribution", {})

        if content_sentiment and comment_sentiment:
            positive_comments = comment_sentiment.get("positive", 0)
            total_comments = (
                sum(comment_sentiment.values()) if comment_sentiment.values() else 1
            )
            positive_ratio = positive_comments / total_comments

            insights["content_audience_alignment"] = {
                "content_tone": content_sentiment,
                "audience_response_positive_ratio": positive_ratio,
                "alignment_score": self._calculate_alignment_score(
                    content_sentiment, positive_ratio
                ),
            }

        view_count = video_info.get("view_count", 0)
        like_count = video_info.get("like_count", 0)
        comment_count = len(comment_analysis.get("comments", []))

        if view_count > 0:
            engagement_rate = (like_count + comment_count) / view_count
            insights["engagement_patterns"] = {
                "like_to_view_ratio": like_count / view_count,
                "comment_to_view_ratio": comment_count / view_count,
                "overall_engagement_rate": engagement_rate,
                "engagement_quality": (
                    "high"
                    if engagement_rate > 0.05
                    else "medium"
                    if engagement_rate > 0.01
                    else "low"
                ),
            }

        content_topics = content_analysis.get("topic_analysis", {}).get(
            "main_topics", []
        )
        comment_keywords = comment_analysis.get("key_themes", [])

        if content_topics and comment_keywords:
            topic_overlap = self._calculate_topic_overlap(
                content_topics, comment_keywords
            )
            insights["topic_resonance"] = {
                "content_topics": content_topics[:5],
                "audience_themes": comment_keywords[:5],
                "topic_overlap_score": topic_overlap,
                "resonance_level": (
                    "high"
                    if topic_overlap > 0.6
                    else "medium"
                    if topic_overlap > 0.3
                    else "low"
                ),
            }

        return insights

    def _generate_recommendations(
        self,
        content_analysis: Dict[str, Any],
        comment_analysis: Dict[str, Any],
        video_info: Dict[str, Any],
        transcript_info: Dict[str, Any],
    ) -> Dict[str, Any]:
        """生成改进建议"""

        recommendations = {
            "content_optimization": [],
            "audience_engagement": [],
            "technical_improvements": [],
            "strategic_insights": [],
        }

        content_structure = content_analysis.get("content_structure", {})
        if content_structure.get("introduction_quality", 0) < 0.7:
            recommendations["content_optimization"].append("考虑改进视频开头，提高观众留存率")

        if content_structure.get("conclusion_quality", 0) < 0.7:
            recommendations["content_optimization"].append("加强视频结尾，提供明确的行动号召")

        comment_sentiment = comment_analysis.get("sentiment_distribution", {})
        negative_ratio = (
            comment_sentiment.get("negative", 0) / sum(comment_sentiment.values())
            if comment_sentiment.values()
            else 0
        )

        if negative_ratio > 0.3:
            recommendations["audience_engagement"].append("关注负面反馈，考虑在后续内容中回应观众关切")

        creator_responses = comment_analysis.get("creator_interaction", {}).get(
            "response_rate", 0
        )
        if creator_responses < 0.1:
            recommendations["audience_engagement"].append("增加与观众的互动，回复更多评论以提高参与度")

        speaking_rate = transcript_info.get("speaking_rate_wpm", 0)
        if speaking_rate > 180:
            recommendations["technical_improvements"].append("考虑放慢语速，提高内容可理解性")
        elif speaking_rate < 120:
            recommendations["technical_improvements"].append("可以适当提高语速，保持观众注意力")

        view_count = video_info.get("view_count", 0)
        like_count = video_info.get("like_count", 0)

        if view_count > 0 and like_count / view_count < 0.02:
            recommendations["strategic_insights"].append("考虑优化内容质量或标题缩略图以提高点赞率")

        return recommendations

    def _calculate_alignment_score(
        self, content_sentiment: str, positive_ratio: float
    ) -> float:
        """计算内容与观众情感对齐分数"""
        if content_sentiment == "positive" and positive_ratio > 0.6:
            return 0.9
        elif content_sentiment == "neutral" and 0.3 <= positive_ratio <= 0.7:
            return 0.8
        elif content_sentiment == "negative" and positive_ratio < 0.4:
            return 0.7
        else:
            return 0.5

    def _calculate_topic_overlap(
        self, content_topics: List[str], comment_keywords: List[str]
    ) -> float:
        """计算内容话题与评论关键词的重叠度"""
        if not content_topics or not comment_keywords:
            return 0.0

        content_set = set(topic.lower() for topic in content_topics)
        comment_set = set(keyword.lower() for keyword in comment_keywords)

        intersection = len(content_set.intersection(comment_set))
        union = len(content_set.union(comment_set))

        return intersection / union if union > 0 else 0.0

    def _calculate_overall_score(
        self, content_analysis: Dict[str, Any], comment_analysis: Dict[str, Any]
    ) -> float:
        """计算整体分析评分"""
        scores = []

        content_quality = content_analysis.get("quality_metrics", {}).get(
            "overall_quality", 0.5
        )
        scores.append(content_quality)

        sentiment_dist = comment_analysis.get("sentiment_distribution", {})
        if sentiment_dist:
            positive_ratio = sentiment_dist.get("positive", 0) / sum(
                sentiment_dist.values()
            )
            scores.append(positive_ratio)

        structure_score = content_analysis.get("content_structure", {}).get(
            "overall_structure_score", 0.5
        )
        scores.append(structure_score)

        return round(sum(scores) / len(scores), 2) if scores else 0.5


analysis_orchestrator = AnalysisOrchestrator()
