from unittest.mock import AsyncMock, Mock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import AnalysisTask, TaskStatus
from app.services.content_analyzer import (
    ContentInsights,
    ContentStructure,
    ContentType,
    KeyPoint,
    SentimentAnalysis,
    SentimentType,
    TopicAnalysis,
)
from app.tasks.content_analysis import analyze_content_task
from app.utils.exceptions import ExternalServiceError, ValidationError


@pytest.fixture
def sample_transcript_data():
    """Sample transcript data"""
    return {
        "full_text": "This is a comprehensive tutorial on machine learning algorithms.",
        "segments": [
            {
                "start": 0,
                "end": 10,
                "text": "This is a comprehensive tutorial",
                "confidence": 0.95,
            },
            {
                "start": 10,
                "end": 20,
                "text": "on machine learning algorithms.",
                "confidence": 0.93,
            },
        ],
    }


@pytest.fixture
def sample_video_info():
    """Sample video information"""
    return {
        "id": "video123",
        "title": "Complete Machine Learning Guide",
        "description": "Learn ML from scratch with practical examples",
        "duration": 1800,
        "view_count": 50000,
        "like_count": 2500,
        "channel_id": "channel123",
        "channel_title": "AI Academy",
        "upload_date": "2024-01-15",
        "thumbnail_url": "https://example.com/thumbnail.jpg",
        "language": "en",
    }


@pytest.fixture
def sample_content_insights():
    """Sample content analysis results"""
    return ContentInsights(
        key_points=[
            KeyPoint("Machine learning fundamentals", 0.9, 0, 10, "concept"),
            KeyPoint("Practical applications", 0.8, 10, 20, "application"),
        ],
        topic_analysis=TopicAnalysis(
            main_topic="Machine Learning",
            sub_topics=["Algorithms", "Applications"],
            keywords=["ML", "AI", "algorithms"],
            content_type=ContentType.EDUCATIONAL,
            confidence=0.85,
        ),
        sentiment_analysis=SentimentAnalysis(
            overall_sentiment=SentimentType.POSITIVE,
            sentiment_score=0.4,
            emotional_tone=["informative", "enthusiastic"],
            sentiment_progression=[
                {"timestamp": 0, "sentiment": "positive", "score": 0.4}
            ],
        ),
        content_structure=ContentStructure(
            introduction_end=60.0,
            main_content_segments=[{"start": 60, "end": 1740, "topic": "Main content"}],
            conclusion_start=1740.0,
            call_to_action="Subscribe for more ML content",
        ),
        summary="This comprehensive tutorial covers machine learning fundamentals with practical examples.",
        recommendations=[
            "Practice with real datasets",
            "Implement algorithms from scratch",
        ],
        quality_score=0.82,
    )


@pytest.mark.asyncio
async def test_analyze_content_task_success(
    sample_transcript_data, sample_video_info, sample_content_insights
):
    """Test successful content analysis task execution"""
    task_id = "test-task-123"

    with (
        patch("app.tasks.content_analysis.AsyncSessionLocal") as mock_session_local,
        patch("app.tasks.content_analysis.content_analyzer") as mock_analyzer,
        patch("app.tasks.content_analysis.send_progress_update") as mock_progress,
        patch("app.tasks.content_analysis.select") as mock_select,
        patch("app.tasks.content_analysis.update") as mock_update,
    ):
        mock_db = AsyncMock()
        mock_session_local.return_value.__aenter__.return_value = mock_db

        mock_task = Mock()
        mock_task.id = task_id
        mock_task.result_data = {}

        mock_db.execute.return_value.scalar_one_or_none.return_value = mock_task
        mock_db.execute.return_value.scalar_one.return_value = mock_task

        mock_analyzer.analyze.return_value = sample_content_insights

        result = await analyze_content_task(
            task_id, sample_transcript_data, sample_video_info
        )

        mock_analyzer.analyze.assert_called_once_with(
            sample_transcript_data, sample_video_info
        )

        assert mock_progress.call_count >= 2
        assert mock_db.execute.call_count >= 2
        assert mock_db.commit.call_count >= 2

        assert "key_points" in result
        assert "topic_analysis" in result
        assert "sentiment_analysis" in result
        assert "content_structure" in result
        assert "summary" in result
        assert "recommendations" in result
        assert "quality_score" in result


