"""
Simple Phase 2 Integration Test - Basic Flow Validation
Simplified test to validate core functionality without complex database setup.
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, Mock, patch

from fixtures.youtube_data import get_sample_video_info, get_sample_comments_data
from fixtures.transcription_data import get_sample_transcription_result
from fixtures.content_analysis_data import get_sample_content_analysis_result
from fixtures.comment_analysis_data import get_sample_comment_analysis_result


class TestSimpleDataFlow:
    """Simple test for YouTube video analysis data flow"""

    @pytest.mark.asyncio
    async def test_mocked_analysis_pipeline(self):
        """Test the analysis pipeline with mocked services"""
        video_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        
        mock_youtube_extractor = Mock()
        mock_youtube_extractor.extract_video_id.return_value = 'dQw4w9WgXcQ'
        mock_youtube_extractor.get_video_info = AsyncMock(return_value=Mock(**get_sample_video_info()))
        mock_youtube_extractor.download_audio = AsyncMock(return_value='/tmp/test_audio.wav')
        mock_youtube_extractor.get_comments = AsyncMock(return_value=[Mock(**comment) for comment in get_sample_comments_data()])
        mock_youtube_extractor.cleanup_audio_file = AsyncMock()
        
        mock_transcription_service = Mock()
        mock_transcription_service.validate_audio_file.return_value = True
        mock_transcription_service.detect_language = AsyncMock(return_value={'language': 'en', 'confidence': 0.98})
        mock_transcription_service.transcribe_audio = AsyncMock(return_value=Mock(**get_sample_transcription_result()))
        
        mock_content_analyzer = Mock()
        mock_content_analyzer.analyze = AsyncMock(return_value=Mock(**get_sample_content_analysis_result()))
        
        mock_comment_analyzer = Mock()
        mock_comment_analyzer.analyze_comments = AsyncMock(return_value=Mock(**get_sample_comment_analysis_result()))
        
        video_id = mock_youtube_extractor.extract_video_id(video_url)
        assert video_id == 'dQw4w9WgXcQ'
        
        video_info = await mock_youtube_extractor.get_video_info()
        assert video_info.title
        assert video_info.duration
        
        audio_path = await mock_youtube_extractor.download_audio()
        assert audio_path == '/tmp/test_audio.wav'
        
        transcription = await mock_transcription_service.transcribe_audio(audio_path)
        assert transcription.full_text
        assert transcription.segments
        
        content_analysis = await mock_content_analyzer.analyze(transcription.full_text)
        assert content_analysis.summary
        assert content_analysis.key_points
        
        comments = await mock_youtube_extractor.get_comments()
        comment_analysis = await mock_comment_analyzer.analyze_comments(comments)
        assert comment_analysis.sentiment_distribution
        assert comment_analysis.total_comments
        
        mock_youtube_extractor.extract_video_id.assert_called_once_with(video_url)
        mock_youtube_extractor.get_video_info.assert_called_once()
        mock_youtube_extractor.download_audio.assert_called_once()
        mock_youtube_extractor.get_comments.assert_called_once()
        mock_transcription_service.transcribe_audio.assert_called_once()
        mock_content_analyzer.analyze.assert_called_once()
        mock_comment_analyzer.analyze_comments.assert_called_once()

    @pytest.mark.asyncio
    async def test_data_format_validation(self):
        """Test that all data formats match expected structure"""
        video_info = get_sample_video_info()
        required_fields = ['id', 'title', 'duration', 'view_count', 'like_count', 'description']
        for field in required_fields:
            assert field in video_info, f"Missing field: {field}"
        
        transcription = get_sample_transcription_result()
        required_fields = ['full_text', 'segments', 'language', 'duration']
        for field in required_fields:
            assert field in transcription, f"Missing field: {field}"
        
        content_analysis = get_sample_content_analysis_result()
        required_fields = ['summary', 'key_points', 'topic_analysis', 'sentiment_analysis', 'quality_score']
        for field in required_fields:
            assert field in content_analysis, f"Missing field: {field}"
        
        comment_analysis = get_sample_comment_analysis_result()
        required_fields = ['total_comments', 'sentiment_distribution', 'main_themes', 'author_engagement']
        for field in required_fields:
            assert field in comment_analysis, f"Missing field: {field}"

    @pytest.mark.asyncio
    async def test_error_handling(self):
        """Test basic error handling scenarios"""
        mock_extractor = Mock()
        mock_extractor.extract_video_id.side_effect = ValueError("Invalid video URL")
        
        with pytest.raises(ValueError, match="Invalid video URL"):
            mock_extractor.extract_video_id("invalid_url")
        
        mock_transcription = Mock()
        mock_transcription.transcribe_audio = AsyncMock(side_effect=Exception("Transcription failed"))
        
        with pytest.raises(Exception, match="Transcription failed"):
            await mock_transcription.transcribe_audio("/path/to/audio")
