# Task 4: YouTube数据提取

## 任务概述

实现YouTube视频数据提取服务，包括视频元数据获取、音频文件提取、评论数据抓取和URL验证功能。这是整个分析流程的第一步，为后续的转录和分析服务提供原始数据。

## 目标

- 实现yt-dlp集成进行视频下载和元数据提取
- 集成YouTube Data API获取详细信息和评论
- 建立数据验证和标准化流程
- 实现错误处理和重试机制
- 优化大文件处理和存储管理

## 可交付成果

### 1. YouTube提取器服务

```python
# backend/app/services/youtube_extractor.py
import yt_dlp
import asyncio
import os
import re
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging
from googleapiclient.discovery import build

from app.core.config import settings
from app.utils.exceptions import ExternalServiceError, ValidationError
from app.models.schemas import VideoInfo, Comment, AudioFile

class YouTubeExtractor:
    """YouTube数据提取器"""
    
    def __init__(self):
        self.storage_path = settings.storage_path
        self.youtube_api_key = settings.youtube_api_key
        os.makedirs(self.storage_path, exist_ok=True)
        
        # YouTube Data API客户端
        if self.youtube_api_key:
            self.youtube_api = build('youtube', 'v3', developerKey=self.youtube_api_key)
        else:
            self.youtube_api = None
            logging.warning("YouTube API key not configured")
        
        # yt-dlp配置
        self.ydl_opts_info = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
        }
        
        self.ydl_opts_audio = {
            'format': 'bestaudio/best',
            'outtmpl': os.path.join(self.storage_path, '%(id)s.%(ext)s'),
            'quiet': True,
            'extractaudio': True,
            'audioformat': 'wav',
            'audioquality': '192K',
        }
    
    async def validate_url(self, url: str) -> bool:
        """验证YouTube URL有效性"""
        youtube_patterns = [
            r'^https?://(www\.)?youtube\.com/watch\?v=[\w-]+',
            r'^https?://(www\.)?youtu\.be/[\w-]+',
            r'^https?://(www\.)?youtube\.com/embed/[\w-]+',
        ]
        
        for pattern in youtube_patterns:
            if re.match(pattern, url):
                try:
                    video_id = self._extract_video_id(url)
                    return video_id is not None
                except Exception:
                    return False
        return False
    
    def _extract_video_id(self, url: str) -> Optional[str]:
        """从URL提取视频ID"""
        patterns = [
            r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([^&\n?#]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None
    
    async def extract_video_info(self, url: str) -> VideoInfo:
        """提取视频基本信息"""
        try:
            with yt_dlp.YoutubeDL(self.ydl_opts_info) as ydl:
                info = await asyncio.get_event_loop().run_in_executor(
                    None, ydl.extract_info, url, False
                )
                
                if not info:
                    raise ExternalServiceError("Failed to extract video information")
                
                # 使用YouTube API获取更详细信息
                video_id = info.get('id')
                api_info = await self._get_api_video_info(video_id) if video_id else {}
                
                # 合并信息
                return VideoInfo(
                    id=video_id or '',
                    title=info.get('title', ''),
                    description=info.get('description', ''),
                    duration=info.get('duration', 0),
                    view_count=api_info.get('viewCount', info.get('view_count', 0)),
                    like_count=api_info.get('likeCount', info.get('like_count', 0)),
                    comment_count=api_info.get('commentCount', info.get('comment_count', 0)),
                    channel_id=info.get('channel_id', ''),
                    channel_name=info.get('uploader', ''),
                    published_at=self._parse_date(info.get('upload_date')),
                    tags=api_info.get('tags', []),
                    category=api_info.get('categoryId', ''),
                    language=info.get('language', 'unknown'),
                    thumbnail_url=info.get('thumbnail', '')
                )
                
        except Exception as e:
            logging.error(f"Failed to extract video info: {e}")
            raise ExternalServiceError(f"Video extraction failed: {str(e)}")
    
    async def extract_audio(self, url: str, quality: str = 'best') -> AudioFile:
        """提取音频文件"""
        try:
            video_id = self._extract_video_id(url)
            if not video_id:
                raise ValidationError("Invalid YouTube URL")
            
            # 配置音频提取选项
            opts = self.ydl_opts_audio.copy()
            if quality == 'low':
                opts['audioquality'] = '96K'
            elif quality == 'high':
                opts['audioquality'] = '320K'
            
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = await asyncio.get_event_loop().run_in_executor(
                    None, ydl.extract_info, url, True
                )
                
                # 查找生成的音频文件
                audio_file = None
                for ext in ['wav', 'mp3', 'm4a']:
                    potential_file = os.path.join(self.storage_path, f"{video_id}.{ext}")
                    if os.path.exists(potential_file):
                        audio_file = potential_file
                        break
                
                if not audio_file:
                    raise ExternalServiceError("Audio file not found after extraction")
                
                file_size = os.path.getsize(audio_file)
                
                return AudioFile(
                    file_path=audio_file,
                    format=audio_file.split('.')[-1],
                    quality=quality,
                    duration=info.get('duration', 0),
                    file_size=file_size
                )
                
        except Exception as e:
            logging.error(f"Failed to extract audio: {e}")
            raise ExternalServiceError(f"Audio extraction failed: {str(e)}")
    
    async def extract_comments(
        self, 
        video_id: str, 
        max_count: int = 1000,
        sort_by: str = 'relevance'
    ) -> List[Comment]:
        """提取评论数据"""
        if not self.youtube_api:
            raise ExternalServiceError("YouTube API not configured")
        
        try:
            comments = []
            next_page_token = None
            
            while len(comments) < max_count:
                # 获取评论
                request = self.youtube_api.commentThreads().list(
                    part='snippet,replies',
                    videoId=video_id,
                    order=sort_by,
                    maxResults=min(100, max_count - len(comments)),
                    pageToken=next_page_token
                )
                
                response = await asyncio.get_event_loop().run_in_executor(
                    None, request.execute
                )
                
                # 处理评论
                for item in response.get('items', []):
                    top_comment = item['snippet']['topLevelComment']['snippet']
                    
                    comment = Comment(
                        id=item['id'],
                        text=top_comment['textDisplay'],
                        author=top_comment['authorDisplayName'],
                        author_channel_id=top_comment.get('authorChannelId', {}).get('value'),
                        like_count=top_comment.get('likeCount', 0),
                        reply_count=item['snippet'].get('totalReplyCount', 0),
                        published_at=self._parse_api_date(top_comment['publishedAt']),
                        is_author_reply=False
                    )
                    comments.append(comment)
                    
                    # 处理回复
                    if 'replies' in item:
                        for reply_item in item['replies']['comments']:
                            reply = reply_item['snippet']
                            
                            # 检查是否为作者回复
                            is_author_reply = self._is_author_reply(
                                reply.get('authorChannelId', {}).get('value'),
                                video_id
                            )
                            
                            reply_comment = Comment(
                                id=reply_item['id'],
                                text=reply['textDisplay'],
                                author=reply['authorDisplayName'],
                                author_channel_id=reply.get('authorChannelId', {}).get('value'),
                                like_count=reply.get('likeCount', 0),
                                reply_count=0,
                                published_at=self._parse_api_date(reply['publishedAt']),
                                is_author_reply=is_author_reply,
                                parent_comment_id=comment.id
                            )
                            comments.append(reply_comment)
                
                next_page_token = response.get('nextPageToken')
                if not next_page_token:
                    break
            
            return comments[:max_count]
            
        except Exception as e:
            logging.error(f"Failed to extract comments: {e}")
            raise ExternalServiceError(f"Comment extraction failed: {str(e)}")
    
    async def _get_api_video_info(self, video_id: str) -> Dict[str, Any]:
        """使用API获取视频详细信息"""
        if not self.youtube_api:
            return {}
        
        try:
            request = self.youtube_api.videos().list(
                part='snippet,statistics',
                id=video_id
            )
            
            response = await asyncio.get_event_loop().run_in_executor(
                None, request.execute
            )
            
            if response['items']:
                item = response['items'][0]
                snippet = item['snippet']
                statistics = item.get('statistics', {})
                
                return {
                    'viewCount': int(statistics.get('viewCount', 0)),
                    'likeCount': int(statistics.get('likeCount', 0)),
                    'commentCount': int(statistics.get('commentCount', 0)),
                    'tags': snippet.get('tags', []),
                    'categoryId': snippet.get('categoryId', ''),
                }
            
            return {}
            
        except Exception as e:
            logging.warning(f"Failed to get API video info: {e}")
            return {}
    
    async def _is_author_reply(self, commenter_channel_id: str, video_id: str) -> bool:
        """检查评论是否为视频作者回复"""
        if not commenter_channel_id or not self.youtube_api:
            return False
        
        try:
            # 获取视频的频道ID
            request = self.youtube_api.videos().list(
                part='snippet',
                id=video_id
            )
            
            response = await asyncio.get_event_loop().run_in_executor(
                None, request.execute
            )
            
            if response['items']:
                video_channel_id = response['items'][0]['snippet']['channelId']
                return commenter_channel_id == video_channel_id
            
            return False
            
        except Exception:
            return False
    
    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """解析日期字符串"""
        if not date_str:
            return None
        
        try:
            return datetime.strptime(date_str, '%Y%m%d')
        except ValueError:
            return None
    
    def _parse_api_date(self, date_str: str) -> datetime:
        """解析API日期字符串"""
        try:
            # 移除时区信息并解析
            clean_date = date_str.replace('Z', '+00:00')
            return datetime.fromisoformat(clean_date.replace('+00:00', ''))
        except ValueError:
            return datetime.now()
    
    async def cleanup_files(self, video_id: str):
        """清理临时文件"""
        try:
            for ext in ['wav', 'mp3', 'm4a', 'webm', 'mp4']:
                file_path = os.path.join(self.storage_path, f"{video_id}.{ext}")
                if os.path.exists(file_path):
                    os.remove(file_path)
                    logging.info(f"Cleaned up file: {file_path}")
        except Exception as e:
            logging.warning(f"Failed to cleanup files: {e}")
```

