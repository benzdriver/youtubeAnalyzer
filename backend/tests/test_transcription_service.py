import os
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from app.services.transcription_service import (
    TranscriptionService,
    TranscriptResult,
    TranscriptSegment,
)
from app.utils.exceptions import ExternalServiceError, ValidationError


@pytest.fixture
def transcription_service():
    """Create a TranscriptionService instance for testing"""
    return TranscriptionService()


@pytest.fixture
def mock_whisper_result():
    """Mock Whisper transcription result"""
    return {
        "language": "en",
        "language_confidence": 0.95,
        "segments": [
            {"start": 0.0, "end": 5.0, "text": "Hello world", "avg_logprob": -0.5},
            {"start": 5.0, "end": 10.0, "text": "This is a test", "avg_logprob": -0.3},
        ],
    }


@pytest.mark.asyncio
async def test_transcribe_audio_success(transcription_service, mock_whisper_result):
    """Test successful audio transcription"""
    with patch.object(transcription_service, "_load_model"):
        transcription_service.model = Mock()
        transcription_service.model.transcribe.return_value = mock_whisper_result

        with patch("os.path.exists", return_value=True):
            with patch("asyncio.get_event_loop") as mock_loop:
                mock_executor = AsyncMock()
                mock_executor.return_value = mock_whisper_result
                mock_loop.return_value.run_in_executor = mock_executor

                result = await transcription_service.transcribe_audio("test.wav")

                assert isinstance(result, TranscriptResult)
                assert result.language == "en"
                assert result.language_confidence == 0.95
                assert result.full_text == "Hello world This is a test"
                assert len(result.segments) == 2
                assert result.word_count == 5
                assert result.duration == 10.0


@pytest.mark.asyncio
async def test_transcribe_audio_file_not_exists(transcription_service):
    """Test transcription with non-existent file"""
    with pytest.raises(ValidationError, match="音频文件不存在"):
        await transcription_service.transcribe_audio("nonexistent.wav")


@pytest.mark.asyncio
async def test_transcribe_audio_model_load_failure(transcription_service):
    """Test transcription with model loading failure"""
    with patch.object(
        transcription_service,
        "_load_model",
        side_effect=ExternalServiceError("Model load failed"),
    ):
        with patch("os.path.exists", return_value=True):
            with pytest.raises(ExternalServiceError, match="Model load failed"):
                await transcription_service.transcribe_audio("test.wav")


@pytest.mark.asyncio
async def test_detect_language_success(transcription_service):
    """Test successful language detection"""
    with patch.object(transcription_service, "_load_model"):
        transcription_service.model = Mock()
        transcription_service.model.device = "cpu"
        transcription_service.model.detect_language.return_value = (
            None,
            {"en": 0.9, "zh": 0.1},
        )

        with patch("os.path.exists", return_value=True):
            with patch("whisper.load_audio"):
                with patch("whisper.pad_or_trim"):
                    with patch("whisper.log_mel_spectrogram") as mock_mel:
                        mock_mel.return_value.to.return_value = Mock()

                        with patch("asyncio.get_event_loop") as mock_loop:
                            mock_executor = AsyncMock()
                            mock_executor.side_effect = [
                                Mock(),  # audio loading
                                (None, {"en": 0.9, "zh": 0.1}),  # language detection
                            ]
                            mock_loop.return_value.run_in_executor = mock_executor

                            result = await transcription_service.detect_language(
                                "test.wav"
                            )

                            assert result["language"] == "en"
                            assert result["confidence"] == 0.9
                            assert "all_probabilities" in result


@pytest.mark.asyncio
async def test_detect_language_file_not_exists(transcription_service):
    """Test language detection with non-existent file"""
    with pytest.raises(ValidationError, match="音频文件不存在"):
        await transcription_service.detect_language("nonexistent.wav")


def test_validate_audio_file_success(transcription_service):
    """Test successful audio file validation"""
    with patch("os.path.exists", return_value=True):
        with patch("os.path.getsize", return_value=1024):
            result = transcription_service.validate_audio_file("test.wav")
            assert result is True


def test_validate_audio_file_not_exists(transcription_service):
    """Test audio file validation with non-existent file"""
    with patch("os.path.exists", return_value=False):
        result = transcription_service.validate_audio_file("nonexistent.wav")
        assert result is False


def test_validate_audio_file_empty(transcription_service):
    """Test audio file validation with empty file"""
    with patch("os.path.exists", return_value=True):
        with patch("os.path.getsize", return_value=0):
            result = transcription_service.validate_audio_file("empty.wav")
            assert result is False


