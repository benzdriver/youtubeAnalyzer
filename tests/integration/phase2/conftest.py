import pytest
import asyncio
import os
import sys
from unittest.mock import AsyncMock, Mock, patch
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../backend"))
sys.path.insert(0, backend_path)

from app.core.database import get_db_session
from app.models.task import Base
from app.main import app
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

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Set up test environment variables."""
    os.environ.setdefault("ENVIRONMENT", "test")
    os.environ.setdefault("DEBUG", "true")
    os.environ.setdefault("DATABASE_URL", "postgresql://test_user:test_password@localhost:5432/youtube_analyzer_test")
    os.environ.setdefault("REDIS_URL", "redis://localhost:6379/1")
    os.environ.setdefault("SECRET_KEY", "test_secret_key_for_integration_testing_32_chars_minimum")
    os.environ.setdefault("OPENAI_API_KEY", "test_key_for_integration_testing")
    os.environ.setdefault("YOUTUBE_API_KEY", "test_key_for_integration_testing")

@pytest.fixture
async def test_db():
    """Create test database session factory."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    TestSessionLocal = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async def override_get_db_session():
        async with TestSessionLocal() as session:
            try:
                yield session
            finally:
                await session.close()
    
    app.dependency_overrides[get_db_session] = override_get_db_session
    
    try:
        yield TestSessionLocal
    finally:
        app.dependency_overrides.clear()
        await engine.dispose()

@pytest.fixture
def test_videos():
    """Return a list of test videos for integration testing."""
    return [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",  # Short video (3min)
        "https://youtu.be/EYM4TBfCGiU",  # Medium video (15min)
        "https://youtu.be/TYeUQFKhMsk",  # Long video (45min)
        "https://www.youtube.com/watch?v=jNQXAC9IVRw"   # Comments-heavy video
    ]

@pytest.fixture
def mock_youtube_extractor():
    """Mock YouTube extractor for testing."""
    with patch('app.services.youtube_extractor.YouTubeExtractor') as mock:
        instance = mock.return_value
        instance.extract_video_id.return_value = 'dQw4w9WgXcQ'
        instance.get_video_info = AsyncMock(return_value=Mock(**get_sample_video_info()))
        instance.download_audio = AsyncMock(return_value='/tmp/test_audio.wav')
        instance.get_comments = AsyncMock(return_value=[Mock(**comment) for comment in get_sample_comments_data()])
        instance.cleanup_audio_file = AsyncMock()
        yield instance

@pytest.fixture
def mock_transcription_service():
    """Mock transcription service for testing."""
    with patch('app.services.transcription_service.TranscriptionService') as mock:
        instance = mock.return_value
        instance.validate_audio_file.return_value = True
        instance.detect_language = AsyncMock(return_value={'language': 'en', 'confidence': 0.98})
        instance.transcribe_audio = AsyncMock(return_value=Mock(**get_sample_transcription_result()))
        yield instance

@pytest.fixture
def mock_content_analyzer():
    """Mock content analyzer for testing."""
    with patch('app.services.content_analyzer.content_analyzer') as mock:
        mock.analyze = AsyncMock(return_value=Mock(**get_sample_content_analysis_result()))
        yield mock

@pytest.fixture
def mock_comment_analyzer():
    """Mock comment analyzer for testing."""
    with patch('app.services.comment_analyzer.CommentAnalyzer') as mock:
        instance = mock.return_value
        instance.analyze_comments = AsyncMock(return_value=Mock(**get_sample_comment_analysis_result()))
        yield instance

@pytest.fixture
def mock_websocket_manager():
    """Mock WebSocket manager for testing."""
    with patch('app.api.v1.websocket.send_progress_update') as mock_progress, \
         patch('app.api.v1.websocket.send_task_completed') as mock_completed, \
         patch('app.api.v1.websocket.send_task_failed') as mock_failed:
        yield {
            'progress': mock_progress,
            'completed': mock_completed,
            'failed': mock_failed
        }

@pytest.fixture
def use_real_apis():
    """Fixture to determine if real APIs should be used."""
    return os.getenv('USE_REAL_APIS', 'false').lower() == 'true'

@pytest.fixture
def sample_task_id():
    """Sample task ID for testing."""
    return 'test-task-12345'
