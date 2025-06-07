"""
Transcription data fixtures for Phase 2 integration tests
"""
from typing import Dict, List, Any

def get_sample_transcript_segments() -> List[Dict[str, Any]]:
    """Sample transcript segments fixture"""
    return [
        {
            'start': 0.0,
            'end': 3.5,
            'text': "We're no strangers to love",
            'confidence': 0.95
        },
        {
            'start': 3.5,
            'end': 6.8,
            'text': "You know the rules and so do I",
            'confidence': 0.93
        },
        {
            'start': 6.8,
            'end': 10.2,
            'text': "A full commitment's what I'm thinking of",
            'confidence': 0.91
        },
        {
            'start': 10.2,
            'end': 14.1,
            'text': "You wouldn't get this from any other guy",
            'confidence': 0.94
        }
    ]

def get_sample_transcription_result() -> Dict[str, Any]:
    """Complete sample transcription result"""
    segments = get_sample_transcript_segments()
    full_text = " ".join([seg['text'] for seg in segments])
    
    return {
        'language': 'en',
        'language_confidence': 0.98,
        'duration': 212.0,
        'word_count': len(full_text.split()),
        'full_text': full_text,
        'segments': segments
    }

def get_sample_whisper_response() -> Dict[str, Any]:
    """Sample Whisper API response format"""
    return {
        'text': "We're no strangers to love You know the rules and so do I",
        'segments': get_sample_transcript_segments(),
        'language': 'en'
    }
