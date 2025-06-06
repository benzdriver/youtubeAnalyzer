#!/usr/bin/env python3

import sys
import os
sys.path.append('.')

from app.services.youtube_extractor import YouTubeExtractor
from unittest.mock import patch

def test_video_id_extraction():
    """Test video ID extraction from various URL formats"""
    with patch('app.core.config.settings') as mock_settings:
        mock_settings.youtube_api_key = "test_key"
        mock_settings.storage_path = "/tmp"
        with patch('googleapiclient.discovery.build'):
            extractor = YouTubeExtractor()
    
    test_urls = [
        "https://youtube.com/watch?v=dQw4w9WgXcQ",
        "https://youtu.be/dQw4w9WgXcQ", 
        "https://youtube.com/embed/dQw4w9WgXcQ",
        "https://youtube.com/watch?v=dQw4w9WgXcQ&t=10s"
    ]
    
    print("Testing video ID extraction...")
    for url in test_urls:
        try:
            video_id = extractor.extract_video_id(url)
            print(f"✓ {url} -> {video_id}")
            assert video_id == "dQw4w9WgXcQ", f"Expected dQw4w9WgXcQ, got {video_id}"
        except Exception as e:
            print(f"✗ {url} -> Error: {e}")
            return False
    
    return True

def test_duration_parsing():
    """Test ISO 8601 duration parsing"""
    with patch('app.core.config.settings') as mock_settings:
        mock_settings.youtube_api_key = "test_key"
        mock_settings.storage_path = "/tmp"
        with patch('googleapiclient.discovery.build'):
            extractor = YouTubeExtractor()
    
    test_cases = [
        ("PT5M30S", 330),  # 5 minutes 30 seconds
        ("PT1H2M3S", 3723),  # 1 hour 2 minutes 3 seconds
        ("PT45S", 45),  # 45 seconds
        ("PT10M", 600),  # 10 minutes
        ("PT2H", 7200),  # 2 hours
    ]
    
    print("\nTesting duration parsing...")
    for duration_str, expected_seconds in test_cases:
        try:
            result = extractor._parse_duration(duration_str)
            print(f"✓ {duration_str} -> {result}s")
            assert result == expected_seconds, f"Expected {expected_seconds}, got {result}"
        except Exception as e:
            print(f"✗ {duration_str} -> Error: {e}")
            return False
    
    return True

def test_invalid_urls():
    """Test handling of invalid URLs"""
    with patch('app.core.config.settings') as mock_settings:
        mock_settings.youtube_api_key = "test_key"
        mock_settings.storage_path = "/tmp"
        with patch('googleapiclient.discovery.build'):
            extractor = YouTubeExtractor()
    
    invalid_urls = [
        "https://example.com",
        "not_a_url",
        "https://youtube.com/watch",
        ""
    ]
    
    print("\nTesting invalid URL handling...")
    for url in invalid_urls:
        try:
            video_id = extractor.extract_video_id(url)
            print(f"✗ {url} -> Should have failed but got: {video_id}")
            return False
        except Exception as e:
            print(f"✓ {url} -> Correctly failed: {type(e).__name__}")
    
    return True

def main():
    """Run basic functionality tests"""
    print("=== YouTube Extractor Basic Tests ===\n")
    
    try:
        tests = [
            test_video_id_extraction,
            test_duration_parsing, 
            test_invalid_urls
        ]
        
        all_passed = True
        for test in tests:
            if not test():
                all_passed = False
                break
        
        if all_passed:
            print("\n✓ All basic tests passed!")
            print("Note: API-dependent tests (video info, audio download, comments) require YouTube API key")
        else:
            print("\n✗ Some tests failed!")
            return 1
            
    except Exception as e:
        print(f"\n✗ Test setup failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
