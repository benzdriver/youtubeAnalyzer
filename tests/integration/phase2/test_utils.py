"""
Phase 2 Integration Tests - Test Utilities
Helper functions and utilities for Phase 2 integration testing.
"""
import os
import json
import tempfile
import asyncio
from typing import Dict, Any, List, Optional
from unittest.mock import Mock, AsyncMock, patch
from pathlib import Path

from app.models.task import AnalysisTask, TaskStatus, AnalysisType
from fixtures.youtube_data import (
    get_sample_video_info, get_sample_comments_data, get_sample_extraction_result
)
from fixtures.transcription_data import (
    get_sample_transcription_result, get_sample_transcript_segments
)
from fixtures.content_analysis_data import (
    get_sample_content_analysis_result, get_sample_key_points
)
from fixtures.comment_analysis_data import (
    get_sample_comment_analysis_result, get_sample_sentiment_distribution
)


class TestDataManager:
    """Manages test data creation and cleanup"""
    
    def __init__(self):
        self.temp_files = []
        self.temp_dirs = []
    
    def create_temp_audio_file(self, duration_seconds: int = 180) -> str:
        """Create a temporary audio file for testing"""
        temp_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
        temp_file.close()
        
        sample_rate = 44100
        num_channels = 1
        bits_per_sample = 16
        num_samples = duration_seconds * sample_rate
        
        with open(temp_file.name, 'wb') as f:
            f.write(b'RIFF')
            f.write((36 + num_samples * num_channels * bits_per_sample // 8).to_bytes(4, 'little'))
            f.write(b'WAVE')
            f.write(b'fmt ')
            f.write((16).to_bytes(4, 'little'))
            f.write((1).to_bytes(2, 'little'))  # PCM format
            f.write(num_channels.to_bytes(2, 'little'))
            f.write(sample_rate.to_bytes(4, 'little'))
            f.write((sample_rate * num_channels * bits_per_sample // 8).to_bytes(4, 'little'))
            f.write((num_channels * bits_per_sample // 8).to_bytes(2, 'little'))
            f.write(bits_per_sample.to_bytes(2, 'little'))
            f.write(b'data')
            f.write((num_samples * num_channels * bits_per_sample // 8).to_bytes(4, 'little'))
            
            f.write(b'\x00' * (num_samples * num_channels * bits_per_sample // 8))
        
        self.temp_files.append(temp_file.name)
        return temp_file.name
    
    def create_temp_directory(self) -> str:
        """Create a temporary directory for testing"""
        temp_dir = tempfile.mkdtemp()
        self.temp_dirs.append(temp_dir)
        return temp_dir
    
    def cleanup(self):
        """Clean up all temporary files and directories"""
        for file_path in self.temp_files:
            try:
                os.unlink(file_path)
            except FileNotFoundError:
                pass
        
        for dir_path in self.temp_dirs:
            try:
                import shutil
                shutil.rmtree(dir_path)
            except FileNotFoundError:
                pass
        
        self.temp_files.clear()
        self.temp_dirs.clear()


class MockServiceFactory:
    """Factory for creating mock services with configurable behavior"""
    
    @staticmethod
    def create_youtube_extractor_mock(
        use_real_api: bool = False,
        video_info_override: Optional[Dict] = None,
        comments_override: Optional[List[Dict]] = None,
        should_fail: bool = False,
        failure_message: str = "Mock failure"
    ):
        """Create a mock YouTube extractor with configurable behavior"""
        if use_real_api:
            raise NotImplementedError("Real API usage not implemented in mock factory")
        
        mock = Mock()
        
        if should_fail:
            mock.extract_video_id.side_effect = Exception(failure_message)
            mock.get_video_info = AsyncMock(side_effect=Exception(failure_message))
            mock.download_audio = AsyncMock(side_effect=Exception(failure_message))
            mock.get_comments = AsyncMock(side_effect=Exception(failure_message))
        else:
            mock.extract_video_id.return_value = 'dQw4w9WgXcQ'
            mock.get_video_info = AsyncMock(return_value=Mock(**(video_info_override or get_sample_video_info())))
            mock.download_audio = AsyncMock(return_value='/tmp/test_audio.wav')
            mock.get_comments = AsyncMock(return_value=[
                Mock(**comment) for comment in (comments_override or get_sample_comments_data())
            ])
        
        mock.cleanup_audio_file = AsyncMock()
        return mock
    
    @staticmethod
    def create_transcription_service_mock(
        use_real_api: bool = False,
        transcription_override: Optional[Dict] = None,
        should_fail: bool = False,
        failure_message: str = "Mock transcription failure"
    ):
        """Create a mock transcription service with configurable behavior"""
        if use_real_api:
            raise NotImplementedError("Real API usage not implemented in mock factory")
        
        mock = Mock()
        
        if should_fail:
            mock.validate_audio_file.side_effect = Exception(failure_message)
            mock.detect_language = AsyncMock(side_effect=Exception(failure_message))
            mock.transcribe_audio = AsyncMock(side_effect=Exception(failure_message))
        else:
            mock.validate_audio_file.return_value = True
            mock.detect_language = AsyncMock(return_value={'language': 'en', 'confidence': 0.98})
            mock.transcribe_audio = AsyncMock(return_value=Mock(**(transcription_override or get_sample_transcription_result())))
        
        return mock
    
    @staticmethod
    def create_content_analyzer_mock(
        use_real_api: bool = False,
        analysis_override: Optional[Dict] = None,
        should_fail: bool = False,
        failure_message: str = "Mock content analysis failure"
    ):
        """Create a mock content analyzer with configurable behavior"""
        if use_real_api:
            raise NotImplementedError("Real API usage not implemented in mock factory")
        
        mock = Mock()
        
        if should_fail:
            mock.analyze = AsyncMock(side_effect=Exception(failure_message))
        else:
            mock.analyze = AsyncMock(return_value=Mock(**(analysis_override or get_sample_content_analysis_result())))
        
        return mock
    
    @staticmethod
    def create_comment_analyzer_mock(
        use_real_api: bool = False,
        analysis_override: Optional[Dict] = None,
        should_fail: bool = False,
        failure_message: str = "Mock comment analysis failure"
    ):
        """Create a mock comment analyzer with configurable behavior"""
        if use_real_api:
            raise NotImplementedError("Real API usage not implemented in mock factory")
        
        mock = Mock()
        
        if should_fail:
            mock.analyze_comments = AsyncMock(side_effect=Exception(failure_message))
        else:
            mock.analyze_comments = AsyncMock(return_value=Mock(**(analysis_override or get_sample_comment_analysis_result())))
        
        return mock


class ConfigurableMockManager:
    """Manages configurable mocking that can switch between real and fake APIs"""
    
    def __init__(self, use_real_apis: bool = False):
        self.use_real_apis = use_real_apis
        self.active_patches = []
    
    def setup_youtube_extractor_mock(self, **kwargs):
        """Setup YouTube extractor mock with configuration"""
        mock = MockServiceFactory.create_youtube_extractor_mock(
            use_real_api=self.use_real_apis,
            **kwargs
        )
        
        if not self.use_real_apis:
            patch_obj = patch('app.services.youtube_extractor.YouTubeExtractor', return_value=mock)
            self.active_patches.append(patch_obj)
            return patch_obj.start()
        
        return mock
    
    def setup_transcription_service_mock(self, **kwargs):
        """Setup transcription service mock with configuration"""
        mock = MockServiceFactory.create_transcription_service_mock(
            use_real_api=self.use_real_apis,
            **kwargs
        )
        
        if not self.use_real_apis:
            patch_obj = patch('app.services.transcription_service.TranscriptionService', return_value=mock)
            self.active_patches.append(patch_obj)
            return patch_obj.start()
        
        return mock
    
    def setup_content_analyzer_mock(self, **kwargs):
        """Setup content analyzer mock with configuration"""
        mock = MockServiceFactory.create_content_analyzer_mock(
            use_real_api=self.use_real_apis,
            **kwargs
        )
        
        if not self.use_real_apis:
            patch_obj = patch('app.services.content_analyzer.content_analyzer', mock)
            self.active_patches.append(patch_obj)
            return patch_obj.start()
        
        return mock
    
    def setup_comment_analyzer_mock(self, **kwargs):
        """Setup comment analyzer mock with configuration"""
        mock = MockServiceFactory.create_comment_analyzer_mock(
            use_real_api=self.use_real_apis,
            **kwargs
        )
        
        if not self.use_real_apis:
            patch_obj = patch('app.services.comment_analyzer.CommentAnalyzer', return_value=mock)
            self.active_patches.append(patch_obj)
            return patch_obj.start()
        
        return mock
    
    def setup_websocket_mocks(self):
        """Setup WebSocket mocks for progress updates"""
        mocks = {
            'progress': AsyncMock(),
            'completed': AsyncMock(),
            'failed': AsyncMock()
        }
        
        progress_patch = patch('app.api.v1.websocket.send_progress_update', mocks['progress'])
        completed_patch = patch('app.api.v1.websocket.send_task_completed', mocks['completed'])
        failed_patch = patch('app.api.v1.websocket.send_task_failed', mocks['failed'])
        
        self.active_patches.extend([progress_patch, completed_patch, failed_patch])
        
        progress_patch.start()
        completed_patch.start()
        failed_patch.start()
        
        return mocks
    
    def cleanup(self):
        """Stop all active patches"""
        for patch_obj in self.active_patches:
            try:
                patch_obj.stop()
            except RuntimeError:
                pass
        self.active_patches.clear()


class TaskTestHelper:
    """Helper for creating and managing test tasks"""
    
    @staticmethod
    async def create_test_task(
        db_session,
        task_id: str,
        video_url: str,
        analysis_type: AnalysisType = AnalysisType.FULL,
        status: TaskStatus = TaskStatus.PENDING
    ) -> AnalysisTask:
        """Create a test task in the database"""
        task = AnalysisTask(
            id=task_id,
            video_url=video_url,
            analysis_type=analysis_type,
            status=status,
            progress=0
        )
        db_session.add(task)
        await db_session.commit()
        return task
    
    @staticmethod
    async def update_task_status(
        db_session,
        task_id: str,
        status: TaskStatus,
        progress: Optional[int] = None,
        error_message: Optional[str] = None
    ):
        """Update task status in the database"""
        from sqlalchemy import select, update
        
        update_data = {'status': status}
        if progress is not None:
            update_data['progress'] = progress
        if error_message is not None:
            update_data['error_message'] = error_message
        
        await db_session.execute(
            update(AnalysisTask)
            .where(AnalysisTask.id == task_id)
            .values(**update_data)
        )
        await db_session.commit()
    
    @staticmethod
    async def get_task_by_id(db_session, task_id: str) -> Optional[AnalysisTask]:
        """Get task by ID from the database"""
        from sqlalchemy import select
        
        result = await db_session.execute(
            select(AnalysisTask).where(AnalysisTask.id == task_id)
        )
        return result.scalar_one_or_none()


class APITestHelper:
    """Helper for API testing scenarios"""
    
    @staticmethod
    def create_analysis_request(video_url: str, analysis_type: str = "full") -> Dict[str, Any]:
        """Create a standard analysis request payload"""
        return {
            "video_url": video_url,
            "analysis_type": analysis_type
        }
    
    @staticmethod
    def validate_analysis_response(response_data: Dict[str, Any]) -> bool:
        """Validate that an analysis response has the expected structure"""
        required_fields = ['task_id', 'status', 'video_url']
        return all(field in response_data for field in required_fields)
    
    @staticmethod
    def validate_task_status_response(response_data: Dict[str, Any]) -> bool:
        """Validate that a task status response has the expected structure"""
        required_fields = ['task_id', 'status', 'progress']
        return all(field in response_data for field in required_fields)
    
    @staticmethod
    def validate_completed_task_response(response_data: Dict[str, Any]) -> bool:
        """Validate that a completed task response has the expected structure"""
        required_fields = ['task_id', 'status', 'results']
        if not all(field in response_data for field in required_fields):
            return False
        
        if response_data['status'] == 'completed':
            results = response_data.get('results', {})
            required_result_fields = ['video_info', 'transcription', 'content_analysis', 'comment_analysis']
            return all(field in results for field in required_result_fields)
        
        return True


class PerformanceTestHelper:
    """Helper for performance testing scenarios"""
    
    @staticmethod
    def create_performance_monitor():
        """Create a performance monitor for tracking metrics"""
        return {
            'start_time': None,
            'end_time': None,
            'memory_usage': [],
            'progress_updates': [],
            'db_operations': []
        }
    
    @staticmethod
    def start_monitoring(monitor: Dict[str, Any]):
        """Start performance monitoring"""
        import time
        monitor['start_time'] = time.time()
    
    @staticmethod
    def stop_monitoring(monitor: Dict[str, Any]):
        """Stop performance monitoring"""
        import time
        monitor['end_time'] = time.time()
    
    @staticmethod
    def get_duration(monitor: Dict[str, Any]) -> float:
        """Get the duration of the monitored operation"""
        if monitor['start_time'] and monitor['end_time']:
            return monitor['end_time'] - monitor['start_time']
        return 0.0
    
    @staticmethod
    def record_memory_usage(monitor: Dict[str, Any]):
        """Record current memory usage"""
        try:
            import psutil
            import os
            process = psutil.Process(os.getpid())
            memory_mb = process.memory_info().rss / 1024 / 1024
            monitor['memory_usage'].append(memory_mb)
        except ImportError:
            pass
    
    @staticmethod
    def get_peak_memory_usage(monitor: Dict[str, Any]) -> float:
        """Get peak memory usage during monitoring"""
        if monitor['memory_usage']:
            return max(monitor['memory_usage'])
        return 0.0


def get_test_video_urls() -> List[str]:
    """Get the standard test video URLs for Phase 2 testing"""
    return [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",  # Short video (3min)
        "https://youtu.be/EYM4TBfCGiU",  # Medium video (15min)
        "https://youtu.be/TYeUQFKhMsk",  # Long video (45min)
        "https://www.youtube.com/watch?v=jNQXAC9IVRw"   # Comments-heavy video
    ]


def get_invalid_video_urls() -> List[str]:
    """Get invalid video URLs for error testing"""
    return [
        "https://www.youtube.com/watch?v=invalid_video_id_12345",
        "https://youtu.be/nonexistent_video",
        "https://www.youtube.com/watch?v=",
        "not_a_url_at_all",
        "https://vimeo.com/123456789"  # Different platform
    ]


async def wait_for_task_completion(
    client,
    task_id: str,
    timeout: int = 300,
    poll_interval: int = 2
) -> Dict[str, Any]:
    """Wait for a task to complete and return the final result"""
    import time
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        response = client.get(f"/api/v1/tasks/{task_id}")
        if response.status_code == 200:
            data = response.json()
            status = data.get('status')
            
            if status in ['completed', 'failed']:
                return data
        
        await asyncio.sleep(poll_interval)
    
    raise TimeoutError(f"Task {task_id} did not complete within {timeout} seconds")
