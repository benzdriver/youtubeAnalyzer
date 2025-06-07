"""
Phase 2 Integration Tests - Performance Testing
Tests performance benchmarks for video analysis with different video lengths.
"""
import pytest
import asyncio
import time
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime, timedelta

from app.models.task import AnalysisTask, TaskStatus, AnalysisType
from app.tasks.analysis_task import run_analysis
from fixtures.youtube_data import get_sample_video_info
from fixtures.transcription_data import get_sample_transcription_result
from fixtures.content_analysis_data import get_sample_content_analysis_result
from fixtures.comment_analysis_data import get_sample_comment_analysis_result


class TestPerformance:
    """Test performance benchmarks for video analysis"""

    @pytest.mark.asyncio
    @pytest.mark.performance
    @pytest.mark.slow
    async def test_short_video_analysis_performance(
        self,
        mock_youtube_extractor,
        mock_transcription_service,
        mock_content_analyzer,
        mock_comment_analyzer
    ):
        """Test that short video (3min) analysis completes within 5 minutes"""
        video_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Short video (3min)
        task_id = "perf-test-short-video"
        
        short_video_info = get_sample_video_info()
        short_video_info['duration'] = 180  # 3 minutes
        mock_youtube_extractor.get_video_info = AsyncMock(return_value=Mock(**short_video_info))
        
        async def mock_transcribe_with_delay(*args, **kwargs):
            await asyncio.sleep(0.5)  # Simulate 0.5s transcription time
            return Mock(**get_sample_transcription_result())
        
        async def mock_content_analysis_with_delay(*args, **kwargs):
            await asyncio.sleep(0.3)  # Simulate 0.3s content analysis time
            return Mock(**get_sample_content_analysis_result())
        
        async def mock_comment_analysis_with_delay(*args, **kwargs):
            await asyncio.sleep(0.2)  # Simulate 0.2s comment analysis time
            return Mock(**get_sample_comment_analysis_result())
        
        mock_transcription_service.transcribe_audio = mock_transcribe_with_delay
        mock_content_analyzer.analyze = mock_content_analysis_with_delay
        mock_comment_analyzer.analyze_comments = mock_comment_analysis_with_delay
        
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

        start_time = time.time()
        
        with patch('app.tasks.analysis_task.YouTubeExtractor', return_value=mock_youtube_extractor), \
             patch('app.tasks.analysis_task.TranscriptionService', return_value=mock_transcription_service), \
             patch('app.tasks.analysis_task.content_analyzer', mock_content_analyzer), \
             patch('app.tasks.analysis_task.CommentAnalyzer', return_value=mock_comment_analyzer), \
             patch('app.tasks.analysis_task.send_progress_update', mock_websocket_manager['progress']), \
             patch('app.tasks.analysis_task.send_task_completed', mock_websocket_manager['completed']):

            result = await run_analysis(task_id)
            
        end_time = time.time()
        execution_time = end_time - start_time
        
        assert execution_time < 300, f"Short video analysis took {execution_time:.2f}s, expected < 300s"
        assert result is not None
        assert all(key in result for key in ['video_info', 'transcription', 'content_analysis', 'comment_analysis'])

    @pytest.mark.asyncio
    @pytest.mark.performance
    @pytest.mark.slow
    async def test_medium_video_analysis_performance(
        self,
        test_db,
        mock_youtube_extractor,
        mock_transcription_service,
        mock_content_analyzer,
        mock_comment_analyzer,
        mock_websocket_manager
    ):
        """Test that medium video (15min) analysis completes within 15 minutes"""
        video_url = "https://youtu.be/EYM4TBfCGiU"  # Medium video (15min)
        task_id = "perf-test-medium-video"
        
        medium_video_info = get_sample_video_info()
        medium_video_info['duration'] = 900  # 15 minutes
        mock_youtube_extractor.get_video_info = AsyncMock(return_value=Mock(**medium_video_info))
        
        async def mock_transcribe_with_delay(*args, **kwargs):
            await asyncio.sleep(2.0)  # Simulate 2s transcription time
            return Mock(**get_sample_transcription_result())
        
        async def mock_content_analysis_with_delay(*args, **kwargs):
            await asyncio.sleep(1.5)  # Simulate 1.5s content analysis time
            return Mock(**get_sample_content_analysis_result())
        
        async def mock_comment_analysis_with_delay(*args, **kwargs):
            await asyncio.sleep(1.0)  # Simulate 1s comment analysis time
            return Mock(**get_sample_comment_analysis_result())
        
        mock_transcription_service.transcribe_audio = mock_transcribe_with_delay
        mock_content_analyzer.analyze = mock_content_analysis_with_delay
        mock_comment_analyzer.analyze_comments = mock_comment_analysis_with_delay
        
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

        start_time = time.time()
        
        with patch('app.tasks.analysis_task.YouTubeExtractor', return_value=mock_youtube_extractor), \
             patch('app.tasks.analysis_task.TranscriptionService', return_value=mock_transcription_service), \
             patch('app.tasks.analysis_task.content_analyzer', mock_content_analyzer), \
             patch('app.tasks.analysis_task.CommentAnalyzer', return_value=mock_comment_analyzer), \
             patch('app.tasks.analysis_task.send_progress_update', mock_websocket_manager['progress']), \
             patch('app.tasks.analysis_task.send_task_completed', mock_websocket_manager['completed']):

            result = await run_analysis(task_id)
            
        end_time = time.time()
        execution_time = end_time - start_time
        
        assert execution_time < 900, f"Medium video analysis took {execution_time:.2f}s, expected < 900s"
        assert result is not None
        assert all(key in result for key in ['video_info', 'transcription', 'content_analysis', 'comment_analysis'])

    @pytest.mark.asyncio
    @pytest.mark.performance
    @pytest.mark.slow
    async def test_long_video_analysis_performance(
        self,
        test_db,
        mock_youtube_extractor,
        mock_transcription_service,
        mock_content_analyzer,
        mock_comment_analyzer,
        mock_websocket_manager
    ):
        """Test that long video (45min) analysis completes within 30 minutes"""
        video_url = "https://youtu.be/TYeUQFKhMsk"  # Long video (45min)
        task_id = "perf-test-long-video"
        
        long_video_info = get_sample_video_info()
        long_video_info['duration'] = 2700  # 45 minutes
        mock_youtube_extractor.get_video_info = AsyncMock(return_value=Mock(**long_video_info))
        
        async def mock_transcribe_with_delay(*args, **kwargs):
            await asyncio.sleep(5.0)  # Simulate 5s transcription time
            return Mock(**get_sample_transcription_result())
        
        async def mock_content_analysis_with_delay(*args, **kwargs):
            await asyncio.sleep(3.0)  # Simulate 3s content analysis time
            return Mock(**get_sample_content_analysis_result())
        
        async def mock_comment_analysis_with_delay(*args, **kwargs):
            await asyncio.sleep(2.0)  # Simulate 2s comment analysis time
            return Mock(**get_sample_comment_analysis_result())
        
        mock_transcription_service.transcribe_audio = mock_transcribe_with_delay
        mock_content_analyzer.analyze = mock_content_analysis_with_delay
        mock_comment_analyzer.analyze_comments = mock_comment_analysis_with_delay
        
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

        start_time = time.time()
        
        with patch('app.tasks.analysis_task.YouTubeExtractor', return_value=mock_youtube_extractor), \
             patch('app.tasks.analysis_task.TranscriptionService', return_value=mock_transcription_service), \
             patch('app.tasks.analysis_task.content_analyzer', mock_content_analyzer), \
             patch('app.tasks.analysis_task.CommentAnalyzer', return_value=mock_comment_analyzer), \
             patch('app.tasks.analysis_task.send_progress_update', mock_websocket_manager['progress']), \
             patch('app.tasks.analysis_task.send_task_completed', mock_websocket_manager['completed']):

            result = await run_analysis(task_id)
            
        end_time = time.time()
        execution_time = end_time - start_time
        
        assert execution_time < 1800, f"Long video analysis took {execution_time:.2f}s, expected < 1800s"
        assert result is not None
        assert all(key in result for key in ['video_info', 'transcription', 'content_analysis', 'comment_analysis'])

    @pytest.mark.asyncio
    @pytest.mark.performance
    @pytest.mark.slow
    async def test_concurrent_analysis_performance(
        self,
        test_db,
        test_videos,
        mock_youtube_extractor,
        mock_transcription_service,
        mock_content_analyzer,
        mock_comment_analyzer,
        mock_websocket_manager
    ):
        """Test concurrent processing of multiple videos without performance degradation"""
        
        task_ids = [f"perf-test-concurrent-{i}" for i in range(3)]
        video_urls = test_videos[:3]
        
        async def mock_transcribe_with_delay(*args, **kwargs):
            await asyncio.sleep(1.0)  # Simulate 1s transcription time
            return Mock(**get_sample_transcription_result())
        
        async def mock_content_analysis_with_delay(*args, **kwargs):
            await asyncio.sleep(0.8)  # Simulate 0.8s content analysis time
            return Mock(**get_sample_content_analysis_result())
        
        async def mock_comment_analysis_with_delay(*args, **kwargs):
            await asyncio.sleep(0.5)  # Simulate 0.5s comment analysis time
            return Mock(**get_sample_comment_analysis_result())
        
        mock_transcription_service.transcribe_audio = mock_transcribe_with_delay
        mock_content_analyzer.analyze = mock_content_analysis_with_delay
        mock_comment_analyzer.analyze_comments = mock_comment_analysis_with_delay
        
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

        start_time = time.time()
        
        with patch('app.tasks.analysis_task.YouTubeExtractor', return_value=mock_youtube_extractor), \
             patch('app.tasks.analysis_task.TranscriptionService', return_value=mock_transcription_service), \
             patch('app.tasks.analysis_task.content_analyzer', mock_content_analyzer), \
             patch('app.tasks.analysis_task.CommentAnalyzer', return_value=mock_comment_analyzer), \
             patch('app.tasks.analysis_task.send_progress_update', mock_websocket_manager['progress']), \
             patch('app.tasks.analysis_task.send_task_completed', mock_websocket_manager['completed']):

            tasks = [run_analysis(task_id) for task_id in task_ids]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
        end_time = time.time()
        execution_time = end_time - start_time
        
        max_expected_time = 10.0  # Allow some overhead for concurrency
        assert execution_time < max_expected_time, f"Concurrent analysis took {execution_time:.2f}s, expected < {max_expected_time}s"
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                pytest.fail(f"Task {task_ids[i]} failed: {result}")
            
            assert result is not None
            assert isinstance(result, dict)
            assert all(key in result for key in ['video_info', 'transcription', 'content_analysis', 'comment_analysis'])

    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_memory_usage_during_analysis(
        self,
        test_db,
        mock_youtube_extractor,
        mock_transcription_service,
        mock_content_analyzer,
        mock_comment_analyzer,
        mock_websocket_manager
    ):
        """Test memory usage remains within acceptable limits during analysis"""
        import psutil
        import os
        
        video_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        task_id = "perf-test-memory"
        
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

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        with patch('app.tasks.analysis_task.YouTubeExtractor', return_value=mock_youtube_extractor), \
             patch('app.tasks.analysis_task.TranscriptionService', return_value=mock_transcription_service), \
             patch('app.tasks.analysis_task.content_analyzer', mock_content_analyzer), \
             patch('app.tasks.analysis_task.CommentAnalyzer', return_value=mock_comment_analyzer), \
             patch('app.tasks.analysis_task.send_progress_update', mock_websocket_manager['progress']), \
             patch('app.tasks.analysis_task.send_task_completed', mock_websocket_manager['completed']):

            result = await run_analysis(task_id)
            
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        max_memory_increase = 2048  # MB
        assert memory_increase < max_memory_increase, f"Memory increased by {memory_increase:.2f}MB, expected < {max_memory_increase}MB"
        
        assert result is not None

    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_progress_update_frequency(
        self,
        test_db,
        mock_youtube_extractor,
        mock_transcription_service,
        mock_content_analyzer,
        mock_comment_analyzer
    ):
        """Test that progress updates are sent at appropriate frequency"""
        video_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        task_id = "perf-test-progress"
        
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

        progress_updates = []
        update_timestamps = []
        
        async def capture_progress_with_timing(task_id, progress, message, current_step=None):
            progress_updates.append({
                'task_id': task_id,
                'progress': progress,
                'message': message,
                'current_step': current_step
            })
            update_timestamps.append(time.time())

        start_time = time.time()
        
        with patch('app.tasks.analysis_task.YouTubeExtractor', return_value=mock_youtube_extractor), \
             patch('app.tasks.analysis_task.TranscriptionService', return_value=mock_transcription_service), \
             patch('app.tasks.analysis_task.content_analyzer', mock_content_analyzer), \
             patch('app.tasks.analysis_task.CommentAnalyzer', return_value=mock_comment_analyzer), \
             patch('app.tasks.analysis_task.send_progress_update', side_effect=capture_progress_with_timing), \
             patch('app.tasks.analysis_task.send_task_completed', AsyncMock()):

            result = await run_analysis(task_id)
            
        end_time = time.time()
        total_time = end_time - start_time
        
        assert len(progress_updates) >= 4, f"Expected at least 4 progress updates, got {len(progress_updates)}"
        
        if len(update_timestamps) > 1:
            min_interval = min(update_timestamps[i+1] - update_timestamps[i] for i in range(len(update_timestamps)-1))
            assert min_interval >= 0.05, f"Progress updates too frequent: minimum interval {min_interval:.3f}s"
        
        progress_values = [update['progress'] for update in progress_updates]
        assert progress_values == sorted(progress_values), "Progress values should be monotonically increasing"
        
        assert result is not None

    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_database_query_performance(
        self,
        test_db,
        mock_youtube_extractor,
        mock_transcription_service,
        mock_content_analyzer,
        mock_comment_analyzer,
        mock_websocket_manager
    ):
        """Test database query performance during analysis"""
        video_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        task_id = "perf-test-db"
        
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

        db_operation_times = []
        
        with patch('app.tasks.analysis_task.YouTubeExtractor', return_value=mock_youtube_extractor), \
             patch('app.tasks.analysis_task.TranscriptionService', return_value=mock_transcription_service), \
             patch('app.tasks.analysis_task.content_analyzer', mock_content_analyzer), \
             patch('app.tasks.analysis_task.CommentAnalyzer', return_value=mock_comment_analyzer), \
             patch('app.tasks.analysis_task.send_progress_update', mock_websocket_manager['progress']), \
             patch('app.tasks.analysis_task.send_task_completed', mock_websocket_manager['completed']):

            start_time = time.time()
            result = await run_analysis(task_id)
            end_time = time.time()
            
            db_operation_time = end_time - start_time
            db_operation_times.append(db_operation_time)
        
        if db_operation_times:
            max_db_time = max(db_operation_times)
            avg_db_time = sum(db_operation_times) / len(db_operation_times)
            
            assert max_db_time < 1.0, f"Database operation took {max_db_time:.3f}s, expected < 1.0s"
            assert avg_db_time < 0.5, f"Average database operation took {avg_db_time:.3f}s, expected < 0.5s"
        
        assert result is not None
