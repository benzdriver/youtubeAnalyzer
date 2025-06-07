"""
Phase 2 Integration Tests - Error Handling
Tests error handling for various failure scenarios in the video analysis pipeline.
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, Mock, patch
from requests.exceptions import ConnectionError, Timeout, HTTPError
from openai import RateLimitError, APIError

from app.models.task import AnalysisTask, TaskStatus, AnalysisType
from app.tasks.analysis_task import run_analysis
from app.utils.exceptions import ValidationError, ExternalServiceError, RateLimitError
from app.services.youtube_extractor import YouTubeExtractor
from app.services.transcription_service import TranscriptionService
from app.services.content_analyzer import ContentAnalyzer
from app.services.comment_analyzer import CommentAnalyzer


class TestErrorHandling:
    """Test error handling for various failure scenarios"""

    @pytest.mark.asyncio
    @pytest.mark.error_handling
    async def test_invalid_youtube_url_error(
        self,
        test_db,
        mock_websocket_manager
    ):
        """Test error handling for invalid YouTube URLs"""
        invalid_urls = [
            "https://www.youtube.com/watch?v=invalid_video_id_12345",
            "https://youtu.be/nonexistent_video",
            "https://www.youtube.com/watch?v=",
            "not_a_url_at_all",
            "https://vimeo.com/123456789"  # Different platform
        ]
        
        for invalid_url in invalid_urls:
            task_id = f"error-test-invalid-url-{hash(invalid_url) % 1000}"
            
            async with test_db() as db:
                task = AnalysisTask(
                    id=task_id,
                    video_url=invalid_url,
                    analysis_type=AnalysisType.FULL,
                    status=TaskStatus.PENDING,
                    progress=0
                )
                db.add(task)
                await db.commit()

            with patch('app.services.youtube_extractor.YouTubeExtractor') as mock_extractor_class:
                mock_extractor = mock_extractor_class.return_value
                mock_extractor.extract_video_id.side_effect = ValidationError(f"Invalid YouTube URL: {invalid_url}")
                
                with patch('app.tasks.analysis_task.send_progress_update', mock_websocket_manager['progress']), \
                     patch('app.tasks.analysis_task.send_task_failed', mock_websocket_manager['failed']):

                    with pytest.raises(ValidationError):
                        await run_analysis(task_id)

                    mock_websocket_manager['failed'].assert_called()
                    
                    async with test_db() as db:
                        from sqlalchemy import select
                        db_task = await db.execute(select(AnalysisTask).where(AnalysisTask.id == task_id))
                        task = db_task.scalar_one()
                        assert task.status == TaskStatus.FAILED
                        assert "Invalid YouTube URL" in task.error_message

    @pytest.mark.asyncio
    @pytest.mark.error_handling
    async def test_private_unavailable_video_error(
        self,
        test_db,
        mock_websocket_manager
    ):
        """Test error handling for private or unavailable videos"""
        private_video_url = "https://www.youtube.com/watch?v=private_video_id"
        task_id = "error-test-private-video"
        
        async with test_db() as db:
            task = AnalysisTask(
                id=task_id,
                video_url=private_video_url,
                analysis_type=AnalysisType.FULL,
                status=TaskStatus.PENDING,
                progress=0
            )
            db.add(task)
            await db.commit()

        with patch('app.services.youtube_extractor.YouTubeExtractor') as mock_extractor_class:
            mock_extractor = mock_extractor_class.return_value
            mock_extractor.extract_video_id.return_value = "private_video_id"
            mock_extractor.get_video_info.side_effect = ExternalServiceError("Video is private or unavailable")
            
            with patch('app.tasks.analysis_task.send_progress_update', mock_websocket_manager['progress']), \
                 patch('app.tasks.analysis_task.send_task_failed', mock_websocket_manager['failed']):

                with pytest.raises(ExternalServiceError):
                    await run_analysis(task_id)

                async with test_db() as db:
                    from sqlalchemy import select
                    db_task = await db.execute(select(AnalysisTask).where(AnalysisTask.id == task_id))
                    task = db_task.scalar_one()
                    assert task.status == TaskStatus.FAILED
                    assert "private or unavailable" in task.error_message.lower()

    @pytest.mark.asyncio
    @pytest.mark.error_handling
    async def test_youtube_api_quota_exhaustion(
        self,
        test_db,
        mock_websocket_manager
    ):
        """Test error handling for YouTube API quota exhaustion"""
        video_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        task_id = "error-test-quota-exhausted"
        
        async with test_db() as db:
            task = AnalysisTask(
                id=task_id,
                video_url=video_url,
                analysis_type=AnalysisType.FULL,
                status=TaskStatus.PENDING,
                progress=0
            )
            db.add(task)
            await db.commit()

        with patch('app.services.youtube_extractor.YouTubeExtractor') as mock_extractor_class:
            mock_extractor = mock_extractor_class.return_value
            mock_extractor.extract_video_id.return_value = "dQw4w9WgXcQ"
            mock_extractor.get_video_info.side_effect = RateLimitError("YouTube API quota exceeded")
            
            with patch('app.tasks.analysis_task.send_progress_update', mock_websocket_manager['progress']), \
                 patch('app.tasks.analysis_task.send_task_failed', mock_websocket_manager['failed']):

                with pytest.raises(RateLimitError):
                    await run_analysis(task_id)

                async with test_db() as db:
                    from sqlalchemy import select
                    db_task = await db.execute(select(AnalysisTask).where(AnalysisTask.id == task_id))
                    task = db_task.scalar_one()
                    assert task.status == TaskStatus.FAILED
                    assert "quota exceeded" in task.error_message.lower()

    @pytest.mark.asyncio
    @pytest.mark.error_handling
    async def test_openai_api_quota_exhaustion(
        self,
        test_db,
        mock_youtube_extractor,
        mock_transcription_service,
        mock_websocket_manager
    ):
        """Test error handling for OpenAI API quota exhaustion"""
        video_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        task_id = "error-test-openai-quota"
        
        async with test_db() as db:
            task = AnalysisTask(
                id=task_id,
                video_url=video_url,
                analysis_type=AnalysisType.FULL,
                status=TaskStatus.PENDING,
                progress=0
            )
            db.add(task)
            await db.commit()

        with patch('app.services.content_analyzer.ContentAnalyzer') as mock_analyzer_class:
            mock_analyzer = mock_analyzer_class.return_value
            mock_analyzer.analyze.side_effect = RateLimitError("OpenAI API rate limit exceeded")
            
            with patch('app.tasks.analysis_task.YouTubeExtractor', return_value=mock_youtube_extractor), \
                 patch('app.tasks.analysis_task.TranscriptionService', return_value=mock_transcription_service), \
                 patch('app.tasks.analysis_task.send_progress_update', mock_websocket_manager['progress']), \
                 patch('app.tasks.analysis_task.send_task_failed', mock_websocket_manager['failed']):

                with pytest.raises(RateLimitError):
                    await run_analysis(task_id)

                async with test_db() as db:
                    from sqlalchemy import select
                    db_task = await db.execute(select(AnalysisTask).where(AnalysisTask.id == task_id))
                    task = db_task.scalar_one()
                    assert task.status == TaskStatus.FAILED
                    assert "rate limit" in task.error_message.lower()

    @pytest.mark.asyncio
    @pytest.mark.error_handling
    async def test_whisper_service_unavailable(
        self,
        test_db,
        mock_youtube_extractor,
        mock_websocket_manager
    ):
        """Test error handling for Whisper service unavailability"""
        video_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        task_id = "error-test-whisper-unavailable"
        
        async with test_db() as db:
            task = AnalysisTask(
                id=task_id,
                video_url=video_url,
                analysis_type=AnalysisType.FULL,
                status=TaskStatus.PENDING,
                progress=0
            )
            db.add(task)
            await db.commit()

        with patch('app.services.transcription_service.TranscriptionService') as mock_transcription_class:
            mock_transcription = mock_transcription_class.return_value
            mock_transcription.validate_audio_file.return_value = True
            mock_transcription.transcribe_audio.side_effect = ExternalServiceError("Whisper service is currently unavailable")
            
            with patch('app.tasks.analysis_task.YouTubeExtractor', return_value=mock_youtube_extractor), \
                 patch('app.tasks.analysis_task.send_progress_update', mock_websocket_manager['progress']), \
                 patch('app.tasks.analysis_task.send_task_failed', mock_websocket_manager['failed']):

                with pytest.raises(ExternalServiceError):
                    await run_analysis(task_id)

                async with test_db() as db:
                    from sqlalchemy import select
                    db_task = await db.execute(select(AnalysisTask).where(AnalysisTask.id == task_id))
                    task = db_task.scalar_one()
                    assert task.status == TaskStatus.FAILED
                    assert "whisper service" in task.error_message.lower()

    @pytest.mark.asyncio
    @pytest.mark.error_handling
    async def test_network_connection_failure(
        self,
        test_db,
        mock_websocket_manager
    ):
        """Test error handling for network connection failures"""
        video_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        task_id = "error-test-network-failure"
        
        async with test_db() as db:
            task = AnalysisTask(
                id=task_id,
                video_url=video_url,
                analysis_type=AnalysisType.FULL,
                status=TaskStatus.PENDING,
                progress=0
            )
            db.add(task)
            await db.commit()

        network_errors = [
            ConnectionError("Network connection failed"),
            Timeout("Request timed out"),
            HTTPError("HTTP 503 Service Unavailable")
        ]
        
        for error in network_errors:
            with patch('app.services.youtube_extractor.YouTubeExtractor') as mock_extractor_class:
                mock_extractor = mock_extractor_class.return_value
                mock_extractor.extract_video_id.return_value = "dQw4w9WgXcQ"
                mock_extractor.get_video_info.side_effect = error
                
                with patch('app.tasks.analysis_task.send_progress_update', mock_websocket_manager['progress']), \
                     patch('app.tasks.analysis_task.send_task_failed', mock_websocket_manager['failed']):

                    with pytest.raises((ConnectionError, Timeout, HTTPError)):
                        await run_analysis(task_id)

    @pytest.mark.asyncio
    @pytest.mark.error_handling
    async def test_task_timeout_error(
        self,
        test_db,
        mock_youtube_extractor,
        mock_websocket_manager
    ):
        """Test error handling for task timeouts"""
        video_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        task_id = "error-test-timeout"
        
        async with test_db() as db:
            task = AnalysisTask(
                id=task_id,
                video_url=video_url,
                analysis_type=AnalysisType.FULL,
                status=TaskStatus.PENDING,
                progress=0
            )
            db.add(task)
            await db.commit()

        with patch('app.services.transcription_service.TranscriptionService') as mock_transcription_class:
            mock_transcription = mock_transcription_class.return_value
            mock_transcription.validate_audio_file.return_value = True
            
            async def slow_transcription(*args, **kwargs):
                await asyncio.sleep(10)  # Simulate 10 second delay
                return Mock(full_text="test", segments=[], language="en")
            
            mock_transcription.transcribe_audio = slow_transcription
            
            with patch('app.tasks.analysis_task.YouTubeExtractor', return_value=mock_youtube_extractor), \
                 patch('app.tasks.analysis_task.send_progress_update', mock_websocket_manager['progress']), \
                 patch('app.tasks.analysis_task.send_task_failed', mock_websocket_manager['failed']):

                with pytest.raises(asyncio.TimeoutError):
                    await asyncio.wait_for(run_analysis(task_id), timeout=5.0)

    @pytest.mark.asyncio
    @pytest.mark.error_handling
    async def test_cleanup_on_failure(
        self,
        test_db,
        mock_websocket_manager
    ):
        """Test that resources are properly cleaned up on failure"""
        video_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        task_id = "error-test-cleanup"
        
        async with test_db() as db:
            task = AnalysisTask(
                id=task_id,
                video_url=video_url,
                analysis_type=AnalysisType.FULL,
                status=TaskStatus.PENDING,
                progress=0
            )
            db.add(task)
            await db.commit()

        cleanup_called = False
        
        def mock_cleanup():
            nonlocal cleanup_called
            cleanup_called = True

        with patch('app.services.youtube_extractor.YouTubeExtractor') as mock_extractor_class:
            mock_extractor = mock_extractor_class.return_value
            mock_extractor.extract_video_id.return_value = "dQw4w9WgXcQ"
            mock_extractor.get_video_info.return_value = Mock(title="Test", duration=180)
            mock_extractor.download_audio.return_value = "/tmp/test_audio.wav"
            mock_extractor.cleanup_audio_file = Mock(side_effect=mock_cleanup)
            mock_extractor.get_comments.side_effect = ExternalServiceError("Comments API failed")
            
            with patch('app.tasks.analysis_task.send_progress_update', mock_websocket_manager['progress']), \
                 patch('app.tasks.analysis_task.send_task_failed', mock_websocket_manager['failed']):

                with pytest.raises(ExternalServiceError):
                    await run_analysis(task_id)

                mock_extractor.cleanup_audio_file.assert_called()
                assert cleanup_called
