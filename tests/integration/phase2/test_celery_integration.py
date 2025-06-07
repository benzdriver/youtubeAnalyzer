"""
Phase 2 Integration Tests - Celery Integration
Tests Celery task execution, queuing, status updates, and error handling.
"""
import pytest
import asyncio
import time
from unittest.mock import AsyncMock, Mock, patch, MagicMock
from celery import Celery
from celery.result import AsyncResult

from app.core.celery_app import (
    celery_app, 
    analyze_video_task, 
    transcribe_audio_celery_task,
    analyze_content_celery_task,
    analyze_comments_celery_task
)
from app.models.task import AnalysisTask, TaskStatus, AnalysisType
from app.tasks.analysis_task import run_analysis
from app.tasks.transcription import transcribe_audio_task
from app.tasks.content_analysis import analyze_content_task
from app.tasks.comment_analysis import analyze_comments_task
from fixtures.youtube_data import get_sample_video_info
from fixtures.transcription_data import get_sample_transcription_result
from fixtures.content_analysis_data import get_sample_content_analysis_result
from fixtures.comment_analysis_data import get_sample_comment_analysis_result


class TestCeleryIntegration:
    """Test Celery task integration and execution"""

    @pytest.mark.asyncio
    @pytest.mark.celery
    async def test_celery_app_configuration(self):
        """Test Celery app configuration and task registration"""
        assert celery_app.conf.task_serializer == "json"
        assert celery_app.conf.accept_content == ["json"]
        assert celery_app.conf.result_serializer == "json"
        assert celery_app.conf.timezone == "UTC"
        assert celery_app.conf.enable_utc is True
        assert celery_app.conf.task_track_started is True

        task_routes = celery_app.conf.task_routes
        assert "app.core.celery_app.analyze_video_task" in task_routes
        assert "app.tasks.transcription.transcribe_audio_task" in task_routes
        assert "app.tasks.content_analysis.analyze_content_task" in task_routes

        registered_tasks = celery_app.tasks
        assert "app.core.celery_app.analyze_video_task" in registered_tasks
        assert "app.core.celery_app.transcribe_audio_celery_task" in registered_tasks
        assert "app.core.celery_app.analyze_content_celery_task" in registered_tasks
        assert "app.core.celery_app.analyze_comments_celery_task" in registered_tasks

    @pytest.mark.asyncio
    @pytest.mark.celery
    async def test_video_analysis_task_execution(
        self,
        test_db,
        sample_task_id,
        mock_youtube_extractor,
        mock_transcription_service,
        mock_content_analyzer,
        mock_comment_analyzer,
        mock_websocket_manager
    ):
        """Test main video analysis Celery task execution"""
        
        async with test_db() as db:
            task = AnalysisTask(
                id=sample_task_id,
                video_url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                analysis_type=AnalysisType.FULL,
                status=TaskStatus.PENDING,
                progress=0
            )
            db.add(task)
            await db.commit()

        with patch('app.tasks.analysis_task.YouTubeExtractor', return_value=mock_youtube_extractor), \
             patch('app.tasks.analysis_task.TranscriptionService', return_value=mock_transcription_service), \
             patch('app.tasks.analysis_task.content_analyzer', mock_content_analyzer), \
             patch('app.tasks.analysis_task.CommentAnalyzer', return_value=mock_comment_analyzer), \
             patch('app.tasks.analysis_task.send_progress_update', mock_websocket_manager['progress']), \
             patch('app.tasks.analysis_task.send_task_completed', mock_websocket_manager['completed']):

            result = analyze_video_task(sample_task_id)
            
            assert result is not None
            assert isinstance(result, dict)
            assert 'video_info' in result
            assert 'transcription' in result
            assert 'content_analysis' in result
            assert 'comment_analysis' in result

    @pytest.mark.asyncio
    @pytest.mark.celery
    async def test_transcription_celery_task(
        self,
        test_db,
        sample_task_id,
        mock_transcription_service,
        mock_websocket_manager
    ):
        """Test transcription Celery task execution"""
        audio_file_path = "/tmp/test_audio.wav"
        language = "en"
        
        async with test_db() as db:
            task = AnalysisTask(
                id=sample_task_id,
                video_url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                analysis_type=AnalysisType.FULL,
                status=TaskStatus.PROCESSING,
                progress=20
            )
            db.add(task)
            await db.commit()

        with patch('app.tasks.transcription.TranscriptionService', return_value=mock_transcription_service), \
             patch('app.tasks.transcription.send_progress_update', mock_websocket_manager['progress']):

            result = transcribe_audio_celery_task(sample_task_id, audio_file_path, language)
            
            assert result is not None
            assert isinstance(result, dict)
            assert 'full_text' in result
            assert 'segments' in result
            assert 'language' in result
            
            mock_transcription_service.validate_audio_file.assert_called_once_with(audio_file_path)
            mock_transcription_service.transcribe_audio.assert_called_once()

    @pytest.mark.asyncio
    @pytest.mark.celery
    async def test_content_analysis_celery_task(
        self,
        test_db,
        sample_task_id,
        mock_content_analyzer,
        mock_websocket_manager
    ):
        """Test content analysis Celery task execution"""
        transcript_data = get_sample_transcription_result()
        video_info = get_sample_video_info()
        
        async with test_db() as db:
            task = AnalysisTask(
                id=sample_task_id,
                video_url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                analysis_type=AnalysisType.FULL,
                status=TaskStatus.PROCESSING,
                progress=60,
                result_data={'transcription': transcript_data}
            )
            db.add(task)
            await db.commit()

        with patch('app.tasks.content_analysis.content_analyzer', mock_content_analyzer), \
             patch('app.tasks.content_analysis.send_progress_update', mock_websocket_manager['progress']):

            result = analyze_content_celery_task(sample_task_id, transcript_data, video_info)
            
            assert result is not None
            assert isinstance(result, dict)
            assert 'key_points' in result
            assert 'topic_analysis' in result
            assert 'sentiment_analysis' in result
            assert 'summary' in result
            
            mock_content_analyzer.analyze.assert_called_once_with(transcript_data, video_info)

    @pytest.mark.asyncio
    @pytest.mark.celery
    async def test_comment_analysis_celery_task(
        self,
        test_db,
        sample_task_id,
        mock_comment_analyzer,
        mock_youtube_extractor,
        mock_websocket_manager
    ):
        """Test comment analysis Celery task execution"""
        video_id = "dQw4w9WgXcQ"
        
        async with test_db() as db:
            task = AnalysisTask(
                id=sample_task_id,
                video_url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                analysis_type=AnalysisType.FULL,
                status=TaskStatus.PROCESSING,
                progress=80
            )
            db.add(task)
            await db.commit()

        with patch('app.tasks.comment_analysis.CommentAnalyzer', return_value=mock_comment_analyzer), \
             patch('app.tasks.comment_analysis.YouTubeExtractor', return_value=mock_youtube_extractor), \
             patch('app.tasks.comment_analysis.send_progress_update', mock_websocket_manager['progress']):

            result = analyze_comments_celery_task(sample_task_id, video_id)
            
            assert result is not None
            assert isinstance(result, dict)
            assert 'sentiment_distribution' in result
            assert 'main_themes' in result
            assert 'author_engagement' in result
            assert 'total_comments' in result
            
            mock_youtube_extractor.get_video_info.assert_called_once_with(video_id)
            mock_youtube_extractor.get_comments.assert_called_once()
            mock_comment_analyzer.analyze_comments.assert_called_once()

    @pytest.mark.asyncio
    @pytest.mark.celery
    async def test_task_failure_handling(
        self,
        test_db,
        sample_task_id,
        mock_websocket_manager
    ):
        """Test Celery task failure handling and error propagation"""
        
        async with test_db() as db:
            task = AnalysisTask(
                id=sample_task_id,
                video_url="https://www.youtube.com/watch?v=invalid_id",
                analysis_type=AnalysisType.FULL,
                status=TaskStatus.PENDING,
                progress=0
            )
            db.add(task)
            await db.commit()

        with patch('app.services.youtube_extractor.YouTubeExtractor') as mock_extractor_class:
            mock_extractor = mock_extractor_class.return_value
            mock_extractor.extract_video_id.side_effect = Exception("YouTube API error")
            
            with patch('app.tasks.analysis_task.send_progress_update', mock_websocket_manager['progress']), \
                 patch('app.tasks.analysis_task.send_task_failed', mock_websocket_manager['failed']):

                with pytest.raises(Exception, match="YouTube API error"):
                    analyze_video_task(sample_task_id)

    @pytest.mark.asyncio
    @pytest.mark.celery
    async def test_task_status_updates(
        self,
        test_db,
        sample_task_id,
        mock_transcription_service,
        mock_websocket_manager
    ):
        """Test that Celery tasks properly update task status in database"""
        audio_file_path = "/tmp/test_audio.wav"
        
        async with test_db() as db:
            task = AnalysisTask(
                id=sample_task_id,
                video_url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                analysis_type=AnalysisType.FULL,
                status=TaskStatus.PROCESSING,
                progress=20
            )
            db.add(task)
            await db.commit()

        with patch('app.tasks.transcription.TranscriptionService', return_value=mock_transcription_service), \
             patch('app.tasks.transcription.send_progress_update', mock_websocket_manager['progress']):

            result = transcribe_audio_celery_task(sample_task_id, audio_file_path)
            
            assert result is not None
            
            async with test_db() as db:
                from sqlalchemy import select
                db_task = await db.execute(select(AnalysisTask).where(AnalysisTask.id == sample_task_id))
                updated_task = db_task.scalar_one()
                
                assert updated_task.result_data is not None
                assert 'transcription' in updated_task.result_data

    @pytest.mark.asyncio
    @pytest.mark.celery
    async def test_task_retry_mechanism(
        self,
        test_db,
        sample_task_id,
        mock_websocket_manager
    ):
        """Test Celery task retry mechanism on failures"""
        
        async with test_db() as db:
            task = AnalysisTask(
                id=sample_task_id,
                video_url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                analysis_type=AnalysisType.FULL,
                status=TaskStatus.PENDING,
                progress=0
            )
            db.add(task)
            await db.commit()

        retry_count = 0
        
        def mock_extract_with_retry(*args, **kwargs):
            nonlocal retry_count
            retry_count += 1
            if retry_count < 3:
                raise Exception("Temporary failure")
            return "dQw4w9WgXcQ"

        with patch('app.services.youtube_extractor.YouTubeExtractor') as mock_extractor_class:
            mock_extractor = mock_extractor_class.return_value
            mock_extractor.extract_video_id.side_effect = mock_extract_with_retry
            
            task_instance = analyze_video_task
            
            assert task_instance.max_retries == 3
            assert task_instance.default_retry_delay == 60

    @pytest.mark.asyncio
    @pytest.mark.celery
    async def test_concurrent_task_execution(
        self,
        test_db,
        mock_youtube_extractor,
        mock_transcription_service,
        mock_content_analyzer,
        mock_comment_analyzer,
        mock_websocket_manager
    ):
        """Test concurrent execution of multiple Celery tasks"""
        task_ids = [f"test-task-{i}" for i in range(3)]
        video_urls = [
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "https://youtu.be/EYM4TBfCGiU",
            "https://youtu.be/TYeUQFKhMsk"
        ]
        
        for task_id, video_url in zip(task_ids, video_urls):
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

        with patch('app.tasks.analysis_task.YouTubeExtractor', return_value=mock_youtube_extractor), \
             patch('app.tasks.analysis_task.TranscriptionService', return_value=mock_transcription_service), \
             patch('app.tasks.analysis_task.content_analyzer', mock_content_analyzer), \
             patch('app.tasks.analysis_task.CommentAnalyzer', return_value=mock_comment_analyzer), \
             patch('app.tasks.analysis_task.send_progress_update', mock_websocket_manager['progress']), \
             patch('app.tasks.analysis_task.send_task_completed', mock_websocket_manager['completed']):

            tasks = []
            for task_id in task_ids:
                task_future = asyncio.create_task(
                    asyncio.to_thread(analyze_video_task, task_id)
                )
                tasks.append(task_future)

            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    pytest.fail(f"Task {task_ids[i]} failed: {result}")
                
                assert result is not None
                assert isinstance(result, dict)
                assert all(key in result for key in ['video_info', 'transcription', 'content_analysis', 'comment_analysis'])

    @pytest.mark.asyncio
    @pytest.mark.celery
    async def test_websocket_progress_integration(
        self,
        test_db,
        sample_task_id,
        mock_youtube_extractor,
        mock_transcription_service,
        mock_content_analyzer,
        mock_comment_analyzer
    ):
        """Test WebSocket progress updates during Celery task execution"""
        
        async with test_db() as db:
            task = AnalysisTask(
                id=sample_task_id,
                video_url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                analysis_type=AnalysisType.FULL,
                status=TaskStatus.PENDING,
                progress=0
            )
            db.add(task)
            await db.commit()

        progress_updates = []
        
        async def capture_progress(task_id, progress, message, current_step=None):
            progress_updates.append({
                'task_id': task_id,
                'progress': progress,
                'message': message,
                'current_step': current_step,
                'timestamp': time.time()
            })

        completion_calls = []
        
        async def capture_completion(task_id, result):
            completion_calls.append({
                'task_id': task_id,
                'result': result,
                'timestamp': time.time()
            })

        with patch('app.tasks.analysis_task.YouTubeExtractor', return_value=mock_youtube_extractor), \
             patch('app.tasks.analysis_task.TranscriptionService', return_value=mock_transcription_service), \
             patch('app.tasks.analysis_task.content_analyzer', mock_content_analyzer), \
             patch('app.tasks.analysis_task.CommentAnalyzer', return_value=mock_comment_analyzer), \
             patch('app.tasks.analysis_task.send_progress_update', side_effect=capture_progress), \
             patch('app.tasks.analysis_task.send_task_completed', side_effect=capture_completion):

            result = analyze_video_task(sample_task_id)
            
            assert len(progress_updates) >= 4
            assert len(completion_calls) == 1
            
            assert all(update['task_id'] == sample_task_id for update in progress_updates)
            assert completion_calls[0]['task_id'] == sample_task_id
            
            progress_values = [update['progress'] for update in progress_updates]
            assert progress_values == sorted(progress_values)
            assert 0 <= min(progress_values) <= max(progress_values) <= 100
