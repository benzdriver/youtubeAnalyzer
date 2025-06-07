import os
from unittest.mock import AsyncMock, Mock, patch

import pytest
from googleapiclient.errors import HttpError

from app.services.youtube_extractor import CommentData, VideoInfo, YouTubeExtractor
from app.utils.exceptions import (
    AudioDownloadError,
    RateLimitError,
    ValidationError,
    YouTubeAPIError,
)


@pytest.fixture
def extractor():
    with patch("app.services.youtube_extractor.settings") as mock_settings:
        mock_settings.youtube_api_key = "test_api_key"
        mock_settings.storage_path = "/tmp/test_storage"

        with patch("app.services.youtube_extractor.build") as mock_build:
            mock_build.return_value = Mock()
            return YouTubeExtractor()


class TestVideoIdExtraction:
    """测试视频ID提取功能"""

    def test_extract_video_id_standard_url(self, extractor):
        """测试标准YouTube URL"""
        urls = [
            "https://youtube.com/watch?v=dQw4w9WgXcQ",
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "https://youtube.com/watch?v=dQw4w9WgXcQ&t=10s",
        ]

        for url in urls:
            video_id = extractor.extract_video_id(url)
            assert video_id == "dQw4w9WgXcQ"

    def test_extract_video_id_short_url(self, extractor):
        """测试短链接URL"""
        url = "https://youtu.be/dQw4w9WgXcQ"
        video_id = extractor.extract_video_id(url)
        assert video_id == "dQw4w9WgXcQ"

    def test_extract_video_id_embed_url(self, extractor):
        """测试嵌入URL"""
        url = "https://youtube.com/embed/dQw4w9WgXcQ"
        video_id = extractor.extract_video_id(url)
        assert video_id == "dQw4w9WgXcQ"

    def test_extract_video_id_invalid_url(self, extractor):
        """测试无效URL"""
        invalid_urls = [
            "https://example.com",
            "not_a_url",
            "https://youtube.com/channel/UC123",
            "",
        ]

        for url in invalid_urls:
            with pytest.raises(ValidationError):
                extractor.extract_video_id(url)


class TestVideoInfoExtraction:
    """测试视频信息获取功能"""

    @pytest.mark.asyncio
    async def test_get_video_info_success(self, extractor):
        """测试成功获取视频信息"""
        mock_response = {
            "items": [
                {
                    "snippet": {
                        "title": "Test Video",
                        "description": "Test Description",
                        "channelId": "test_channel_id",
                        "channelTitle": "Test Channel",
                        "publishedAt": "2023-01-01T00:00:00Z",
                        "thumbnails": {
                            "high": {"url": "https://example.com/thumb.jpg"}
                        },
                        "defaultLanguage": "en",
                    },
                    "statistics": {"viewCount": "1000", "likeCount": "100"},
                    "contentDetails": {"duration": "PT5M30S"},
                }
            ]
        }

        mock_request = Mock()
        mock_request.execute.return_value = mock_response
        extractor.youtube_api.videos.return_value.list.return_value = mock_request

        video_info = await extractor.get_video_info("test_id")

        assert video_info.id == "test_id"
        assert video_info.title == "Test Video"
        assert video_info.description == "Test Description"
        assert video_info.duration == 330  # 5分30秒
        assert video_info.view_count == 1000
        assert video_info.like_count == 100
        assert video_info.channel_id == "test_channel_id"
        assert video_info.channel_title == "Test Channel"
        assert video_info.language == "en"

    @pytest.mark.asyncio
    async def test_get_video_info_not_found(self, extractor):
        """测试视频不存在"""
        mock_response = {"items": []}

        mock_request = Mock()
        mock_request.execute.return_value = mock_response
        extractor.youtube_api.videos.return_value.list.return_value = mock_request

        with pytest.raises(ValidationError, match="视频不存在或无法访问"):
            await extractor.get_video_info("nonexistent_id")

    @pytest.mark.asyncio
    async def test_get_video_info_api_error_403(self, extractor):
        """测试API 403错误"""
        mock_error = HttpError(
            resp=Mock(status=403),
            content=b'{"error": {"errors": [{"reason": "quotaExceeded"}]}}',
        )

        mock_request = Mock()
        mock_request.execute.side_effect = mock_error
        extractor.youtube_api.videos.return_value.list.return_value = mock_request

        with pytest.raises(RateLimitError, match="YouTube API配额已用完"):
            await extractor.get_video_info("test_id")

    @pytest.mark.asyncio
    async def test_get_video_info_api_error_404(self, extractor):
        """测试API 404错误"""
        mock_error = HttpError(
            resp=Mock(status=404), content=b'{"error": {"message": "Video not found"}}'
        )

        mock_request = Mock()
        mock_request.execute.side_effect = mock_error
        extractor.youtube_api.videos.return_value.list.return_value = mock_request

        with pytest.raises(YouTubeAPIError, match="视频不存在"):
            await extractor.get_video_info("test_id")


