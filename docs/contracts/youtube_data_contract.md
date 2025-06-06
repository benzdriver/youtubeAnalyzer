# YouTube数据提取接口契约

**提供方**: TASK_04 (YouTube数据提取)  
**使用方**: TASK_05 (音频转录服务), TASK_07 (评论分析模块)  
**版本**: v1.0.0

## 概述

定义YouTube数据提取服务的接口规范，包括视频信息、音频文件、评论数据的提取和格式化。

## 数据模型定义

### VideoInfo 数据结构

```python
from pydantic import BaseModel, HttpUrl
from typing import Optional, List
from datetime import datetime

class VideoInfo(BaseModel):
    """视频基本信息"""
    id: str
    title: str
    description: Optional[str] = None
    duration: int  # 秒
    upload_date: datetime
    view_count: Optional[int] = None
    like_count: Optional[int] = None
    comment_count: Optional[int] = None
    
    # 频道信息
    channel_id: str
    channel_title: str
    channel_subscriber_count: Optional[int] = None
    
    # 媒体信息
    thumbnail_url: Optional[HttpUrl] = None
    video_url: HttpUrl
    
    # 技术信息
    format_id: str
    resolution: Optional[str] = None
    fps: Optional[int] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
```

### AudioFile 数据结构

```python
class AudioFile(BaseModel):
    """音频文件信息"""
    file_path: str
    file_size: int  # 字节
    duration: int  # 秒
    format: str  # 'wav', 'mp3', 'm4a'
    sample_rate: int  # Hz
    channels: int
    bitrate: Optional[int] = None
    
    # 提取信息
    extracted_at: datetime
    source_video_id: str
    
    def __str__(self):
        return f"AudioFile({self.file_path}, {self.duration}s, {self.format})"
```

### CommentData 数据结构

```python
class CommentAuthor(BaseModel):
    """评论作者信息"""
    id: str
    name: str
    channel_url: Optional[str] = None
    is_verified: bool = False
    subscriber_count: Optional[int] = None

class Comment(BaseModel):
    """单条评论"""
    id: str
    text: str
    author: CommentAuthor
    like_count: int = 0
    reply_count: int = 0
    published_at: datetime
    updated_at: Optional[datetime] = None
    
    # 层级关系
    parent_id: Optional[str] = None  # 如果是回复，指向父评论ID
    is_author_reply: bool = False  # 是否为视频作者回复
    
    # 位置信息
    timestamp: Optional[int] = None  # 评论对应的视频时间戳（秒）
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class CommentData(BaseModel):
    """评论数据集合"""
    video_id: str
    total_count: int
    comments: List[Comment]
    
    # 提取信息
    extracted_at: datetime
    extraction_method: str  # 'api', 'scraping'
    
    # 统计信息
    author_reply_count: int = 0
    top_level_count: int = 0
    reply_count: int = 0
    
    def get_author_replies(self, channel_id: str) -> List[Comment]:
        """获取作者回复"""
        return [c for c in self.comments if c.author.id == channel_id]
    
    def get_top_comments(self, limit: int = 10) -> List[Comment]:
        """获取热门评论"""
        return sorted(self.comments, key=lambda x: x.like_count, reverse=True)[:limit]
```

## API接口规范

### 提取服务接口

```python
from abc import ABC, abstractmethod

class YouTubeExtractor(ABC):
    """YouTube数据提取器接口"""
    
    @abstractmethod
    async def extract_video_info(self, url: str) -> VideoInfo:
        """提取视频基本信息"""
        pass
    
    @abstractmethod
    async def download_audio(self, url: str, output_dir: str) -> AudioFile:
        """下载音频文件"""
        pass
    
    @abstractmethod
    async def extract_comments(self, url: str, max_comments: int = 1000) -> CommentData:
        """提取评论数据"""
        pass
    
    @abstractmethod
    async def extract_all(self, url: str, options: dict) -> dict:
        """提取所有数据"""
        pass
```

### 具体实现接口