### 2. Celery任务集成

```python
# backend/app/tasks/extraction.py
from celery import current_task
from app.core.celery_app import celery_app
from app.services.youtube_extractor import YouTubeExtractor
from app.api.v1.websocket import send_progress_update
from app.models.task import AnalysisTask, TaskStatus
from app.core.database import get_db_session

@celery_app.task(bind=True)
def extract_youtube_data(self, task_id: str, youtube_url: str, options: dict):
    """提取YouTube数据的Celery任务"""
    
    async def _extract_data():
        extractor = YouTubeExtractor()
        
        try:
            # 更新任务状态
            async with get_db_session() as db:
                await db.execute(
                    update(AnalysisTask)
                    .where(AnalysisTask.id == task_id)
                    .values(
                        status=TaskStatus.PROCESSING,
                        current_step="数据提取"
                    )
                )
                await db.commit()
            
            # 发送进度更新
            await send_progress_update(task_id, 10, "验证YouTube链接")
            
            # 验证URL
            if not await extractor.validate_url(youtube_url):
                raise ValidationError("Invalid YouTube URL")
            
            await send_progress_update(task_id, 20, "提取视频信息")
            
            # 提取视频信息
            video_info = await extractor.extract_video_info(youtube_url)
            
            await send_progress_update(task_id, 40, "提取音频文件")
            
            # 提取音频
            audio_file = await extractor.extract_audio(
                youtube_url, 
                options.get('audio_quality', 'best')
            )
            
            # 提取评论（如果需要）
            comments = []
            if options.get('include_comments', True):
                await send_progress_update(task_id, 60, "提取评论数据")
                comments = await extractor.extract_comments(
                    video_info.id,
                    options.get('max_comments', 1000)
                )
            
            await send_progress_update(task_id, 80, "保存提取结果")
            
            # 保存结果到数据库
            extraction_result = {
                'video_info': video_info.__dict__,
                'audio_file': audio_file.__dict__,
                'comments': [comment.__dict__ for comment in comments],
                'extraction_metadata': {
                    'extracted_at': datetime.utcnow().isoformat(),
                    'comment_count': len(comments),
                    'audio_duration': audio_file.duration,
                    'audio_size': audio_file.file_size
                }
            }
            
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
            logging.error(f"Extraction failed for task {task_id}: {e}")
            
            async with get_db_session() as db:
                await db.execute(
                    update(AnalysisTask)
                    .where(AnalysisTask.id == task_id)
                    .values(
                        status=TaskStatus.FAILED,
                        error_message=str(e)
                    )
                )
                await db.commit()
            
            raise
    
    # 运行异步函数
    import asyncio
    return asyncio.run(_extract_data())
```