def test_validate_audio_file_too_large(transcription_service):
    """Test audio file validation with oversized file"""
    with patch("os.path.exists", return_value=True):
        with patch("os.path.getsize", return_value=999999999999):  # Very large file
            result = transcription_service.validate_audio_file("large.wav")
            assert result is False


def test_process_transcription_result(transcription_service, mock_whisper_result):
    """Test processing of Whisper transcription result"""
    result = transcription_service._process_transcription_result(mock_whisper_result)

    assert isinstance(result, TranscriptResult)
    assert result.language == "en"
    assert result.language_confidence == 0.95
    assert len(result.segments) == 2
    assert result.segments[0].start == 0.0
    assert result.segments[0].end == 5.0
    assert result.segments[0].text == "Hello world"
    assert result.segments[0].confidence == -0.5
    assert result.full_text == "Hello world This is a test"
    assert result.duration == 10.0
    assert result.word_count == 5


def test_process_transcription_result_empty(transcription_service):
    """Test processing of empty transcription result"""
    empty_result = {"language": "unknown", "segments": []}
    result = transcription_service._process_transcription_result(empty_result)

    assert isinstance(result, TranscriptResult)
    assert result.language == "unknown"
    assert len(result.segments) == 0
    assert result.full_text == ""
    assert result.duration == 0
    assert result.word_count == 0


def test_export_subtitle_srt(transcription_service):
    """Test SRT subtitle export"""
    transcript_result = TranscriptResult(
        language="en",
        language_confidence=0.95,
        segments=[
            TranscriptSegment(start=0.0, end=5.0, text="Hello world"),
            TranscriptSegment(start=5.0, end=10.0, text="This is a test"),
        ],
        full_text="Hello world This is a test",
        duration=10.0,
        word_count=5,
    )

    srt_content = transcription_service.export_subtitle_file(transcript_result, "srt")

    assert "1" in srt_content
    assert "00:00:00,000 --> 00:00:05,000" in srt_content
    assert "Hello world" in srt_content
    assert "2" in srt_content
    assert "00:00:05,000 --> 00:00:10,000" in srt_content
    assert "This is a test" in srt_content


def test_export_subtitle_vtt(transcription_service):
    """Test VTT subtitle export"""
    transcript_result = TranscriptResult(
        language="en",
        language_confidence=0.95,
        segments=[TranscriptSegment(start=0.0, end=5.0, text="Hello world")],
        full_text="Hello world",
        duration=5.0,
        word_count=2,
    )

    vtt_content = transcription_service.export_subtitle_file(transcript_result, "vtt")

    assert "WEBVTT" in vtt_content
    assert "00:00:00.000 --> 00:00:05.000" in vtt_content
    assert "Hello world" in vtt_content


def test_export_subtitle_invalid_format(transcription_service):
    """Test subtitle export with invalid format"""
    transcript_result = TranscriptResult(
        language="en",
        language_confidence=0.95,
        segments=[],
        full_text="",
        duration=0.0,
        word_count=0,
    )

    with pytest.raises(ValidationError, match="不支持的字幕格式"):
        transcription_service.export_subtitle_file(transcript_result, "invalid")


def test_format_timestamp(transcription_service):
    """Test timestamp formatting for SRT"""
    timestamp = transcription_service._format_timestamp(3661.5)  # 1:01:01.500
    assert timestamp == "01:01:01,500"


def test_format_timestamp_vtt(transcription_service):
    """Test timestamp formatting for VTT"""
    timestamp = transcription_service._format_timestamp_vtt(3661.5)  # 1:01:01.500
    assert timestamp == "01:01:01.500"


def test_load_model_success(transcription_service):
    """Test successful model loading"""
    with patch("whisper.load_model") as mock_load:
        mock_model = Mock()
        mock_load.return_value = mock_model

        transcription_service._load_model()

        assert transcription_service.model == mock_model
        mock_load.assert_called_once_with("base", device="cpu")


def test_load_model_failure(transcription_service):
    """Test model loading failure"""
    with patch("whisper.load_model", side_effect=Exception("Model load failed")):
        with pytest.raises(ExternalServiceError, match="转录模型加载失败"):
            transcription_service._load_model()


def test_load_model_only_once(transcription_service):
    """Test that model is loaded only once"""
    with patch("whisper.load_model") as mock_load:
        mock_model = Mock()
        mock_load.return_value = mock_model

        transcription_service._load_model()
        transcription_service._load_model()  # Second call

        mock_load.assert_called_once()  # Should only be called once
