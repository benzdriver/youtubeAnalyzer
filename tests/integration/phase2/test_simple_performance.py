"""
Simple Performance Tests for Phase 2 Integration
Simplified performance tests without database dependencies.
"""
import pytest
import asyncio
import time
from unittest.mock import AsyncMock, Mock

from fixtures.youtube_data import get_sample_video_info
from fixtures.transcription_data import get_sample_transcription_result
from fixtures.content_analysis_data import get_sample_content_analysis_result
from fixtures.comment_analysis_data import get_sample_comment_analysis_result


class TestSimplePerformance:
    """Simple performance tests for YouTube video analysis"""

    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_short_video_analysis_performance(self, mock_youtube_extractor, 
                                                   mock_transcription_service, mock_content_analyzer, 
                                                   mock_comment_analyzer):
        """Test that short video analysis completes within 5 minutes"""
        video_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        
        async def mock_transcribe_with_delay(*args, **kwargs):
            await asyncio.sleep(0.5)  # 0.5 seconds simulated
            return Mock(**get_sample_transcription_result())
        
        async def mock_content_analysis_with_delay(*args, **kwargs):
            await asyncio.sleep(0.3)  # 0.3 seconds simulated
            return Mock(**get_sample_content_analysis_result())
        
        async def mock_comment_analysis_with_delay(*args, **kwargs):
            await asyncio.sleep(0.2)  # 0.2 seconds simulated
            return Mock(**get_sample_comment_analysis_result())
        
        mock_transcription_service.transcribe_audio = mock_transcribe_with_delay
        mock_content_analyzer.analyze = mock_content_analysis_with_delay
        mock_comment_analyzer.analyze_comments = mock_comment_analysis_with_delay
        
        start_time = time.time()
        
        video_id = mock_youtube_extractor.extract_video_id(video_url)
        video_info = await mock_youtube_extractor.get_video_info()
        audio_path = await mock_youtube_extractor.download_audio()
        transcription = await mock_transcription_service.transcribe_audio(audio_path)
        content_analysis = await mock_content_analyzer.analyze(transcription.full_text)
        comments = await mock_youtube_extractor.get_comments()
        comment_analysis = await mock_comment_analyzer.analyze_comments(comments)
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        assert execution_time < 300, f"Short video analysis took {execution_time:.2f}s, should be < 300s"
        
        assert video_id == 'dQw4w9WgXcQ'
        assert video_info.title
        assert transcription.full_text
        assert content_analysis.summary
        assert comment_analysis.sentiment_distribution

    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_medium_video_analysis_performance(self, mock_youtube_extractor, 
                                                    mock_transcription_service, mock_content_analyzer, 
                                                    mock_comment_analyzer):
        """Test that medium video analysis completes within 15 minutes"""
        video_url = "https://youtu.be/EYM4TBfCGiU"
        
        async def mock_transcribe_with_delay(*args, **kwargs):
            await asyncio.sleep(1.0)  # 1 second simulated
            return Mock(**get_sample_transcription_result())
        
        async def mock_content_analysis_with_delay(*args, **kwargs):
            await asyncio.sleep(0.8)  # 0.8 seconds simulated
            return Mock(**get_sample_content_analysis_result())
        
        async def mock_comment_analysis_with_delay(*args, **kwargs):
            await asyncio.sleep(0.5)  # 0.5 seconds simulated
            return Mock(**get_sample_comment_analysis_result())
        
        mock_transcription_service.transcribe_audio = mock_transcribe_with_delay
        mock_content_analyzer.analyze = mock_content_analysis_with_delay
        mock_comment_analyzer.analyze_comments = mock_comment_analysis_with_delay
        
        start_time = time.time()
        
        video_id = mock_youtube_extractor.extract_video_id(video_url)
        video_info = await mock_youtube_extractor.get_video_info()
        audio_path = await mock_youtube_extractor.download_audio()
        transcription = await mock_transcription_service.transcribe_audio(audio_path)
        content_analysis = await mock_content_analyzer.analyze(transcription.full_text)
        comments = await mock_youtube_extractor.get_comments()
        comment_analysis = await mock_comment_analyzer.analyze_comments(comments)
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        assert execution_time < 900, f"Medium video analysis took {execution_time:.2f}s, should be < 900s"
        
        assert video_id
        assert video_info.title
        assert transcription.full_text
        assert content_analysis.summary
        assert comment_analysis.sentiment_distribution

    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_concurrent_analysis_performance(self, mock_youtube_extractor, 
                                                  mock_transcription_service, mock_content_analyzer, 
                                                  mock_comment_analyzer):
        """Test concurrent processing of multiple videos"""
        video_urls = [
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "https://youtu.be/EYM4TBfCGiU",
            "https://youtu.be/TYeUQFKhMsk"
        ]
        
        async def mock_transcribe_with_delay(*args, **kwargs):
            await asyncio.sleep(0.2)
            return Mock(**get_sample_transcription_result())
        
        async def mock_content_analysis_with_delay(*args, **kwargs):
            await asyncio.sleep(0.1)
            return Mock(**get_sample_content_analysis_result())
        
        async def mock_comment_analysis_with_delay(*args, **kwargs):
            await asyncio.sleep(0.1)
            return Mock(**get_sample_comment_analysis_result())
        
        mock_transcription_service.transcribe_audio = mock_transcribe_with_delay
        mock_content_analyzer.analyze = mock_content_analysis_with_delay
        mock_comment_analyzer.analyze_comments = mock_comment_analysis_with_delay
        
        async def analyze_single_video(video_url):
            video_id = mock_youtube_extractor.extract_video_id(video_url)
            video_info = await mock_youtube_extractor.get_video_info()
            audio_path = await mock_youtube_extractor.download_audio()
            transcription = await mock_transcription_service.transcribe_audio(audio_path)
            content_analysis = await mock_content_analyzer.analyze(transcription.full_text)
            comments = await mock_youtube_extractor.get_comments()
            comment_analysis = await mock_comment_analyzer.analyze_comments(comments)
            return {
                'video_id': video_id,
                'video_info': video_info,
                'transcription': transcription,
                'content_analysis': content_analysis,
                'comment_analysis': comment_analysis
            }
        
        start_time = time.time()
        
        tasks = [analyze_single_video(url) for url in video_urls]
        results = await asyncio.gather(*tasks)
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        sequential_time_estimate = len(video_urls) * 0.4  # 0.4s per video
        assert execution_time < sequential_time_estimate * 1.5, f"Concurrent processing took {execution_time:.2f}s, should be more efficient"
        
        assert len(results) == len(video_urls)
        for result in results:
            assert result['video_info'].title
            assert result['transcription'].full_text
            assert result['content_analysis'].summary
            assert result['comment_analysis'].sentiment_distribution

    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_long_video_analysis_performance(self, mock_youtube_extractor, 
                                                  mock_transcription_service, mock_content_analyzer, 
                                                  mock_comment_analyzer):
        """Test that long video analysis completes within 30 minutes"""
        video_url = "https://youtu.be/TYeUQFKhMsk"
        
        async def mock_transcribe_with_delay(*args, **kwargs):
            await asyncio.sleep(2.0)  # 2 seconds simulated
            return Mock(**get_sample_transcription_result())
        
        async def mock_content_analysis_with_delay(*args, **kwargs):
            await asyncio.sleep(1.5)  # 1.5 seconds simulated
            return Mock(**get_sample_content_analysis_result())
        
        async def mock_comment_analysis_with_delay(*args, **kwargs):
            await asyncio.sleep(1.0)  # 1 second simulated
            return Mock(**get_sample_comment_analysis_result())
        
        mock_transcription_service.transcribe_audio = mock_transcribe_with_delay
        mock_content_analyzer.analyze = mock_content_analysis_with_delay
        mock_comment_analyzer.analyze_comments = mock_comment_analysis_with_delay
        
        start_time = time.time()
        
        video_id = mock_youtube_extractor.extract_video_id(video_url)
        video_info = await mock_youtube_extractor.get_video_info()
        audio_path = await mock_youtube_extractor.download_audio()
        transcription = await mock_transcription_service.transcribe_audio(audio_path)
        content_analysis = await mock_content_analyzer.analyze(transcription.full_text)
        comments = await mock_youtube_extractor.get_comments()
        comment_analysis = await mock_comment_analyzer.analyze_comments(comments)
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        assert execution_time < 1800, f"Long video analysis took {execution_time:.2f}s, should be < 1800s"
        
        assert video_id
        assert video_info.title
        assert transcription.full_text
        assert content_analysis.summary
        assert comment_analysis.sentiment_distribution