```python
class YTDLPExtractor(YouTubeExtractor):
    """基于yt-dlp的提取器实现"""
    
    async def extract_video_info(self, url: str) -> VideoInfo:
        """提取视频信息"""
        try:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': False
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
            return VideoInfo(
                id=info['id'],
                title=info['title'],
                description=info.get('description'),
                duration=info.get('duration', 0),
                upload_date=datetime.fromisoformat(info['upload_date']),
                view_count=info.get('view_count'),
                like_count=info.get('like_count'),
                comment_count=info.get('comment_count'),
                channel_id=info['channel_id'],
                channel_title=info['channel'],
                thumbnail_url=info.get('thumbnail'),
                video_url=url,
                format_id=info.get('format_id', 'unknown'),
                resolution=info.get('resolution'),
                fps=info.get('fps')
            )
            
        except Exception as e:
            raise ExtractionError(f"视频信息提取失败: {e}")
    
    async def download_audio(self, url: str, output_dir: str) -> AudioFile:
        """下载音频文件"""
        try:
            output_path = os.path.join(output_dir, f"{uuid.uuid4()}.wav")
            
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': output_path,
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'wav',
                    'preferredquality': '192',
                }],
                'quiet': True
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                
            # 获取音频文件信息
            file_stats = os.stat(output_path)
            
            return AudioFile(
                file_path=output_path,
                file_size=file_stats.st_size,
                duration=info.get('duration', 0),
                format='wav',
                sample_rate=44100,  # 默认采样率
                channels=2,  # 默认立体声
                extracted_at=datetime.utcnow(),
                source_video_id=info['id']
            )
            
        except Exception as e:
            raise ExtractionError(f"音频下载失败: {e}")
```

## 错误处理规范

### 异常类型定义

```python
class ExtractionError(Exception):
    """数据提取错误基类"""
    pass

class VideoNotFoundError(ExtractionError):
    """视频不存在错误"""
    pass

class PrivateVideoError(ExtractionError):
    """私有视频错误"""
    pass

class RegionBlockedError(ExtractionError):
    """地区限制错误"""
    pass

class RateLimitError(ExtractionError):
    """频率限制错误"""
    pass

class AudioDownloadError(ExtractionError):
    """音频下载错误"""
    pass

class CommentExtractionError(ExtractionError):
    """评论提取错误"""
    pass
```

### 错误响应格式

```json
{
  "error": "extraction_error",
  "error_type": "VideoNotFoundError",
  "message": "视频不存在或已被删除",
  "code": "VIDEO_NOT_FOUND",
  "details": {
    "url": "https://youtube.com/watch?v=invalid",
    "video_id": "invalid",
    "timestamp": "2025-06-06T01:00:00Z"
  },
  "retry_after": null
}
```

## 数据验证规则

### URL验证

```python
import re
from urllib.parse import urlparse, parse_qs

def validate_youtube_url(url: str) -> bool:
    """验证YouTube URL格式"""
    patterns = [
        r'(?:https?://)?(?:www\.)?youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})',
        r'(?:https?://)?(?:www\.)?youtu\.be/([a-zA-Z0-9_-]{11})',
        r'(?:https?://)?(?:www\.)?youtube\.com/embed/([a-zA-Z0-9_-]{11})'
    ]
    
    return any(re.match(pattern, url) for pattern in patterns)

def extract_video_id(url: str) -> str:
    """从URL提取视频ID"""
    if 'youtu.be/' in url:
        return url.split('youtu.be/')[-1].split('?')[0]
    elif 'youtube.com/watch' in url:
        parsed = urlparse(url)
        return parse_qs(parsed.query)['v'][0]
    elif 'youtube.com/embed/' in url:
        return url.split('embed/')[-1].split('?')[0]
    else:
        raise ValueError("无效的YouTube URL")
```

### 数据完整性验证

```python
def validate_video_info(info: VideoInfo) -> bool:
    """验证视频信息完整性"""
    required_fields = ['id', 'title', 'duration', 'channel_id', 'channel_title']
    
    for field in required_fields:
        if not getattr(info, field):
            raise ValueError(f"缺少必需字段: {field}")
    
    if info.duration <= 0:
        raise ValueError("视频时长必须大于0")
    
    return True

def validate_audio_file(audio: AudioFile) -> bool:
    """验证音频文件"""
    if not os.path.exists(audio.file_path):
        raise ValueError(f"音频文件不存在: {audio.file_path}")
    
    if audio.file_size <= 0:
        raise ValueError("音频文件大小无效")
    
    if audio.duration <= 0:
        raise ValueError("音频时长无效")
    
    return True
```

## 性能要求

### 提取时间限制