@pytest.mark.asyncio
async def test_analyze_content_task_missing_task():
    """Test content analysis with missing task"""
    task_id = "nonexistent-task"

    with (
        patch("app.tasks.content_analysis.AsyncSessionLocal") as mock_session_local,
        patch("app.tasks.content_analysis.send_task_failed") as mock_send_failed,
    ):
        mock_db = AsyncMock()
        mock_session_local.return_value.__aenter__.return_value = mock_db
        mock_db.execute.return_value.scalar_one_or_none.return_value = None

        with pytest.raises(ValidationError, match="Task nonexistent-task not found"):
            await analyze_content_task(task_id, {}, {})


@pytest.mark.asyncio
async def test_analyze_content_task_empty_transcript():
    """Test content analysis with empty transcript"""
    task_id = "test-task-123"
    empty_transcript = {"full_text": "", "segments": []}

    with (
        patch("app.tasks.content_analysis.AsyncSessionLocal") as mock_session_local,
        patch("app.tasks.content_analysis.send_task_failed") as mock_send_failed,
    ):
        mock_db = AsyncMock()
        mock_session_local.return_value.__aenter__.return_value = mock_db

        mock_task = Mock()
        mock_task.id = task_id
        mock_db.execute.return_value.scalar_one_or_none.return_value = mock_task

        with pytest.raises(ValidationError, match="Transcript data is required"):
            await analyze_content_task(task_id, empty_transcript, {})


@pytest.mark.asyncio
async def test_content_insights_serialization(sample_content_insights):
    """Test that ContentInsights can be properly serialized to dict"""
    task_id = "test-task-123"

    with (
        patch("app.tasks.content_analysis.AsyncSessionLocal") as mock_session_local,
        patch("app.tasks.content_analysis.content_analyzer") as mock_analyzer,
        patch("app.tasks.content_analysis.send_progress_update") as mock_progress,
    ):
        mock_db = AsyncMock()
        mock_session_local.return_value.__aenter__.return_value = mock_db

        mock_task = Mock()
        mock_task.id = task_id
        mock_task.result_data = {}
        mock_db.execute.return_value.scalar_one_or_none.return_value = mock_task
        mock_db.execute.return_value.scalar_one.return_value = mock_task

        mock_analyzer.analyze.return_value = sample_content_insights

        result = await analyze_content_task(
            task_id, {"full_text": "test", "segments": []}, {"title": "test"}
        )

        assert isinstance(result["key_points"], list)
        assert len(result["key_points"]) == 2
        assert result["key_points"][0]["text"] == "Machine learning fundamentals"
        assert result["key_points"][0]["importance"] == 0.9

        assert isinstance(result["topic_analysis"], dict)
        assert result["topic_analysis"]["main_topic"] == "Machine Learning"
        assert result["topic_analysis"]["content_type"] == "educational"

        assert isinstance(result["sentiment_analysis"], dict)
        assert result["sentiment_analysis"]["overall_sentiment"] == "positive"
        assert result["sentiment_analysis"]["sentiment_score"] == 0.4

        assert isinstance(result["content_structure"], dict)
        assert result["content_structure"]["introduction_end"] == 60.0

        assert isinstance(result["summary"], str)
        assert isinstance(result["recommendations"], list)
        assert isinstance(result["quality_score"], float)


@pytest.mark.asyncio
async def test_analyzer_failure_handling(sample_transcript_data, sample_video_info):
    """Test content analysis with analyzer failure"""
    task_id = "test-task-123"

    with (
        patch("app.tasks.content_analysis.AsyncSessionLocal") as mock_session_local,
        patch("app.tasks.content_analysis.content_analyzer") as mock_analyzer,
        patch("app.tasks.content_analysis.send_task_failed") as mock_send_failed,
        patch("app.tasks.content_analysis.send_progress_update") as mock_progress,
    ):
        mock_db = AsyncMock()
        mock_session_local.return_value.__aenter__.return_value = mock_db

        mock_task = Mock()
        mock_task.id = task_id
        mock_task.result_data = {}
        mock_db.execute.return_value.scalar_one_or_none.return_value = mock_task

        mock_analyzer.analyze.side_effect = ExternalServiceError("OpenAI API failed")

        with pytest.raises(ExternalServiceError):
            await analyze_content_task(
                task_id, sample_transcript_data, sample_video_info
            )

        mock_send_failed.assert_called_once()
