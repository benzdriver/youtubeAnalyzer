"""
Content analysis data fixtures for Phase 2 integration tests
"""
from typing import Dict, List, Any

def get_sample_key_points() -> List[Dict[str, Any]]:
    """Sample key points fixture"""
    return [
        {
            'text': 'Classic 80s pop song with memorable lyrics',
            'importance': 0.9,
            'timestamp_start': 0.0,
            'timestamp_end': 30.0,
            'category': 'music_style'
        },
        {
            'text': 'Iconic music video that became internet meme',
            'importance': 0.85,
            'timestamp_start': 30.0,
            'timestamp_end': 60.0,
            'category': 'cultural_impact'
        }
    ]

def get_sample_topic_analysis() -> Dict[str, Any]:
    """Sample topic analysis fixture"""
    return {
        'main_topic': 'Music Video',
        'sub_topics': ['Pop Music', '80s Music', 'Internet Culture'],
        'keywords': ['love', 'commitment', 'classic', 'pop'],
        'content_type': 'entertainment',
        'confidence': 0.92
    }

def get_sample_sentiment_analysis() -> Dict[str, Any]:
    """Sample sentiment analysis fixture"""
    return {
        'overall_sentiment': 'positive',
        'sentiment_score': 0.7,
        'emotional_tone': ['nostalgic', 'upbeat', 'romantic'],
        'sentiment_progression': [
            {'timestamp': 0, 'sentiment': 'positive', 'score': 0.6},
            {'timestamp': 60, 'sentiment': 'positive', 'score': 0.8},
            {'timestamp': 120, 'sentiment': 'positive', 'score': 0.7}
        ]
    }

def get_sample_content_structure() -> Dict[str, Any]:
    """Sample content structure fixture"""
    return {
        'introduction_end': 15.0,
        'main_content_segments': [
            {'start': 15, 'end': 180, 'topic': 'Main song performance'},
            {'start': 180, 'end': 212, 'topic': 'Outro and credits'}
        ],
        'conclusion_start': 180.0,
        'call_to_action': 'Subscribe for more classic music videos'
    }

def get_sample_content_analysis_result() -> Dict[str, Any]:
    """Complete sample content analysis result"""
    return {
        'key_points': get_sample_key_points(),
        'topic_analysis': get_sample_topic_analysis(),
        'sentiment_analysis': get_sample_sentiment_analysis(),
        'content_structure': get_sample_content_structure(),
        'summary': 'Classic 1980s pop song by Rick Astley featuring memorable lyrics about love and commitment, became an internet phenomenon.',
        'recommendations': [
            'Great example of 80s pop music production',
            'Study the cultural impact of internet memes',
            'Analyze the song structure and lyrical themes'
        ],
        'quality_score': 0.88
    }
