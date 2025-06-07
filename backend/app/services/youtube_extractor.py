import logging
import os
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import yt_dlp
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from app.core.config import settings
from app.utils.exceptions import (
    AudioDownloadError,
    ExternalServiceError,
    RateLimitError,
    ValidationError,
    YouTubeAPIError,
)


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
        if not settings.youtube_api_key:
            raise ValidationError("YouTube API key is required")

        self.youtube_api = build("youtube", "v3", developerKey=settings.youtube_api_key)

        audio_dir = os.path.join(settings.storage_path, "audio")
        os.makedirs(audio_dir, exist_ok=True)

        self.ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": os.path.join(audio_dir, "%(id)s.%(ext)s"),
            "extractaudio": True,
            "audioformat": "wav",
            "audioquality": "192K",
            "no_warnings": True,
            "quiet": True,
        }

    def extract_video_id(self, url: str) -> str:
        """从YouTube URL提取视频ID"""
        patterns = [
            r"(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([^&\n?#]+)",
            r"youtube\.com/watch\?.*v=([^&\n?#]+)",
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
                part="snippet,statistics,contentDetails", id=video_id
            )
            response = request.execute()

            if not response["items"]:
                raise ValidationError(f"视频不存在或无法访问: {video_id}")

            item = response["items"][0]
            snippet = item["snippet"]
            statistics = item["statistics"]
            content_details = item["contentDetails"]

            duration = self._parse_duration(content_details["duration"])

            return VideoInfo(
                id=video_id,
                title=snippet["title"],
                description=snippet["description"],
                duration=duration,
                view_count=int(statistics.get("viewCount", 0)),
                like_count=int(statistics.get("likeCount", 0)),
                channel_id=snippet["channelId"],
                channel_title=snippet["channelTitle"],
                upload_date=snippet["publishedAt"],
                thumbnail_url=snippet["thumbnails"]["high"]["url"],
                language=snippet.get("defaultLanguage"),
            )

        except HttpError as e:
            logging.error(f"YouTube API error: {e}")

            if e.resp.status == 403:
                if "quotaExceeded" in str(e):
                    raise RateLimitError(
                        f"YouTube API配额已用完",
                        service="youtube_api",
                        retry_after=3600,
                    )
                elif "forbidden" in str(e).lower():
                    raise YouTubeAPIError(
                        f"视频访问被禁止: {video_id}", error_code="forbidden"
                    )
            elif e.resp.status == 404:
                raise YouTubeAPIError(f"视频不存在: {video_id}", error_code="not_found")
            elif e.resp.status == 429:
                raise RateLimitError(
                    f"YouTube API请求过于频繁", service="youtube_api", retry_after=300
                )
            else:
                raise YouTubeAPIError(
                    f"YouTube API调用失败: {e}", error_code=str(e.resp.status)
                )

        except Exception as e:
            logging.error(f"Video info extraction failed: {e}")
            raise ExternalServiceError(f"视频信息获取失败: {e}")

    async def download_audio(self, video_id: str) -> str:
        """下载视频音频"""
        try:
            url = f"https://youtube.com/watch?v={video_id}"

            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)

                audio_dir = os.path.join(settings.storage_path, "audio")
                for ext in ["wav", "mp3", "m4a", "webm"]:
                    potential_path = os.path.join(audio_dir, f"{video_id}.{ext}")
                    if os.path.exists(potential_path):
                        return potential_path

                raise ExternalServiceError(f"音频文件下载失败: {video_id}")

        except Exception as e:
            logging.error(f"Audio download failed for {video_id}: {e}")

            error_msg = str(e).lower()
            if "private video" in error_msg or "video unavailable" in error_msg:
                raise AudioDownloadError(
                    f"视频不可用或为私有视频: {video_id}", video_id=video_id
                )
            elif "age-restricted" in error_msg:
                raise AudioDownloadError(
                    f"年龄限制视频无法下载: {video_id}", video_id=video_id
                )
            elif "copyright" in error_msg:
                raise AudioDownloadError(
                    f"版权限制视频无法下载: {video_id}", video_id=video_id
                )
            elif "network" in error_msg or "connection" in error_msg:
                raise RateLimitError(f"网络连接问题，请稍后重试: {e}", retry_after=60)
            else:
                raise AudioDownloadError(f"音频下载失败: {e}", video_id=video_id)

    async def get_comments(
        self, video_id: str, max_results: int = 100
    ) -> List[CommentData]:
        """获取视频评论"""
        try:
            video_info = await self.get_video_info(video_id)
            video_channel_id = video_info.channel_id

            comments = []
            next_page_token = None

            while len(comments) < max_results:
                request = self.youtube_api.commentThreads().list(
                    part="snippet,replies",
                    videoId=video_id,
                    maxResults=min(100, max_results - len(comments)),
                    order="relevance",
                    pageToken=next_page_token,
                )

                response = request.execute()

                for item in response["items"]:
                    top_comment = item["snippet"]["topLevelComment"]["snippet"]

                    comment_data = CommentData(
                        id=item["snippet"]["topLevelComment"]["id"],
                        text=top_comment["textDisplay"],
                        author=top_comment["authorDisplayName"],
                        author_channel_id=top_comment.get("authorChannelId", {}).get(
                            "value", ""
                        ),
                        like_count=top_comment["likeCount"],
                        reply_count=item["snippet"]["totalReplyCount"],
                        published_at=top_comment["publishedAt"],
                        is_author_reply=top_comment.get("authorChannelId", {}).get(
                            "value", ""
                        )
                        == video_channel_id,
                    )
                    comments.append(comment_data)

                    if "replies" in item:
                        for reply in item["replies"]["comments"]:
                            reply_snippet = reply["snippet"]
                            reply_data = CommentData(
                                id=reply["id"],
                                text=reply_snippet["textDisplay"],
                                author=reply_snippet["authorDisplayName"],
                                author_channel_id=reply_snippet.get(
                                    "authorChannelId", {}
                                ).get("value", ""),
                                like_count=reply_snippet["likeCount"],
                                reply_count=0,
                                published_at=reply_snippet["publishedAt"],
                                is_author_reply=reply_snippet.get(
                                    "authorChannelId", {}
                                ).get("value", "")
                                == video_channel_id,
                                parent_id=item["snippet"]["topLevelComment"]["id"],
                            )
                            comments.append(reply_data)

                next_page_token = response.get("nextPageToken")
                if not next_page_token:
                    break

            return comments[:max_results]

        except HttpError as e:
            logging.error(f"YouTube API error getting comments: {e}")

            if e.resp.status == 403:
                if "commentsDisabled" in str(e):
                    logging.warning(f"Comments disabled for video {video_id}")
                    return []  # Return empty list instead of failing
                elif "quotaExceeded" in str(e):
                    raise RateLimitError(
                        f"YouTube API配额已用完",
                        service="youtube_api",
                        retry_after=3600,
                    )
                else:
                    raise YouTubeAPIError(
                        f"评论访问被禁止: {e}", error_code="forbidden"
                    )
            elif e.resp.status == 404:
                logging.warning(f"Video not found for comments: {video_id}")
                return []  # Return empty list for missing videos
            elif e.resp.status == 429:
                raise RateLimitError(
                    f"YouTube API请求过于频繁", service="youtube_api", retry_after=300
                )
            else:
                raise YouTubeAPIError(
                    f"评论获取失败: {e}", error_code=str(e.resp.status)
                )

        except Exception as e:
            logging.error(f"Comment extraction failed: {e}")
            raise ExternalServiceError(f"评论数据提取失败: {e}")

    def _parse_duration(self, duration_str: str) -> int:
        """解析ISO 8601时长格式为秒数"""
        import re

        pattern = r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?"
        match = re.match(pattern, duration_str)

        if not match:
            return 0

        hours = int(match.group(1) or 0)
        minutes = int(match.group(2) or 0)
        seconds = int(match.group(3) or 0)

        return hours * 3600 + minutes * 60 + seconds

    def cleanup_audio_file(self, file_path: str) -> None:
        """清理音频文件"""
        from app.utils.storage import storage_manager

        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logging.info(f"Cleaned up audio file: {file_path}")
        except Exception as e:
            logging.error(f"Failed to cleanup audio file {file_path}: {e}")

    def cleanup_video_files(self, video_id: str) -> bool:
        """清理指定视频的所有文件"""
        from app.utils.storage import storage_manager

        return storage_manager.cleanup_audio_file(video_id)