### 3. 数据模型定义

```python
# backend/app/models/schemas.py
from pydantic import BaseModel, Field, validator
from typing import List, Optional
from datetime import datetime

class VideoInfo(BaseModel):
    id: str
    title: str
    description: str
    duration: int = Field(..., description="视频时长（秒）")
    view_count: int = Field(0, description="观看次数")
    like_count: int = Field(0, description="点赞数")
    comment_count: int = Field(0, description="评论数")
    channel_id: str
    channel_name: str
    channel_subscriber_count: Optional[int] = None
    published_at: Optional[datetime] = None
    tags: List[str] = Field(default_factory=list)
    category: str = ""
    language: str = "unknown"
    thumbnail_url: str = ""

class Comment(BaseModel):
    id: str
    text: str
    author: str
    author_channel_id: Optional[str] = None
    like_count: int = 0
    reply_count: int = 0
    published_at: datetime
    is_author_reply: bool = False
    parent_comment_id: Optional[str] = None
    
    @validator('text')
    def clean_text(cls, v):
        # 清理评论文本
        return v.strip()

class AudioFile(BaseModel):
    file_path: str
    format: str
    quality: str
    duration: int = Field(..., description="音频时长（秒）")
    file_size: int = Field(..., description="文件大小（字节）")
    
    @validator('file_path')
    def validate_file_exists(cls, v):
        import os
        if not os.path.exists(v):
            raise ValueError(f"Audio file not found: {v}")
        return v

class ExtractionResult(BaseModel):
    video_info: VideoInfo
    audio_file: AudioFile
    comments: List[Comment]
    extraction_metadata: dict
```

