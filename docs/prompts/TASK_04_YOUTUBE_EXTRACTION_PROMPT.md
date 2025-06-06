# Task 4: YouTube数据提取 - Sub-Session Prompt

## 必读文档

**重要提示**: 开始此任务前，你必须阅读并理解以下文档：

### 核心协调文档
- `docs/TASK_COORDINATION.md` - 整体任务依赖关系和项目结构
- `docs/ARCHITECTURE_OVERVIEW.md` - 系统架构和技术栈
- `docs/CODING_STANDARDS.md` - 代码格式、命名规范和最佳实践
- `docs/API_SPECIFICATIONS.md` - 完整API接口定义

### 任务专用文档
- `docs/tasks/TASK_04_YOUTUBE_EXTRACTION.md` - 详细任务要求和验收标准
- `docs/contracts/youtube_data_contract.md` - YouTube数据提取接口规范

### 参考文档
- `docs/DEVELOPMENT_SETUP.md` - 开发环境配置
- `docs/PROGRESS_TRACKER.md` - 进度跟踪和任务状态更新

### 依赖关系
- Task 1 (项目配置) 必须先完成
- Task 2 (后端API) 必须先完成
- 查看 `docs/contracts/project_config_contract.md` 了解配置接口
- 查看 `docs/contracts/api_framework_contract.md` 了解API接口

## 项目背景

你正在为YouTube视频分析工具构建数据提取服务。这个服务需要：
- 从YouTube URL提取视频元数据
- 下载音频文件用于转录
- 获取视频评论数据
- 特别关注作者回复的识别和提取

## 任务目标

实现完整的YouTube数据提取服务，包括视频信息获取、音频文件下载、评论数据抓取和数据验证处理。

## 具体要求

### 1. YouTube提取器核心实现

