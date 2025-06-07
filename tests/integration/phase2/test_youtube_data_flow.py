"""
Phase 2 Integration Tests - YouTube Data Flow
Tests the complete data flow from YouTube extraction through transcription, content analysis, and comment analysis.
"""
import pytest
import asyncio
import time
from unittest.mock import AsyncMock, Mock, patch
from sqlalchemy import select, update

from app.models.task import AnalysisTask, TaskStatus, AnalysisType
from app.tasks.analysis_task import run_analysis
from app.services.youtube_extractor import YouTubeExtractor, VideoInfo, CommentData
from app.services.transcription_service import TranscriptionService, TranscriptResult
from app.services.content_analyzer import content_analyzer
from app.services.comment_analyzer import CommentAnalyzer
from app.utils.exceptions import ValidationError, ExternalServiceError
from fixtures.youtube_data import get_sample_video_info, get_sample_comments_data
from fixtures.transcription_data import get_sample_transcription_result
from fixtures.content_analysis_data import get_sample_content_analysis_result
from fixtures.comment_analysis_data import get_sample_comment_analysis_result


class TestYouTubeDataFlow:
    """Test complete YouTube video analysis data flow"""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_complete_analysis_flow_mocked(
        self, 
        test_db, 
        sample_task_id,
        mock_youtube_extractor,
        mock_transcription_service,
        mock_content_analyzer,
        mock_comment_analyzer,
        mock_websocket_manager
    ):
        """Test complete analysis flow with mocked services"""
        video_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        
        db = test_db
        async with db() as session:
            task = AnalysisTask(
                id=sample_task_id,
                video_url=video_url,
                analysis_type=AnalysisType.FULL,
                status=TaskStatus.PENDING,
                progress=0
            )
            session.add(task)
            await session.commit()

        with patch('app.tasks.analysis_task.YouTubeExtractor', return_value=mock_youtube_extractor), \
             patch('app.tasks.analysis_task.TranscriptionService', return_value=mock_transcription_service), \
             patch('app.tasks.analysis_task.content_analyzer', mock_content_analyzer), \
             patch('app.tasks.analysis_task.CommentAnalyzer', return_value=mock_comment_analyzer), \
             patch('app.tasks.analysis_task.send_progress_update', mock_websocket_manager['progress']), \
             patch('app.tasks.analysis_task.send_task_completed', mock_websocket_manager['completed']):

            result = await run_analysis(sample_task_id)

            assert result is not None
            assert 'video_info' in result
            assert 'transcription' in result
            assert 'content_analysis' in result
            assert 'comment_analysis' in result

            mock_youtube_extractor.extract_video_id.assert_called_once_with(video_url)
            mock_youtube_extractor.get_video_info.assert_called_once()
            mock_youtube_extractor.download_audio.assert_called_once()
            mock_youtube_extractor.get_comments.assert_called_once()
            
            mock_transcription_service.transcribe_audio.assert_called_once()
            mock_content_analyzer.analyze.assert_called_once()
            mock_comment_analyzer.analyze_comments.assert_called_once()

            assert mock_websocket_manager['progress'].call_count >= 4
            mock_websocket_manager['completed'].assert_called_once()

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_data_format_consistency(
        self,
        test_db,
        sample_task_id,
        mock_youtube_extractor,
        mock_transcription_service,
        mock_content_analyzer,
        mock_comment_analyzer,
        mock_websocket_manager
    ):
        """Test that data formats are consistent between modules"""
        video_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        
        db = test_db
        async with db() as session:
            task = AnalysisTask(
                id=sample_task_id,
                video_url=video_url,
                analysis_type=AnalysisType.FULL,
                status=TaskStatus.PENDING,
                progress=0
            )
            session.add(task)
            await session.commit()

        with patch('app.tasks.analysis_task.YouTubeExtractor', return_value=mock_youtube_extractor), \
             patch('app.tasks.analysis_task.TranscriptionService', return_value=mock_transcription_service), \
             patch('app.tasks.analysis_task.content_analyzer', mock_content_analyzer), \
             patch('app.tasks.analysis_task.CommentAnalyzer', return_value=mock_comment_analyzer), \
             patch('app.tasks.analysis_task.send_progress_update', mock_websocket_manager['progress']), \
             patch('app.tasks.analysis_task.send_task_completed', mock_websocket_manager['completed']):

            result = await run_analysis(sample_task_id)

            video_info = result['video_info']
            assert 'id' in video_info
            assert 'title' in video_info
            assert 'duration' in video_info
            assert isinstance(video_info['view_count'], int)
            assert isinstance(video_info['like_count'], int)

            transcription = result['transcription']
            assert 'full_text' in transcription
            assert 'segments' in transcription
            assert 'language' in transcription
            assert isinstance(transcription['duration'], (int, float))
            assert isinstance(transcription['segments'], list)

            content_analysis = result['content_analysis']
            assert 'key_points' in content_analysis
            assert 'topic_analysis' in content_analysis
            assert 'sentiment_analysis' in content_analysis
            assert 'summary' in content_analysis
            assert isinstance(content_analysis['quality_score'], (int, float))

            comment_analysis = result['comment_analysis']
            assert 'sentiment_distribution' in comment_analysis
            assert 'main_themes' in comment_analysis
            assert 'author_engagement' in comment_analysis
            assert isinstance(comment_analysis['total_comments'], int)

    @pytest.mark.asyncio
    @pytest.mark.integration
    @pytest.mark.slow
    async def test_multiple_video_analysis(
        self,
        test_db,
        test_videos,
        mock_youtube_extractor,
        mock_transcription_service,
        mock_content_analyzer,
        mock_comment_analyzer,
        mock_websocket_manager
    ):
        """Test analysis of multiple videos with different characteristics"""
        
        for i, video_url in enumerate(test_videos[:2]):  # Test first 2 videos to save time
            task_id = f"test-task-{i+1}"
            
            db = test_db
            async with db() as session:
                task = AnalysisTask(
                    id=task_id,
                    video_url=video_url,
                    analysis_type=AnalysisType.FULL,
                    status=TaskStatus.PENDING,
                    progress=0
                )
                session.add(task)
                await session.commit()

            with patch('app.tasks.analysis_task.YouTubeExtractor', return_value=mock_youtube_extractor), \
                 patch('app.tasks.analysis_task.TranscriptionService', return_value=mock_transcription_service), \
                 patch('app.tasks.analysis_task.content_analyzer', mock_content_analyzer), \
                 patch('app.tasks.analysis_task.CommentAnalyzer', return_value=mock_comment_analyzer), \
                 patch('app.tasks.analysis_task.send_progress_update', mock_websocket_manager['progress']), \
                 patch('app.tasks.analysis_task.send_task_completed', mock_websocket_manager['completed']):

                result = await run_analysis(task_id)
                
                assert result is not None
                assert all(key in result for key in ['video_info', 'transcription', 'content_analysis', 'comment_analysis'])

            db = test_db
            async with db() as session:
                db_task = await session.execute(select(AnalysisTask).where(AnalysisTask.id == task_id))
                task = db_task.scalar_one()
                assert task.status == TaskStatus.COMPLETED
                assert task.result_data is not None

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_task_status_progression(
        self,
        test_db,
        sample_task_id,
        mock_youtube_extractor,
        mock_transcription_service,
        mock_content_analyzer,
        mock_comment_analyzer,
        mock_websocket_manager
    ):
        """Test that task status progresses correctly through the analysis pipeline"""
        video_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        
        db = test_db
        async with db() as session:
            task = AnalysisTask(
                id=sample_task_id,
                video_url=video_url,
                analysis_type=AnalysisType.FULL,
                status=TaskStatus.PENDING,
                progress=0
            )
            session.add(task)
            await session.commit()

        progress_updates = []
        
        async def capture_progress(task_id, progress, message, current_step=None):
            progress_updates.append({
                'task_id': task_id,
                'progress': progress,
                'message': message,
                'current_step': current_step
            })

        with patch('app.tasks.analysis_task.YouTubeExtractor', return_value=mock_youtube_extractor), \
             patch('app.tasks.analysis_task.TranscriptionService', return_value=mock_transcription_service), \
             patch('app.tasks.analysis_task.content_analyzer', mock_content_analyzer), \
             patch('app.tasks.analysis_task.CommentAnalyzer', return_value=mock_comment_analyzer), \
             patch('app.tasks.analysis_task.send_progress_update', side_effect=capture_progress), \
             patch('app.tasks.analysis_task.send_task_completed', mock_websocket_manager['completed']):

            await run_analysis(sample_task_id)

            assert len(progress_updates) >= 4
            
            progress_values = [update['progress'] for update in progress_updates]
            assert progress_values == sorted(progress_values)
            assert progress_values[0] >= 0
            assert progress_values[-1] <= 100

        db = test_db
        async with db() as session:
            db_task = await session.execute(select(AnalysisTask).where(AnalysisTask.id == sample_task_id))
            task = db_task.scalar_one()
            assert task.status == TaskStatus.COMPLETED
            assert task.progress == 100

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_error_handling_invalid_video(
        self,
        test_db,
        sample_task_id,
        mock_websocket_manager
    ):
        """Test error handling for invalid video URLs"""
        invalid_video_url = "https://www.youtube.com/watch?v=invalid_video_id"
        
        db = test_db
        async with db() as session:
            task = AnalysisTask(
                id=sample_task_id,
                video_url=invalid_video_url,
                analysis_type=AnalysisType.FULL,
                status=TaskStatus.PENDING,
                progress=0
            )
            session.add(task)
            await session.commit()

        with patch('app.services.youtube_extractor.YouTubeExtractor') as mock_extractor_class:
            mock_extractor = mock_extractor_class.return_value
            mock_extractor.extract_video_id.side_effect = ValidationError("Invalid video URL")
            
            with patch('app.tasks.analysis_task.send_progress_update', mock_websocket_manager['progress']), \
                 patch('app.tasks.analysis_task.send_task_failed', mock_websocket_manager['failed']):

                with pytest.raises(ValidationError):
                    await run_analysis(sample_task_id)

                mock_websocket_manager['failed'].assert_called_once()

        db = test_db
        async with db() as session:
            db_task = await session.execute(select(AnalysisTask).where(AnalysisTask.id == sample_task_id))
            task = db_task.scalar_one()
            assert task.status == TaskStatus.FAILED
            assert "Invalid video URL" in task.error_message

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_service_failure_recovery(
        self,
        test_db,
        sample_task_id,
        mock_youtube_extractor,
        mock_websocket_manager
    ):
        """Test recovery from service failures"""
        video_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        
        db = test_db
        async with db() as session:
            task = AnalysisTask(
                id=sample_task_id,
                video_url=video_url,
                analysis_type=AnalysisType.FULL,
                status=TaskStatus.PENDING,
                progress=0
            )
            session.add(task)
            await session.commit()

        with patch('app.services.transcription_service.TranscriptionService') as mock_transcription_class:
            mock_transcription = mock_transcription_class.return_value
            mock_transcription.transcribe_audio.side_effect = ExternalServiceError("Whisper service unavailable")
            
            with patch('app.tasks.analysis_task.YouTubeExtractor', return_value=mock_youtube_extractor), \
                 patch('app.tasks.analysis_task.send_progress_update', mock_websocket_manager['progress']), \
                 patch('app.tasks.analysis_task.send_task_failed', mock_websocket_manager['failed']):

                with pytest.raises(ExternalServiceError):
                    await run_analysis(sample_task_id)

        db = test_db
        async with db() as session:
            db_task = await session.execute(select(AnalysisTask).where(AnalysisTask.id == sample_task_id))
            task = db_task.scalar_one()
            assert task.status == TaskStatus.FAILED
            assert "Whisper service unavailable" in task.error_message


def pytest_configure(config):
    """Configure pytest with custom options"""
    config.addinivalue_line(
        "markers", "youtube: mark test as requiring YouTube API access"
    )


def pytest_addoption(parser):
    """Add custom pytest options"""
    parser.addoption(
        "--use-real-apis",
        action="store_true",
        default=False,
        help="Run tests that use real external APIs"
    )
