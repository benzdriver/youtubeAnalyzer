import pytest
from unittest.mock import Mock, patch, AsyncMock
import json
from typing import Dict, Any

from app.services.content_analyzer import (
    LLMContentAnalyzer, 
    ContentInsights, 
    KeyPoint, 
    TopicAnalysis, 
    SentimentAnalysis, 
    ContentStructure,
    ContentType,
    SentimentType
)
from app.utils.exceptions import ValidationError, ExternalServiceError


@pytest.fixture
def analyzer():
    """Create content analyzer instance for testing"""
    with patch('app.services.content_analyzer.settings') as mock_settings:
        mock_settings.openai_api_key = "test-api-key"
        mock_settings.openai_model = "gpt-4"
        return LLMContentAnalyzer()


@pytest.fixture
def sample_transcript_data():
    """Sample transcript data for testing"""
    return {
        'full_text': 'This is a test video about machine learning. We will cover neural networks and deep learning concepts.',
        'segments': [
            {'start': 0, 'end': 5, 'text': 'This is a test video about machine learning.', 'confidence': 0.95},
            {'start': 5, 'end': 10, 'text': 'We will cover neural networks and deep learning concepts.', 'confidence': 0.92}
        ]
    }


@pytest.fixture
def sample_video_info():
    """Sample video info for testing"""
    return {
        'id': 'test_video_id',
        'title': 'Machine Learning Tutorial',
        'description': 'Learn the basics of machine learning and neural networks',
        'duration': 600,
        'view_count': 10000,
        'like_count': 500,
        'channel_id': 'test_channel',
        'channel_title': 'Tech Education',
        'upload_date': '2024-01-01',
        'thumbnail_url': 'https://example.com/thumb.jpg',
        'language': 'en'
    }


@pytest.mark.asyncio
async def test_analyzer_initialization_with_api_key():
    """Test analyzer initialization with valid API key"""
    with patch('app.services.content_analyzer.settings') as mock_settings:
        mock_settings.openai_api_key = "test-api-key"
        analyzer = LLMContentAnalyzer()
        assert analyzer.model == "gpt-4"
        assert analyzer.max_retries == 3


@pytest.mark.asyncio
async def test_analyzer_initialization_without_api_key():
    """Test analyzer initialization fails without API key"""
    with patch('app.services.content_analyzer.settings') as mock_settings:
        mock_settings.openai_api_key = None
        with pytest.raises(ValidationError, match="OpenAI API key is required"):
            LLMContentAnalyzer()


@pytest.mark.asyncio
async def test_analyze_content_success(analyzer, sample_transcript_data, sample_video_info):
    """Test successful content analysis"""
    mock_responses = [
        '{"key_points": [{"text": "Machine learning basics", "importance": 0.9, "category": "concept"}]}',
        '{"main_topic": "Machine Learning", "sub_topics": ["Neural Networks"], "keywords": ["ML", "AI"], "content_type": "educational", "confidence": 0.85}',
        '{"overall_sentiment": "positive", "sentiment_score": 0.3, "emotional_tone": ["informative"], "sentiment_progression": []}',
        '{"introduction_end": 30.0, "main_content_segments": [], "conclusion_start": 570.0, "call_to_action": null}',
        'This video provides an introduction to machine learning concepts.',
        '{"recommendations": ["Practice with coding examples", "Read additional ML resources"]}'
    ]
    
    with patch.object(analyzer, '_make_api_call', side_effect=mock_responses):
        result = await analyzer.analyze(sample_transcript_data, sample_video_info)
        
        assert isinstance(result, ContentInsights)
        assert len(result.key_points) == 1
        assert result.key_points[0].text == "Machine learning basics"
        assert result.topic_analysis.main_topic == "Machine Learning"
        assert result.sentiment_analysis.overall_sentiment == SentimentType.POSITIVE
        assert result.summary == "This video provides an introduction to machine learning concepts."
        assert len(result.recommendations) == 2


@pytest.mark.asyncio
async def test_analyze_empty_transcript(analyzer, sample_video_info):
    """Test analysis with empty transcript"""
    empty_transcript = {'full_text': '', 'segments': []}
    
    with pytest.raises(ValidationError, match="Transcript text is empty"):
        await analyzer.analyze(empty_transcript, sample_video_info)


@pytest.mark.asyncio
async def test_extract_key_points(analyzer, sample_transcript_data):
    """Test key points extraction"""
    mock_response = '{"key_points": [{"text": "Neural networks", "importance": 0.8, "category": "concept"}]}'
    
    with patch.object(analyzer, '_make_api_call', return_value=mock_response):
        result = await analyzer._extract_key_points(
            sample_transcript_data['full_text'], 
            sample_transcript_data['segments']
        )
        
        assert len(result) == 1
        assert isinstance(result[0], KeyPoint)
        assert result[0].text == "Neural networks"
        assert result[0].importance == 0.8


@pytest.mark.asyncio
async def test_api_call_retry_logic(analyzer):
    """Test API call retry mechanism"""
    with patch.object(analyzer.client.chat.completions, 'create') as mock_create:
        mock_create.side_effect = [
            Exception("API Error 1"),
            Exception("API Error 2"),
            Mock(choices=[Mock(message=Mock(content="Success"))])
        ]
        
        result = await analyzer._make_api_call("test prompt")
        assert result == "Success"
        assert mock_create.call_count == 3


@pytest.mark.asyncio
async def test_calculate_quality_score(analyzer):
    """Test quality score calculation"""
    key_points = [KeyPoint("Test point", 0.8)]
    topic_analysis = TopicAnalysis("Test", [], [], ContentType.EDUCATIONAL, 0.9)
    sentiment_analysis = SentimentAnalysis(SentimentType.POSITIVE, 0.5, [], [])
    
    score = analyzer._calculate_quality_score(key_points, topic_analysis, sentiment_analysis, 1000)
    
    assert 0.0 <= score <= 1.0
    assert score > 0.5