```python
# backend/app/services/youtube_extractor.py
import yt_dlp
import os
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from app.core.config import settings
from app.utils.exceptions import ExternalServiceError, ValidationError

@dataclass
class VideoInfo:
    id: str
    title: str
    description: str
    duration: int  # seconds
    view_count: int
    like_count: int
    channel_id: str
    channel_title: str
    upload_date: str
    thumbnail_url: str
    language: Optional[str] = None

@dataclass
class CommentData:
    id: str
    text: str
    author: str
    author_channel_id: str
    like_count: int
    reply_count: int
    published_at: str
    is_author_reply: bool = False
    parent_id: Optional[str] = None

class YouTubeExtractor:
    """YouTube数据提取器"""
    
    def __init__(self):
        self.youtube_api = build('youtube', 'v3', developerKey=settings.youtube_api_key)
        self.ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': os.path.join(settings.storage_path, 'audio', '%(id)s.%(ext)s'),
            'extractaudio': True,
            'audioformat': 'wav',
            'audioquality': '192K',
            'no_warnings': True,
            'quiet': True
        }
    
    def extract_video_id(self, url: str) -> str:
        """从YouTube URL提取视频ID"""
        import re
        
        patterns = [
            r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([^&\n?#]+)',
            r'youtube\.com/watch\?.*v=([^&\n?#]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        raise ValidationError(f"无法从URL提取视频ID: {url}")
    
    async def get_video_info(self, video_id: str) -> VideoInfo:
        """获取视频基本信息"""
        try:
            request = self.youtube_api.videos().list(
                part='snippet,statistics,contentDetails',
                id=video_id
            )
            response = request.execute()
            
            if not response['items']:
                raise ValidationError(f"视频不存在或无法访问: {video_id}")
            
            item = response['items'][0]
            snippet = item['snippet']
            statistics = item['statistics']
            content_details = item['contentDetails']
            
            # 解析时长
            duration = self._parse_duration(content_details['duration'])
            
            return VideoInfo(
                id=video_id,
                title=snippet['title'],
                description=snippet['description'],
                duration=duration,
                view_count=int(statistics.get('viewCount', 0)),
                like_count=int(statistics.get('likeCount', 0)),
                channel_id=snippet['channelId'],
                channel_title=snippet['channelTitle'],
                upload_date=snippet['publishedAt'],
                thumbnail_url=snippet['thumbnails']['high']['url'],
                language=snippet.get('defaultLanguage')
            )
            
        except HttpError as e:
            logging.error(f"YouTube API error: {e}")
            raise ExternalServiceError(f"YouTube API调用失败: {e}")
        except Exception as e:
            logging.error(f"Video info extraction failed: {e}")
            raise ExternalServiceError(f"视频信息获取失败: {e}")
    
    async def download_audio(self, video_id: str) -> str:
        """下载视频音频"""
        try:
            url = f"https://youtube.com/watch?v={video_id}"
            
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                # 获取视频信息
                info = ydl.extract_info(url, download=False)
                
                # 检查视频可用性
                if info.get('is_live'):
                    raise ValidationError("不支持直播视频")
                
                if info.get('duration', 0) > 3600:  # 1小时限制
                    raise ValidationError("视频时长超过1小时限制")
                
                # 下载音频
                ydl.download([url])
                
                # 查找下载的文件
                audio_file = self._find_audio_file(video_id)
                if not audio_file:
                    raise ExternalServiceError("音频文件下载失败")
                
                logging.info(f"Audio downloaded: {audio_file}")
                return audio_file
                
        except yt_dlp.DownloadError as e:
            logging.error(f"yt-dlp download error: {e}")
            raise ExternalServiceError(f"音频下载失败: {e}")
        except Exception as e:
            logging.error(f"Audio download failed: {e}")
            raise ExternalServiceError(f"音频下载失败: {e}")
    
    async def get_comments(self, video_id: str, max_comments: int = 1000) -> List[CommentData]:
        """获取视频评论"""
        try:
            comments = []
            next_page_token = None
            
            # 获取视频作者的频道ID
            video_info = await self.get_video_info(video_id)
            author_channel_id = video_info.channel_id
            
            while len(comments) < max_comments:
                request = self.youtube_api.commentThreads().list(
                    part='snippet,replies',
                    videoId=video_id,
                    maxResults=min(100, max_comments - len(comments)),
                    order='relevance',
                    pageToken=next_page_token
                )
                
                response = request.execute()
                
                for item in response['items']:
                    # 主评论
                    top_comment = item['snippet']['topLevelComment']['snippet']
                    
                    comment = CommentData(
                        id=item['snippet']['topLevelComment']['id'],
                        text=top_comment['textDisplay'],
                        author=top_comment['authorDisplayName'],
                        author_channel_id=top_comment.get('authorChannelId', {}).get('value', ''),
                        like_count=top_comment['likeCount'],
                        reply_count=item['snippet']['totalReplyCount'],
                        published_at=top_comment['publishedAt'],
                        is_author_reply=top_comment.get('authorChannelId', {}).get('value') == author_channel_id
                    )
                    comments.append(comment)
                    
                    # 回复评论
                    if 'replies' in item:
                        for reply_item in item['replies']['comments']:
                            reply_snippet = reply_item['snippet']
                            
                            reply_comment = CommentData(
                                id=reply_item['id'],
                                text=reply_snippet['textDisplay'],
                                author=reply_snippet['authorDisplayName'],
                                author_channel_id=reply_snippet.get('authorChannelId', {}).get('value', ''),
                                like_count=reply_snippet['likeCount'],
                                reply_count=0,
                                published_at=reply_snippet['publishedAt'],
                                is_author_reply=reply_snippet.get('authorChannelId', {}).get('value') == author_channel_id,
                                parent_id=comment.id
                            )
                            comments.append(reply_comment)
                
                next_page_token = response.get('nextPageToken')
                if not next_page_token:
                    break
            
            logging.info(f"Extracted {len(comments)} comments for video {video_id}")
            
            # 按作者回复优先排序
            comments.sort(key=lambda x: (not x.is_author_reply, -x.like_count))
            
            return comments[:max_comments]
            
        except HttpError as e:
            logging.error(f"YouTube API error getting comments: {e}")
            if e.resp.status == 403:
                logging.warning("Comments disabled for this video")
                return []
            raise ExternalServiceError(f"评论获取失败: {e}")
        except Exception as e:
            logging.error(f"Comments extraction failed: {e}")
            raise ExternalServiceError(f"评论获取失败: {e}")
    
    def _parse_duration(self, duration_str: str) -> int:
        """解析ISO 8601时长格式"""
        import re
        
        pattern = r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?'
        match = re.match(pattern, duration_str)
        
        if not match:
            return 0
        
        hours = int(match.group(1) or 0)
        minutes = int(match.group(2) or 0)
        seconds = int(match.group(3) or 0)
        
        return hours * 3600 + minutes * 60 + seconds
    
    def _find_audio_file(self, video_id: str) -> Optional[str]:
        """查找下载的音频文件"""
        audio_dir = os.path.join(settings.storage_path, 'audio')
        
        for ext in ['wav', 'mp3', 'm4a', 'webm']:
            file_path = os.path.join(audio_dir, f"{video_id}.{ext}")
            if os.path.exists(file_path):
                return file_path
        
        return None
    
    def cleanup_audio_file(self, file_path: str):
        """清理音频文件"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logging.info(f"Cleaned up audio file: {file_path}")
        except Exception as e:
            logging.error(f"Failed to cleanup audio file {file_path}: {e}")

# 全局实例
youtube_extractor = YouTubeExtractor()
```

