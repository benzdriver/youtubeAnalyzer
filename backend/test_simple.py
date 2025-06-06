#!/usr/bin/env python3

import sys
import os
import re
sys.path.append('.')

def test_video_id_extraction():
    """Test video ID extraction using regex directly"""
    patterns = [
        r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([^&\n?#]+)',
        r'youtube\.com/watch\?.*v=([^&\n?#]+)'
    ]
    
    test_urls = [
        "https://youtube.com/watch?v=dQw4w9WgXcQ",
        "https://youtu.be/dQw4w9WgXcQ", 
        "https://youtube.com/embed/dQw4w9WgXcQ",
        "https://youtube.com/watch?v=dQw4w9WgXcQ&t=10s"
    ]
    
    print("Testing video ID extraction...")
    for url in test_urls:
        video_id = None
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                video_id = match.group(1)
                break
        
        if video_id == "dQw4w9WgXcQ":
            print(f"✓ {url} -> {video_id}")
        else:
            print(f"✗ {url} -> {video_id}")
            return False
    
    return True

def test_duration_parsing():
    """Test ISO 8601 duration parsing"""
    def parse_duration(duration_str):
        pattern = r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?'
        match = re.match(pattern, duration_str)
        
        if not match:
            return 0
        
        hours = int(match.group(1) or 0)
        minutes = int(match.group(2) or 0)
        seconds = int(match.group(3) or 0)
        
        return hours * 3600 + minutes * 60 + seconds
    
    test_cases = [
        ("PT5M30S", 330),  # 5 minutes 30 seconds
        ("PT1H2M3S", 3723),  # 1 hour 2 minutes 3 seconds
        ("PT45S", 45),  # 45 seconds
        ("PT10M", 600),  # 10 minutes
        ("PT2H", 7200),  # 2 hours
    ]
    
    print("\nTesting duration parsing...")
    for duration_str, expected_seconds in test_cases:
        result = parse_duration(duration_str)
        if result == expected_seconds:
            print(f"✓ {duration_str} -> {result}s")
        else:
            print(f"✗ {duration_str} -> {result}s (expected {expected_seconds})")
            return False
    
    return True

def test_invalid_urls():
    """Test handling of invalid URLs"""
    patterns = [
        r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([^&\n?#]+)',
        r'youtube\.com/watch\?.*v=([^&\n?#]+)'
    ]
    
    invalid_urls = [
        "https://example.com",
        "not_a_url",
        "https://youtube.com/watch",
        ""
    ]
    
    print("\nTesting invalid URL handling...")
    for url in invalid_urls:
        video_id = None
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                video_id = match.group(1)
                break
        
        if video_id is None:
            print(f"✓ {url} -> Correctly failed")
        else:
            print(f"✗ {url} -> Should have failed but got: {video_id}")
            return False
    
    return True

def main():
    """Run basic functionality tests"""
    print("=== YouTube Extractor Core Logic Tests ===\n")
    
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
        print("\n✓ All core logic tests passed!")
        print("Note: API-dependent tests require YouTube API key and proper environment setup")
    else:
        print("\n✗ Some tests failed!")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
