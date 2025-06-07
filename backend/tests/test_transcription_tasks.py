from unittest.mock import AsyncMock, Mock, patch

import pytest
from sqlalchemy import select

from app.models.task import AnalysisTask, TaskStatus
from app.services.transcription_service import TranscriptResult, TranscriptSegment
from app.tasks.transcription import transcribe_audio_task
from app.utils.exceptions import ExternalServiceError, ValidationError


@pytest.fixture
def mock_transcript_result():
    """Mock TranscriptResult for testing"""
    return TranscriptResult(
        language="en",
        language_confidence=0.95,
        segments=[
            TranscriptSegment(start=0.0, end=5.0, text="Hello world", confidence=-0.5),
            TranscriptSegment(
                start=5.0, end=10.0, text="This is a test", confidence=-0.3
            ),
        ],
        full_text="Hello world This is a test",
        duration=10.0,
        word_count=5,
    )


@pytest.fixture
def mock_db_session():
    """Mock database session"""
    session = AsyncMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.scalar_one = AsyncMock()
    session.scalar_one_or_none = AsyncMock()
    return session


@pytest.fixture
def mock_analysis_task():
    """Mock AnalysisTask"""
    task = Mock()
    task.id = "test-task-id"
    task.result_data = {}
    return task


@pytest.mark.asyncio
async def test_transcribe_audio_task_success(
    mock_transcript_result, mock_db_session, mock_analysis_task
):
    """Test successful audio transcription task"""

    mock_result = Mock()
    mock_result.scalar_one_or_none.return_value = mock_analysis_task
    mock_result.scalar_one.return_value = mock_analysis_task
    mock_db_session.execute.return_value = mock_result

    with patch("app.tasks.transcription.AsyncSessionLocal") as mock_session_local:
        mock_session_local.return_value.__aenter__.return_value = mock_db_session

        with patch(
            "app.tasks.transcription.TranscriptionService"
        ) as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service

            mock_service.validate_audio_file.return_value = True
            mock_service.detect_language = AsyncMock(
                return_value={"language": "en", "confidence": 0.95}
            )
            mock_service.transcribe_audio = AsyncMock(
                return_value=mock_transcript_result
            )

            with patch("app.tasks.transcription.send_progress_update") as mock_progress:
                result = await transcribe_audio_task(
                    "test-task-id", "/path/to/audio.wav"
                )

                mock_service.validate_audio_file.assert_called_once_with(
                    "/path/to/audio.wav"
                )
                mock_service.detect_language.assert_called_once_with(
                    "/path/to/audio.wav"
                )
                mock_service.transcribe_audio.assert_called_once_with(
                    "/path/to/audio.wav", language="en"
                )

                assert mock_progress.call_count >= 4

                assert result["language"] == "en"
                assert result["language_confidence"] == 0.95
                assert result["duration"] == 10.0
                assert result["word_count"] == 5
                assert result["full_text"] == "Hello world This is a test"
                assert len(result["segments"]) == 2


@pytest.mark.asyncio
async def test_transcribe_audio_task_with_provided_language(
    mock_transcript_result, mock_db_session, mock_analysis_task
):
    """Test transcription task with pre-specified language"""

    mock_result = Mock()
    mock_result.scalar_one_or_none.return_value = mock_analysis_task
    mock_result.scalar_one.return_value = mock_analysis_task
    mock_db_session.execute.return_value = mock_result

    with patch("app.tasks.transcription.AsyncSessionLocal") as mock_session_local:
        mock_session_local.return_value.__aenter__.return_value = mock_db_session

        with patch(
            "app.tasks.transcription.TranscriptionService"
        ) as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service

            mock_service.validate_audio_file.return_value = True
            mock_service.transcribe_audio = AsyncMock(
                return_value=mock_transcript_result
            )

            with patch("app.tasks.transcription.send_progress_update"):
                result = await transcribe_audio_task(
                    "test-task-id", "/path/to/audio.wav", language="zh"
                )

                assert (
                    not hasattr(mock_service, "detect_language")
                    or not mock_service.detect_language.called
                )
                mock_service.transcribe_audio.assert_called_once_with(
                    "/path/to/audio.wav", language="zh"
                )


@pytest.mark.asyncio
async def test_transcribe_audio_task_low_language_confidence(
    mock_transcript_result, mock_db_session, mock_analysis_task
):
    """Test transcription task with low language detection confidence"""

    mock_result = Mock()
    mock_result.scalar_one_or_none.return_value = mock_analysis_task
    mock_result.scalar_one.return_value = mock_analysis_task
    mock_db_session.execute.return_value = mock_result

    with patch("app.tasks.transcription.AsyncSessionLocal") as mock_session_local:
        mock_session_local.return_value.__aenter__.return_value = mock_db_session

        with patch(
            "app.tasks.transcription.TranscriptionService"
        ) as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service

            mock_service.validate_audio_file.return_value = True
            mock_service.detect_language = AsyncMock(
                return_value={
                    "language": "unknown",
                    "confidence": 0.3,  # Low confidence
                }
            )
            mock_service.transcribe_audio = AsyncMock(
                return_value=mock_transcript_result
            )

            with patch("app.tasks.transcription.send_progress_update"):
                result = await transcribe_audio_task(
                    "test-task-id", "/path/to/audio.wav"
                )

                mock_service.transcribe_audio.assert_called_once_with(
                    "/path/to/audio.wav", language=None
                )