### 2. Celery任务集成

```python
# backend/app/tasks/extraction.py
from celery import current_task
from app.core.celery_app import celery_app
from app.services.youtube_extractor import youtube_extractor
from app.api.v1.websocket import send_progress_update
from app.models.task import AnalysisTask, TaskStatus
from app.core.database import get_db_session
from sqlalchemy import update
import logging

@celery_app.task(bind=True)
def extract_youtube_data(self, task_id: str, youtube_url: str, options: dict):
    """YouTube数据提取Celery任务"""
    
    async def _extract():
        try:
            # 更新任务状态
            async with get_db_session() as db:
                await db.execute(
                    update(AnalysisTask)
                    .where(AnalysisTask.id == task_id)
                    .values(
                        status=TaskStatus.PROCESSING,
                        current_step="开始数据提取"
                    )
                )
                await db.commit()
            
            await send_progress_update(task_id, 10, "解析YouTube URL")
            
            # 提取视频ID
            video_id = youtube_extractor.extract_video_id(youtube_url)
            
            await send_progress_update(task_id, 20, "获取视频信息")
            
            # 获取视频信息
            video_info = await youtube_extractor.get_video_info(video_id)
            
            await send_progress_update(task_id, 40, "下载音频文件")
            
            # 下载音频
            audio_file_path = await youtube_extractor.download_audio(video_id)
            
            await send_progress_update(task_id, 70, "获取评论数据")
            
            # 获取评论
            comments = await youtube_extractor.get_comments(
                video_id, 
                max_comments=options.get('max_comments', 1000)
            )
            
            await send_progress_update(task_id, 90, "保存提取结果")
            
            # 构建结果数据
            extraction_result = {
                'video_info': {
                    'id': video_info.id,
                    'title': video_info.title,
                    'description': video_info.description,
                    'duration': video_info.duration,
                    'view_count': video_info.view_count,
                    'like_count': video_info.like_count,
                    'channel_id': video_info.channel_id,
                    'channel_title': video_info.channel_title,
                    'upload_date': video_info.upload_date,
                    'thumbnail_url': video_info.thumbnail_url,
                    'language': video_info.language
                },
                'audio_file_path': audio_file_path,
                'comments': [
                    {
                        'id': comment.id,
                        'text': comment.text,
                        'author': comment.author,
                        'author_channel_id': comment.author_channel_id,
                        'like_count': comment.like_count,
                        'reply_count': comment.reply_count,
                        'published_at': comment.published_at,
                        'is_author_reply': comment.is_author_reply,
                        'parent_id': comment.parent_id
                    }
                    for comment in comments
                ]
            }
            
            # 保存到数据库
            async with get_db_session() as db:
                await db.execute(
                    update(AnalysisTask)
                    .where(AnalysisTask.id == task_id)
                    .values(result_data=extraction_result)
                )
                await db.commit()
            
            await send_progress_update(task_id, 100, "数据提取完成")
            
            return extraction_result
            
        except Exception as e:
            logging.error(f"YouTube extraction failed for task {task_id}: {e}")
            
            # 更新任务状态为失败
            async with get_db_session() as db:
                await db.execute(
                    update(AnalysisTask)
                    .where(AnalysisTask.id == task_id)
                    .values(
                        status=TaskStatus.FAILED,
                        error_message=f"数据提取失败: {str(e)}"
                    )
                )
                await db.commit()
            
            raise
    
    import asyncio
    return asyncio.run(_extract())
```