## 依赖关系

### 前置条件
- Task 1: 项目配置管理（必须完成）
- Task 2: 后端API框架（必须完成）

### 阻塞任务
- Task 5: 音频转录服务（需要音频文件）
- Task 6: 内容分析模块（需要视频信息）
- Task 7: 评论分析模块（需要评论数据）
- Task 8: 分析编排器（需要提取服务）

## 验收标准

### 功能验收
- [ ] YouTube URL验证正确工作
- [ ] 视频信息提取完整准确
- [ ] 音频文件提取成功且质量可控
- [ ] 评论数据提取包含作者回复标识
- [ ] 错误处理和重试机制正常
- [ ] 文件清理功能正常工作

### 技术验收
- [ ] 支持多种YouTube URL格式
- [ ] 音频提取时间 < 视频时长的20%
- [ ] 评论提取速度 > 100条/分钟
- [ ] 内存使用合理（< 1GB）
- [ ] 临时文件正确清理

### 质量验收
- [ ] 单元测试覆盖率 ≥ 80%
- [ ] 集成测试覆盖主要场景
- [ ] 错误日志详细且有用
- [ ] API配额使用优化
- [ ] 代码遵循项目规范

## 测试要求

### 单元测试
```python
# tests/test_youtube_extractor.py
import pytest
from unittest.mock import Mock, patch
from app.services.youtube_extractor import YouTubeExtractor

@pytest.fixture
def extractor():
    return YouTubeExtractor()

@pytest.mark.asyncio
async def test_validate_url_valid(extractor):
    """测试有效URL验证"""
    valid_urls = [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "https://youtu.be/dQw4w9WgXcQ",
        "https://youtube.com/watch?v=dQw4w9WgXcQ"
    ]
    
    for url in valid_urls:
        with patch.object(extractor, '_extract_video_id', return_value='dQw4w9WgXcQ'):
            assert await extractor.validate_url(url) == True

@pytest.mark.asyncio
async def test_validate_url_invalid(extractor):
    """测试无效URL验证"""
    invalid_urls = [
        "https://example.com",
        "not_a_url",
        "https://youtube.com/invalid"
    ]
    
    for url in invalid_urls:
        assert await extractor.validate_url(url) == False

@pytest.mark.asyncio
async def test_extract_video_info(extractor):
    """测试视频信息提取"""
    mock_info = {
        'id': 'test_id',
        'title': 'Test Video',
        'description': 'Test Description',
        'duration': 300,
        'view_count': 1000,
        'channel_id': 'test_channel',
        'uploader': 'Test Channel'
    }
    
    with patch('yt_dlp.YoutubeDL') as mock_ydl:
        mock_ydl.return_value.__enter__.return_value.extract_info.return_value = mock_info
        
        result = await extractor.extract_video_info("https://youtube.com/watch?v=test_id")
        
        assert result.id == 'test_id'
        assert result.title == 'Test Video'
        assert result.duration == 300

@pytest.mark.asyncio
async def test_extract_comments_with_author_replies(extractor):
    """测试评论提取包含作者回复"""
    mock_response = {
        'items': [
            {
                'id': 'comment1',
                'snippet': {
                    'topLevelComment': {
                        'snippet': {
                            'textDisplay': 'Great video!',
                            'authorDisplayName': 'User1',
                            'likeCount': 5,
                            'publishedAt': '2023-01-01T00:00:00Z'
                        }
                    },
                    'totalReplyCount': 1
                },
                'replies': {
                    'comments': [
                        {
                            'id': 'reply1',
                            'snippet': {
                                'textDisplay': 'Thanks!',
                                'authorDisplayName': 'Channel Owner',
                                'authorChannelId': {'value': 'channel_id'},
                                'publishedAt': '2023-01-01T01:00:00Z'
                            }
                        }
                    ]
                }
            }
        ]
    }
    
    with patch.object(extractor, 'youtube_api') as mock_api:
        mock_api.commentThreads.return_value.list.return_value.execute.return_value = mock_response
        
        with patch.object(extractor, '_is_author_reply', return_value=True):
            comments = await extractor.extract_comments('test_video_id')
            
            assert len(comments) == 2
            assert comments[1].is_author_reply == True
            assert comments[1].parent_comment_id == 'comment1'
```