class TestAudioDownload:
    """测试音频下载功能"""

    @pytest.mark.asyncio
    async def test_download_audio_success(self, extractor):
        """测试成功下载音频"""
        test_file_path = "/tmp/test_storage/audio/test_id.wav"

        with patch("app.services.youtube_extractor.yt_dlp.YoutubeDL") as mock_ydl_class:
            mock_ydl = Mock()
            mock_ydl_class.return_value.__enter__.return_value = mock_ydl
            mock_ydl.extract_info.return_value = {"id": "test_id"}

            with patch("os.path.exists") as mock_exists:
                mock_exists.side_effect = lambda path: path == test_file_path

                result = await extractor.download_audio("test_id")
                assert result == test_file_path
                mock_ydl.extract_info.assert_called_once()

    @pytest.mark.asyncio
    async def test_download_audio_private_video(self, extractor):
        """测试私有视频下载失败"""
        with patch("app.services.youtube_extractor.yt_dlp.YoutubeDL") as mock_ydl_class:
            mock_ydl = Mock()
            mock_ydl_class.return_value.__enter__.return_value = mock_ydl
            mock_ydl.extract_info.side_effect = Exception("Private video")

            with pytest.raises(AudioDownloadError, match="视频不可用或为私有视频"):
                await extractor.download_audio("test_id")

    @pytest.mark.asyncio
    async def test_download_audio_age_restricted(self, extractor):
        """测试年龄限制视频"""
        with patch("app.services.youtube_extractor.yt_dlp.YoutubeDL") as mock_ydl_class:
            mock_ydl = Mock()
            mock_ydl_class.return_value.__enter__.return_value = mock_ydl
            mock_ydl.extract_info.side_effect = Exception("age-restricted content")

            with pytest.raises(AudioDownloadError, match="年龄限制视频无法下载"):
                await extractor.download_audio("test_id")