## 验收标准

### 功能验收
- [ ] YouTube URL解析正确
- [ ] 视频信息获取完整
- [ ] 音频文件下载成功
- [ ] 评论数据提取准确
- [ ] 作者回复正确识别
- [ ] 错误处理机制完善

### 技术验收
- [ ] 数据提取时间 < 2分钟（标准视频）
- [ ] 音频文件质量满足转录需求
- [ ] 评论数据结构化存储
- [ ] API调用频率控制合理
- [ ] 文件存储管理规范

### 质量验收
- [ ] 单元测试覆盖率 ≥ 80%
- [ ] 多种URL格式测试通过
- [ ] 异常视频处理正确
- [ ] 大量评论处理稳定
- [ ] 代码遵循项目规范

## 测试要求

### 单元测试
```python
# tests/test_youtube_extractor.py
import pytest
from unittest.mock import Mock, patch, AsyncMock
from app.services.youtube_extractor import YouTubeExtractor

@pytest.fixture
def extractor():
    return YouTubeExtractor()

def test_extract_video_id(extractor):
    """测试视频ID提取"""
    urls = [
        "https://youtube.com/watch?v=dQw4w9WgXcQ",
        "https://youtu.be/dQw4w9WgXcQ",
        "https://youtube.com/embed/dQw4w9WgXcQ"
    ]
    
    for url in urls:
        video_id = extractor.extract_video_id(url)
        assert video_id == "dQw4w9WgXcQ"

@pytest.mark.asyncio
async def test_get_video_info(extractor):
    """测试视频信息获取"""
    with patch.object(extractor.youtube_api.videos(), 'list') as mock_list:
        mock_request = Mock()
        mock_request.execute.return_value = {
            'items': [{
                'snippet': {
                    'title': 'Test Video',
                    'description': 'Test Description',
                    'channelId': 'test_channel',
                    'channelTitle': 'Test Channel',
                    'publishedAt': '2023-01-01T00:00:00Z',
                    'thumbnails': {'high': {'url': 'test_url'}}
                },
                'statistics': {
                    'viewCount': '1000',
                    'likeCount': '100'
                },
                'contentDetails': {
                    'duration': 'PT5M30S'
                }
            }]
        }
        mock_list.return_value = mock_request
        
        video_info = await extractor.get_video_info('test_id')
        
        assert video_info.title == 'Test Video'
        assert video_info.duration == 330  # 5分30秒
        assert video_info.view_count == 1000
```

## 交付物清单

- [ ] YouTube提取器核心类 (app/services/youtube_extractor.py)
- [ ] 数据模型定义 (VideoInfo, CommentData)
- [ ] Celery任务实现 (app/tasks/extraction.py)
- [ ] URL验证和解析功能
- [ ] 音频下载和管理功能
- [ ] 评论数据提取功能
- [ ] 作者回复识别逻辑
- [ ] 错误处理和日志记录
- [ ] 单元测试文件
- [ ] 配置文件更新

## 关键接口

完成此任务后，需要为后续任务提供：
- 结构化的视频信息数据
- 高质量的音频文件
- 完整的评论数据集
- 作者回复标识信息

## 预估时间

- 开发时间: 2-3天
- 测试时间: 1天
- API集成调试: 0.5天
- 文档时间: 0.5天
- 总计: 4-5天

## 注意事项

1. 确保遵循YouTube API使用条款
2. 实现合理的API调用频率限制
3. 处理各种异常情况（私有视频、删除视频等）
4. 音频文件要及时清理避免存储空间问题
5. 作者回复识别要准确可靠

这是整个分析流程的数据源，请确保数据提取的准确性和完整性。
