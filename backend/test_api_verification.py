#!/usr/bin/env python3

import sys
import os
sys.path.append('.')

from dotenv import load_dotenv
load_dotenv('../.env')

def test_environment_setup():
    """Test if environment is properly configured"""
    print("=== Environment Configuration Test ===\n")
    
    env_path = '../.env'
    if os.path.exists(env_path):
        print("✓ .env file found")
    else:
        print("✗ .env file not found")
        return False
    
    youtube_key = os.environ.get('YOUTUBE_API_KEY')
    if youtube_key:
        print(f"✓ YouTube API key configured (length: {len(youtube_key)})")
        print(f"✓ Key starts with: {youtube_key[:10]}...")
    else:
        print("✗ YouTube API key not found in environment")
        return False
    
    return True

def test_youtube_extractor_initialization():
    """Test YouTubeExtractor initialization"""
    print("\n=== YouTubeExtractor Initialization Test ===\n")
    
    try:
        from app.services.youtube_extractor import YouTubeExtractor
        extractor = YouTubeExtractor()
        print("✓ YouTubeExtractor initialized successfully")
        return extractor
    except Exception as e:
        print(f"✗ YouTubeExtractor initialization failed: {e}")
        return None

def test_video_id_extraction(extractor):
    """Test video ID extraction"""
    print("\n=== Video ID Extraction Test ===\n")
    
    test_url = 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'
    try:
        video_id = extractor.extract_video_id(test_url)
        print(f"✓ Video ID extracted: {video_id}")
        return video_id
    except Exception as e:
        print(f"✗ Video ID extraction failed: {e}")
        return None

def test_youtube_api_connection(extractor, video_id):
    """Test YouTube API connection"""
    print("\n=== YouTube API Connection Test ===\n")
    
    import asyncio
    
    async def api_test():
        try:
            video_info = await extractor.get_video_info(video_id)
            print(f"✓ Video info retrieved successfully")
            print(f"  Title: {video_info.title[:50]}...")
            print(f"  Duration: {video_info.duration}s")
            print(f"  Views: {video_info.view_count:,}")
            print(f"  Channel: {video_info.channel_title}")
            return True
        except Exception as e:
            print(f"✗ YouTube API connection failed: {e}")
            return False
    
    return asyncio.run(api_test())

def main():
    """Run comprehensive API verification tests"""
    print("🔍 YouTube Data Extraction Service Verification\n")
    
    if not test_environment_setup():
        print("\n❌ Environment setup failed - cannot proceed with API tests")
        return 1
    
    extractor = test_youtube_extractor_initialization()
    if not extractor:
        print("\n❌ YouTubeExtractor initialization failed")
        return 1
    
    video_id = test_video_id_extraction(extractor)
    if not video_id:
        print("\n❌ Video ID extraction failed")
        return 1
    
    api_success = test_youtube_api_connection(extractor, video_id)
    if not api_success:
        print("\n❌ YouTube API connection failed")
        return 1
    
    print("\n🎉 All verification tests passed!")
    print("✅ YouTube data extraction service is working correctly!")
    return 0

if __name__ == "__main__":
    sys.exit(main())
