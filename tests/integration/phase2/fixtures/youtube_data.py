"""
YouTube data fixtures for Phase 2 integration tests
"""
from typing import Dict, List, Any
from datetime import datetime

def get_sample_video_info() -> Dict[str, Any]:
    """Sample video information fixture"""
    return {
        'id': 'dQw4w9WgXcQ',
        'title': 'Rick Astley - Never Gonna Give You Up (Official Video)',
        'description': 'The official video for "Never Gonna Give You Up" by Rick Astley',
        'duration': 212,
        'view_count': 1400000000,
        'like_count': 15000000,
        'channel_id': 'UCuAXFkgsw1L7xaCfnd5JJOw',
        'channel_title': 'Rick Astley',
        'upload_date': '2009-10-25',
        'thumbnail_url': 'https://i.ytimg.com/vi/dQw4w9WgXcQ/maxresdefault.jpg',
        'language': 'en'
    }

def get_sample_comments_data() -> List[Dict[str, Any]]:
    """Sample comments data fixture"""
    return [
        {
            'id': 'comment_1',
            'text': 'This song never gets old! Classic Rick Astley!',
            'author': 'MusicLover123',
            'author_channel_id': 'UC123456789',
            'like_count': 1250,
            'reply_count': 15,
            'published_at': '2024-01-15T10:30:00Z',
            'is_author_reply': False,
            'parent_id': None
        },
        {
            'id': 'comment_2',
            'text': 'Got rickrolled again! 😂',
            'author': 'InternetUser456',
            'author_channel_id': 'UC987654321',
            'like_count': 890,
            'reply_count': 8,
            'published_at': '2024-01-14T15:45:00Z',
            'is_author_reply': False,
            'parent_id': None
        },
        {
            'id': 'comment_3',
            'text': 'Thanks for all the love on this video! ❤️',
            'author': 'Rick Astley',
            'author_channel_id': 'UCuAXFkgsw1L7xaCfnd5JJOw',
            'like_count': 5000,
            'reply_count': 200,
            'published_at': '2024-01-16T09:15:00Z',
            'is_author_reply': True,
            'parent_id': None
        }
    ]

def get_sample_audio_file_path() -> str:
    """Sample audio file path for testing"""
    return '/tmp/test_audio_dQw4w9WgXcQ.wav'

def get_sample_extraction_result() -> Dict[str, Any]:
    """Complete sample extraction result"""
    return {
        'video_info': get_sample_video_info(),
        'comments': get_sample_comments_data(),
        'audio_file_path': get_sample_audio_file_path(),
        'extraction_timestamp': datetime.utcnow().isoformat()
    }