### 集成测试
```python
# tests/test_extraction_integration.py
import pytest
from app.tasks.extraction import extract_youtube_data

@pytest.mark.integration
@pytest.mark.asyncio
async def test_full_extraction_pipeline():
    """测试完整提取流程"""
    # 使用真实的YouTube视频进行测试
    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    task_id = "test_task_id"
    options = {
        'include_comments': True,
        'max_comments': 10,
        'audio_quality': 'best'
    }
    
    result = await extract_youtube_data(task_id, test_url, options)
    
    assert 'video_info' in result
    assert 'audio_file' in result
    assert 'comments' in result
    assert result['video_info']['id'] == 'dQw4w9WgXcQ'
```

## 预估工作量

- **开发时间**: 3-4天
- **测试时间**: 1.5天
- **集成调试**: 1天
- **文档时间**: 0.5天
- **总计**: 6天

## 关键路径

此任务在关键路径上，完成后将为Task 5、6、7提供必要的数据输入。

## 交付检查清单

- [ ] YouTube提取器服务已实现
- [ ] Celery任务集成已完成
- [ ] 数据模型已定义
- [ ] URL验证功能已实现
- [ ] 音频提取功能已实现
- [ ] 评论提取功能已实现
- [ ] 作者回复识别已实现
- [ ] 错误处理已完善
- [ ] 单元测试和集成测试通过
- [ ] 文件清理功能已实现
- [ ] 代码已提交并通过CI检查

## 后续任务接口

完成此任务后，为后续任务提供：
- 标准化的视频信息数据
- 高质量的音频文件
- 结构化的评论数据（包含作者回复标识）
- 提取元数据和统计信息
- 文件管理和清理机制

这些将被Task 5（音频转录）、Task 6（内容分析）和Task 7（评论分析）直接使用。