class TestCommentExtraction:
    """测试评论提取功能"""

    @pytest.mark.asyncio
    async def test_get_comments_success(self, extractor):
        """测试成功获取评论"""
        video_info = VideoInfo(
            id="test_id",
            title="Test",
            description="Test",
            duration=100,
            view_count=1000,
            like_count=100,
            channel_id="channel_123",
            channel_title="Test Channel",
            upload_date="2023-01-01T00:00:00Z",
            thumbnail_url="https://example.com/thumb.jpg",
        )

        with patch.object(extractor, "get_video_info", return_value=video_info):
            mock_response = {
                "items": [
                    {
                        "snippet": {
                            "topLevelComment": {
                                "id": "comment_1",
                                "snippet": {
                                    "textDisplay": "Great video!",
                                    "authorDisplayName": "User1",
                                    "authorChannelId": {"value": "user_channel_1"},
                                    "likeCount": 5,
                                    "publishedAt": "2023-01-01T00:00:00Z",
                                },
                            },
                            "totalReplyCount": 1,
                        },
                        "replies": {
                            "comments": [
                                {
                                    "id": "reply_1",
                                    "snippet": {
                                        "textDisplay": "Thanks!",
                                        "authorDisplayName": "Test Channel",
                                        "authorChannelId": {"value": "channel_123"},
                                        "likeCount": 2,
                                        "publishedAt": "2023-01-01T01:00:00Z",
                                    },
                                }
                            ]
                        },
                    }
                ]
            }

            mock_request = Mock()
            mock_request.execute.return_value = mock_response
            extractor.youtube_api.commentThreads.return_value.list.return_value = (
                mock_request
            )

            comments = await extractor.get_comments("test_id", max_results=10)

            assert len(comments) == 2

            main_comment = comments[0]
            assert main_comment.id == "comment_1"
            assert main_comment.text == "Great video!"
            assert main_comment.author == "User1"
            assert main_comment.is_author_reply == False
            assert main_comment.parent_id is None

            author_reply = comments[1]
            assert author_reply.id == "reply_1"
            assert author_reply.text == "Thanks!"
            assert author_reply.author == "Test Channel"
            assert author_reply.is_author_reply == True
            assert author_reply.parent_id == "comment_1"

    @pytest.mark.asyncio
    async def test_get_comments_disabled(self, extractor):
        """测试评论被禁用的情况"""
        video_info = VideoInfo(
            id="test_id",
            title="Test",
            description="Test",
            duration=100,
            view_count=1000,
            like_count=100,
            channel_id="channel_123",
            channel_title="Test Channel",
            upload_date="2023-01-01T00:00:00Z",
            thumbnail_url="https://example.com/thumb.jpg",
        )

        with patch.object(extractor, "get_video_info", return_value=video_info):
            mock_error = HttpError(
                resp=Mock(status=403),
                content=b'{"error": {"errors": [{"reason": "commentsDisabled"}]}}',
            )

            mock_request = Mock()
            mock_request.execute.side_effect = mock_error
            extractor.youtube_api.commentThreads.return_value.list.return_value = (
                mock_request
            )

            comments = await extractor.get_comments("test_id")
            assert comments == []


class TestDurationParsing:
    """测试时长解析功能"""

    def test_parse_duration_hours_minutes_seconds(self, extractor):
        """测试完整时长格式"""
        duration = extractor._parse_duration("PT1H30M45S")
        assert duration == 5445  # 1*3600 + 30*60 + 45

    def test_parse_duration_minutes_seconds(self, extractor):
        """测试分钟秒格式"""
        duration = extractor._parse_duration("PT5M30S")
        assert duration == 330  # 5*60 + 30

    def test_parse_duration_seconds_only(self, extractor):
        """测试仅秒格式"""
        duration = extractor._parse_duration("PT45S")
        assert duration == 45

    def test_parse_duration_invalid(self, extractor):
        """测试无效格式"""
        duration = extractor._parse_duration("INVALID")
        assert duration == 0


class TestFileCleanup:
    """测试文件清理功能"""

    def test_cleanup_audio_file(self, extractor):
        """测试音频文件清理"""
        test_file = "/tmp/test_audio.wav"

        with patch("os.path.exists") as mock_exists, patch("os.remove") as mock_remove:

            mock_exists.return_value = True
            extractor.cleanup_audio_file(test_file)

            mock_exists.assert_called_once_with(test_file)
            mock_remove.assert_called_once_with(test_file)

    def test_cleanup_video_files(self, extractor):
        """测试视频文件清理"""
        with patch("app.services.youtube_extractor.storage_manager") as mock_storage:
            mock_storage.cleanup_audio_file.return_value = True

            result = extractor.cleanup_video_files("test_id")

            assert result == True
            mock_storage.cleanup_audio_file.assert_called_once_with("test_id")


class TestInitialization:
    """测试初始化功能"""

    def test_init_without_api_key(self):
        """测试没有API密钥的初始化"""
        with patch("app.services.youtube_extractor.settings") as mock_settings:
            mock_settings.youtube_api_key = None

            with pytest.raises(ValidationError, match="YouTube API key is required"):
                YouTubeExtractor()

    def test_init_creates_directories(self):
        """测试初始化创建目录"""
        with (
            patch("app.services.youtube_extractor.settings") as mock_settings,
            patch("app.services.youtube_extractor.build") as mock_build,
            patch("os.makedirs") as mock_makedirs,
        ):

            mock_settings.youtube_api_key = "test_key"
            mock_settings.storage_path = "/tmp/test"
            mock_build.return_value = Mock()

            YouTubeExtractor()

            mock_makedirs.assert_called_once_with("/tmp/test/audio", exist_ok=True)