- **视频信息提取**: < 10秒
- **音频下载**: < 视频时长 × 0.5
- **评论提取**: < 30秒 (1000条评论)

### 资源使用限制

- **内存使用**: < 500MB per extraction
- **磁盘空间**: 音频文件 < 100MB per minute
- **网络带宽**: 合理使用，避免触发限制

## 测试用例

### 单元测试示例

```python
import pytest
from unittest.mock import Mock, patch

@pytest.mark.asyncio
async def test_extract_video_info():
    """测试视频信息提取"""
    extractor = YTDLPExtractor()
    
    with patch('yt_dlp.YoutubeDL') as mock_ydl:
        mock_ydl.return_value.__enter__.return_value.extract_info.return_value = {
            'id': 'test_video_id',
            'title': 'Test Video',
            'duration': 300,
            'upload_date': '20250606',
            'channel_id': 'test_channel',
            'channel': 'Test Channel',
            'view_count': 1000
        }
        
        result = await extractor.extract_video_info('https://youtube.com/watch?v=test')
        
        assert result.id == 'test_video_id'
        assert result.title == 'Test Video'
        assert result.duration == 300

@pytest.mark.asyncio
async def test_download_audio():
    """测试音频下载"""
    extractor = YTDLPExtractor()
    
    with patch('yt_dlp.YoutubeDL') as mock_ydl:
        with patch('os.stat') as mock_stat:
            mock_stat.return_value.st_size = 1024000
            mock_ydl.return_value.__enter__.return_value.extract_info.return_value = {
                'id': 'test_video_id',
                'duration': 300
            }
            
            result = await extractor.download_audio('https://youtube.com/watch?v=test', '/tmp')
            
            assert result.source_video_id == 'test_video_id'
            assert result.duration == 300
            assert result.file_size == 1024000
```

### 集成测试示例

```python
@pytest.mark.integration
async def test_full_extraction_pipeline():
    """测试完整提取流程"""
    extractor = YTDLPExtractor()
    test_url = "https://youtube.com/watch?v=dQw4w9WgXcQ"  # 测试视频
    
    # 提取视频信息
    video_info = await extractor.extract_video_info(test_url)
    assert video_info.id is not None
    
    # 下载音频
    audio_file = await extractor.download_audio(test_url, "/tmp")
    assert os.path.exists(audio_file.file_path)
    
    # 提取评论
    comments = await extractor.extract_comments(test_url, max_comments=100)
    assert len(comments.comments) > 0
    
    # 清理
    os.remove(audio_file.file_path)
```

## 使用示例

### 基本使用

```python
from app.services.youtube_extractor import YTDLPExtractor

async def extract_youtube_data(url: str):
    """提取YouTube数据示例"""
    extractor = YTDLPExtractor()
    
    try:
        # 提取所有数据
        result = await extractor.extract_all(url, {
            'max_comments': 1000,
            'audio_format': 'wav',
            'output_dir': '/tmp/audio'
        })
        
        return {
            'video_info': result['video_info'],
            'audio_file': result['audio_file'],
            'comments': result['comments']
        }
        
    except ExtractionError as e:
        logger.error(f"提取失败: {e}")
        raise
```

### Celery任务集成

```python
from celery import current_task
from app.core.celery_app import celery_app

@celery_app.task(bind=True)
def extract_youtube_data_task(self, task_id: str, url: str, options: dict):
    """YouTube数据提取任务"""
    
    async def _extract():
        extractor = YTDLPExtractor()
        
        # 更新进度
        self.update_state(state='PROGRESS', meta={'progress': 10, 'message': '开始提取'})
        
        # 提取视频信息
        video_info = await extractor.extract_video_info(url)
        self.update_state(state='PROGRESS', meta={'progress': 30, 'message': '视频信息提取完成'})
        
        # 下载音频
        audio_file = await extractor.download_audio(url, options['output_dir'])
        self.update_state(state='PROGRESS', meta={'progress': 70, 'message': '音频下载完成'})
        
        # 提取评论
        comments = await extractor.extract_comments(url, options.get('max_comments', 1000))
        self.update_state(state='PROGRESS', meta={'progress': 100, 'message': '数据提取完成'})
        
        return {
            'video_info': video_info.dict(),
            'audio_file': audio_file.dict(),
            'comments': comments.dict()
        }
    
    import asyncio
    return asyncio.run(_extract())
```