@pytest.mark.asyncio
async def test_transcribe_audio_task_not_found():
    """Test transcription task with non-existent task"""

    mock_db_session = AsyncMock()
    mock_result = Mock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db_session.execute.return_value = mock_result

    with patch("app.tasks.transcription.AsyncSessionLocal") as mock_session_local:
        mock_session_local.return_value.__aenter__.return_value = mock_db_session

        with pytest.raises(ValidationError, match="Task not found"):
            await transcribe_audio_task("nonexistent-task-id", "/path/to/audio.wav")


@pytest.mark.asyncio
async def test_transcribe_audio_task_invalid_audio_file(
    mock_db_session, mock_analysis_task
):
    """Test transcription task with invalid audio file"""

    mock_result = Mock()
    mock_result.scalar_one_or_none.return_value = mock_analysis_task
    mock_db_session.execute.return_value = mock_result

    with patch("app.tasks.transcription.AsyncSessionLocal") as mock_session_local:
        mock_session_local.return_value.__aenter__.return_value = mock_db_session

        with patch(
            "app.tasks.transcription.TranscriptionService"
        ) as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service

            mock_service.validate_audio_file.return_value = False

            with patch("app.tasks.transcription.send_progress_update"):
                with pytest.raises(ValidationError, match="音频文件无效"):
                    await transcribe_audio_task("test-task-id", "/path/to/invalid.wav")


@pytest.mark.asyncio
async def test_transcribe_audio_task_transcription_failure(
    mock_db_session, mock_analysis_task
):
    """Test transcription task with transcription service failure"""

    mock_result = Mock()
    mock_result.scalar_one_or_none.return_value = mock_analysis_task
    mock_result.scalar_one.return_value = mock_analysis_task
    mock_db_session.execute.return_value = mock_result

    with patch("app.tasks.transcription.AsyncSessionLocal") as mock_session_local:
        mock_session_local.return_value.__aenter__.return_value = mock_db_session

        with patch(
            "app.tasks.transcription.TranscriptionService"
        ) as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service

            mock_service.validate_audio_file.return_value = True
            mock_service.detect_language = AsyncMock(
                return_value={"language": "en", "confidence": 0.95}
            )
            mock_service.transcribe_audio = AsyncMock(
                side_effect=ExternalServiceError("Transcription failed")
            )

            with patch("app.tasks.transcription.send_progress_update"):
                with pytest.raises(ExternalServiceError, match="Transcription failed"):
                    await transcribe_audio_task("test-task-id", "/path/to/audio.wav")

                mock_db_session.execute.assert_called()
                mock_db_session.commit.assert_called()


@pytest.mark.asyncio
async def test_transcribe_audio_task_database_update(
    mock_transcript_result, mock_db_session, mock_analysis_task
):
    """Test that transcription results are properly saved to database"""

    mock_result = Mock()
    mock_result.scalar_one_or_none.return_value = mock_analysis_task
    mock_result.scalar_one.return_value = mock_analysis_task
    mock_db_session.execute.return_value = mock_result

    with patch("app.tasks.transcription.AsyncSessionLocal") as mock_session_local:
        mock_session_local.return_value.__aenter__.return_value = mock_db_session

        with patch(
            "app.tasks.transcription.TranscriptionService"
        ) as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service

            mock_service.validate_audio_file.return_value = True
            mock_service.detect_language = AsyncMock(
                return_value={"language": "en", "confidence": 0.95}
            )
            mock_service.transcribe_audio = AsyncMock(
                return_value=mock_transcript_result
            )

            with patch("app.tasks.transcription.send_progress_update"):
                await transcribe_audio_task("test-task-id", "/path/to/audio.wav")

                assert (
                    mock_db_session.execute.call_count >= 2
                )  # At least select and update
                mock_db_session.commit.assert_called()


@pytest.mark.asyncio
async def test_transcribe_audio_task_progress_updates(
    mock_transcript_result, mock_db_session, mock_analysis_task
):
    """Test that progress updates are sent at appropriate stages"""

    mock_result = Mock()
    mock_result.scalar_one_or_none.return_value = mock_analysis_task
    mock_result.scalar_one.return_value = mock_analysis_task
    mock_db_session.execute.return_value = mock_result

    with patch("app.tasks.transcription.AsyncSessionLocal") as mock_session_local:
        mock_session_local.return_value.__aenter__.return_value = mock_db_session

        with patch(
            "app.tasks.transcription.TranscriptionService"
        ) as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service

            mock_service.validate_audio_file.return_value = True
            mock_service.detect_language = AsyncMock(
                return_value={"language": "en", "confidence": 0.95}
            )
            mock_service.transcribe_audio = AsyncMock(
                return_value=mock_transcript_result
            )

            with patch("app.tasks.transcription.send_progress_update") as mock_progress:
                await transcribe_audio_task("test-task-id", "/path/to/audio.wav")

                progress_calls = mock_progress.call_args_list
                assert len(progress_calls) >= 4

                progress_values = [
                    call[0][1] for call in progress_calls
                ]  # Second argument is progress
                assert 10 in progress_values  # Initialization
                assert 20 in progress_values  # Language detection
                assert 40 in progress_values  # Transcription start
                assert 80 in progress_values  # Result processing
                assert 100 in progress_values  # Completion
