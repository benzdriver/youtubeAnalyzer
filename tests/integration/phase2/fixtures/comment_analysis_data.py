"""
Comment analysis data fixtures for Phase 2 integration tests
"""
from typing import Dict, List, Any

def get_sample_sentiment_distribution() -> Dict[str, float]:
    """Sample sentiment distribution fixture"""
    return {
        'positive': 0.65,
        'neutral': 0.25,
        'negative': 0.10
    }

def get_sample_main_themes() -> List[Dict[str, Any]]:
    """Sample main themes fixture"""
    return [
        {
            'theme': 'Nostalgia and Classic Music',
            'keywords': ['classic', 'nostalgia', 'memories', 'old'],
            'comment_count': 45,
            'sentiment_distribution': {'positive': 0.8, 'neutral': 0.15, 'negative': 0.05}
        },
        {
            'theme': 'Internet Memes and Rickrolling',
            'keywords': ['rickroll', 'meme', 'internet', 'joke'],
            'comment_count': 38,
            'sentiment_distribution': {'positive': 0.7, 'neutral': 0.25, 'negative': 0.05}
        }
    ]

def get_sample_author_engagement() -> Dict[str, Any]:
    """Sample author engagement fixture"""
    return {
        'total_replies': 5,
        'reply_rate': 0.15,
        'avg_response_time': 24.5,
        'sentiment_in_replies': {'positive': 0.9, 'neutral': 0.1, 'negative': 0.0},
        'engagement_quality': 'high'
    }

def get_sample_top_comments() -> List[Dict[str, Any]]:
    """Sample top comments fixture"""
    return [
        {
            'text': 'This song never gets old! Classic Rick Astley!',
            'author': 'MusicLover123',
            'like_count': 1250,
            'sentiment': 'positive',
            'engagement_score': 0.92
        },
        {
            'text': 'Thanks for all the love on this video! ❤️',
            'author': 'Rick Astley',
            'like_count': 5000,
            'sentiment': 'positive',
            'engagement_score': 0.98,
            'is_author_reply': True
        }
    ]

def get_sample_spam_detection() -> Dict[str, Any]:
    """Sample spam detection fixture"""
    return {
        'spam_count': 2,
        'spam_percentage': 0.02,
        'common_spam_patterns': ['bot comments', 'promotional links']
    }

def get_sample_engagement_metrics() -> Dict[str, Any]:
    """Sample engagement metrics fixture"""
    return {
        'total_comments': 100,
        'avg_comment_length': 45.2,
        'reply_chains': 12,
        'author_interaction_rate': 0.15,
        'engagement_score': 0.78
    }

def get_sample_comment_analysis_result() -> Dict[str, Any]:
    """Complete sample comment analysis result"""
    return {
        'total_comments': 100,
        'sentiment_distribution': get_sample_sentiment_distribution(),
        'main_themes': get_sample_main_themes(),
        'author_engagement': get_sample_author_engagement(),
        'top_comments': get_sample_top_comments(),
        'spam_detection': get_sample_spam_detection(),
        'engagement_metrics': get_sample_engagement_metrics(),
        'recommendations': [
            'Continue engaging with positive fan comments',
            'Consider creating more content similar to this classic style',
            'Monitor for spam and inappropriate content'
        ]
    }
