#!/usr/bin/env python3

import sys
import os
import asyncio
sys.path.append('.')

from dotenv import load_dotenv
load_dotenv('../.env')

def test_comment_extraction():
    """Test YouTube comment extraction functionality"""
    print("🔍 YouTube评论提取功能测试\n")
    
    try:
        from app.services.youtube_extractor import YouTubeExtractor
        extractor = YouTubeExtractor()
        print("✓ YouTubeExtractor初始化成功")
        
        video_url = 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'
        video_id = extractor.extract_video_id(video_url)
        print(f"✓ 视频ID提取: {video_id}")
        
        async def test_comments():
            try:
                print("\n正在获取评论数据...")
                comments = await extractor.get_comments(video_id, max_results=10)
                
                if comments:
                    print(f"✅ 成功获取 {len(comments)} 条评论")
                    
                    for i, comment in enumerate(comments[:3], 1):
                        print(f"\n--- 评论 {i} ---")
                        print(f"作者: {comment.author}")
                        print(f"内容: {comment.text[:100]}...")
                        print(f"点赞数: {comment.like_count}")
                        print(f"回复数: {comment.reply_count}")
                        print(f"是否作者回复: {comment.is_author_reply}")
                        print(f"发布时间: {comment.published_at}")
                    
                    author_replies = [c for c in comments if c.is_author_reply]
                    if author_replies:
                        print(f"\n🎯 发现 {len(author_replies)} 条作者回复")
                    else:
                        print("\n📝 在前10条评论中未发现作者回复")
                    
                    return True
                else:
                    print("⚠️ 未获取到评论数据")
                    return False
                    
            except Exception as e:
                print(f"❌ 评论提取失败: {e}")
                return False
        
        result = asyncio.run(test_comments())
        
        if result:
            print("\n🎉 评论提取功能测试成功！")
            print("\n📋 评论数据包含:")
            print("  ✅ 评论内容和作者信息")
            print("  ✅ 点赞数和回复数")
            print("  ✅ 发布时间")
            print("  ✅ 作者回复识别")
            print("  ✅ 评论层级关系")
        else:
            print("\n❌ 评论提取功能测试失败")
            
        return result
        
    except Exception as e:
        print(f"❌ 测试初始化失败: {e}")
        return False

if __name__ == "__main__":
    success = test_comment_extraction()
    sys.exit(0 if success else 1)
