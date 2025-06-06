import pytest
from unittest.mock import Mock, patch

from app.services.comment_analyzer import (
    CommentAnalyzer,
    CommentInsights,
    CommentTheme,
    AuthorEngagement,
)
from app.utils.exceptions import AnalysisError


@pytest.fixture
def analyzer():
    """创建CommentAnalyzer实例"""
    with patch("app.services.comment_analyzer.settings") as mock_settings:
        mock_settings.openai_api_key = "test-api-key"
        return CommentAnalyzer()


@pytest.fixture
def sample_comments():
    """示例评论数据"""
    return [
        {
            "id": "1",
            "text": "Great video! Very helpful and informative.",
            "author": "User1",
            "author_channel_id": "user1_channel",
            "like_count": 15,
            "reply_count": 2,
            "published_at": "2024-01-01T10:00:00Z",
            "is_author_reply": False,
            "parent_id": None,
        },
        {
            "id": "2",
            "text": "Thanks for watching! Glad you found it helpful.",
            "author": "Channel Owner",
            "author_channel_id": "channel123",
            "like_count": 8,
            "reply_count": 0,
            "published_at": "2024-01-01T11:00:00Z",
            "is_author_reply": True,
            "parent_id": "1",
        },
        {
            "id": "3",
            "text": "This is terrible content. Waste of time.",
            "author": "User2",
            "author_channel_id": "user2_channel",
            "like_count": 1,
            "reply_count": 0,
            "published_at": "2024-01-01T12:00:00Z",
            "is_author_reply": False,
            "parent_id": None,
        },
        {
            "id": "4",
            "text": "Check out my channel! Subscribe for more content!",
            "author": "SpamUser",
            "author_channel_id": "spam_channel",
            "like_count": 0,
            "reply_count": 0,
            "published_at": "2024-01-01T13:00:00Z",
            "is_author_reply": False,
            "parent_id": None,
        },
    ]


@pytest.fixture
def sample_video_info():
    """示例视频信息"""
    return {
        "id": "test_video_id",
        "title": "Test Video",
        "channel_id": "channel123",
        "channel_title": "Test Channel",
        "view_count": 10000,
        "like_count": 500,
        "duration": 600,
    }


class TestCommentAnalyzer:
    """CommentAnalyzer测试类"""

    @pytest.mark.asyncio
    async def test_analyze_comments_success(
        self, analyzer, sample_comments, sample_video_info
    ):
        """测试成功的评论分析"""
        mock_sentiment_response = Mock()
        mock_sentiment_response.choices = [Mock()]
        mock_sentiment_response.choices[0].message.content = (
            '{"positive": 2, "negative": 1, "neutral": 1}'
        )

        mock_themes_response = Mock()
        mock_themes_response.choices = [Mock()]
        mock_themes_response.choices[
            0
        ].message.content = """
        {
            "themes": [
                {
                    "theme": "Content Quality",
                    "keywords": ["helpful", "informative"],
                    "comment_count": 2
                }
            ]
        }
        """

        mock_author_sentiment_response = Mock()
        mock_author_sentiment_response.choices = [Mock()]
        mock_author_sentiment_response.choices[0].message.content = (
            '{"positive": 1, "negative": 0, "neutral": 0}'
        )

        with patch.object(analyzer.client.chat.completions, "create") as mock_create:
            mock_create.side_effect = [
                mock_sentiment_response,
                mock_themes_response,
                mock_author_sentiment_response,
            ]

            result = await analyzer.analyze_comments(sample_comments, sample_video_info)

            assert isinstance(result, CommentInsights)
            assert result.total_comments == 4
            assert "positive" in result.sentiment_distribution
            assert "negative" in result.sentiment_distribution
            assert "neutral" in result.sentiment_distribution
            assert len(result.main_themes) >= 0
            assert result.author_engagement.total_replies == 1
            assert len(result.top_comments) <= 10
            assert "duplicate_comments" in result.spam_detection
            assert "engagement_score" in result.engagement_metrics
            assert len(result.recommendations) > 0

    @pytest.mark.asyncio
    async def test_analyze_empty_comments(self, analyzer, sample_video_info):
        """测试空评论列表"""
        result = await analyzer.analyze_comments([], sample_video_info)

        assert isinstance(result, CommentInsights)
        assert result.total_comments == 0
        assert result.sentiment_distribution == {
            "positive": 0,
            "negative": 0,
            "neutral": 0,
        }
        assert len(result.main_themes) == 0
        assert result.author_engagement.total_replies == 0
        assert len(result.top_comments) == 0
        assert result.recommendations == ["暂无评论数据可供分析"]

    @pytest.mark.asyncio
    async def test_analyze_comments_api_error(
        self, analyzer, sample_comments, sample_video_info
    ):
        """测试OpenAI API错误处理"""
        with patch.object(analyzer.client.chat.completions, "create") as mock_create:
            mock_create.side_effect = Exception("API Error")

            with pytest.raises(AnalysisError):
                await analyzer.analyze_comments(sample_comments, sample_video_info)

    def test_preprocess_comments(self, analyzer, sample_comments):
        """测试评论预处理"""
        processed = analyzer._preprocess_comments(sample_comments)

        assert len(processed) == 4
        assert all("text" in comment for comment in processed)
        assert all("author" in comment for comment in processed)
        assert all("like_count" in comment for comment in processed)

    def test_clean_comment_text(self, analyzer):
        """测试评论文本清理"""
        dirty_text = (
            "Great    video!!! Check out https://example.com for more content!!!"
        )
        clean_text = analyzer._clean_comment_text(dirty_text)

        assert "https://example.com" not in clean_text
        assert "Great video!!!" in clean_text
        assert clean_text.count("!") <= 3  # 重复字符被限制

    @pytest.mark.asyncio
    async def test_sentiment_analysis(self, analyzer, sample_comments):
        """测试情感分析"""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = (
            '{"positive": 2, "negative": 1, "neutral": 1}'
        )

        with patch.object(
            analyzer.client.chat.completions, "create", return_value=mock_response
        ):
            result = await analyzer._analyze_sentiment_distribution(sample_comments)

            assert isinstance(result, dict)
            assert "positive" in result
            assert "negative" in result
            assert "neutral" in result
            assert sum(result.values()) == len(sample_comments)

    @pytest.mark.asyncio
    async def test_theme_extraction(self, analyzer, sample_comments):
        """测试主题提取"""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[
            0
        ].message.content = """
        {
            "themes": [
                {
                    "theme": "Video Quality",
                    "keywords": ["great", "helpful"],
                    "comment_count": 2
                }
            ]
        }
        """

        with patch.object(
            analyzer.client.chat.completions, "create", return_value=mock_response
        ):
            result = await analyzer._extract_themes(sample_comments)

            assert isinstance(result, list)
            assert len(result) <= 5
            if result:
                assert isinstance(result[0], CommentTheme)
                assert hasattr(result[0], "theme")
                assert hasattr(result[0], "keywords")

    @pytest.mark.asyncio
    async def test_author_engagement_analysis(
        self, analyzer, sample_comments, sample_video_info
    ):
        """测试作者互动分析"""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = (
            '{"positive": 1, "negative": 0, "neutral": 0}'
        )

        with patch.object(
            analyzer.client.chat.completions, "create", return_value=mock_response
        ):
            result = await analyzer._analyze_author_engagement(
                sample_comments, sample_video_info
            )

            assert isinstance(result, AuthorEngagement)
            assert result.total_replies == 1  # 一条作者回复
            assert 0 <= result.reply_rate <= 1
            assert 0 <= result.engagement_quality <= 100
            assert isinstance(result.sentiment_in_replies, dict)

    @pytest.mark.asyncio
    async def test_top_comments_identification(self, analyzer, sample_comments):
        """测试热门评论识别"""
        result = await analyzer._identify_top_comments(sample_comments)

        assert isinstance(result, list)
        assert len(result) <= 10
        if result:
            assert result[0]["like_count"] >= result[-1]["like_count"]
            assert "text" in result[0]
            assert "author" in result[0]

    @pytest.mark.asyncio
    async def test_spam_detection(self, analyzer, sample_comments):
        """测试垃圾评论检测"""
        result = await analyzer._detect_spam(sample_comments)

        assert isinstance(result, dict)
        assert "duplicate_comments" in result
        assert "suspicious_patterns" in result
        assert "spam_ratio" in result
        assert 0 <= result["spam_ratio"] <= 1
        assert result["suspicious_patterns"] >= 1

    @pytest.mark.asyncio
    async def test_engagement_metrics_calculation(
        self, analyzer, sample_comments, sample_video_info
    ):
        """测试互动指标计算"""
        result = await analyzer._calculate_engagement_metrics(
            sample_comments, sample_video_info
        )

        assert isinstance(result, dict)
        assert "total_comments" in result
        assert "total_likes" in result
        assert "avg_likes_per_comment" in result
        assert "reply_engagement_rate" in result
        assert "comment_to_view_ratio" in result
        assert "engagement_score" in result

        assert result["total_comments"] == len(sample_comments)
        assert result["total_likes"] == sum(c["like_count"] for c in sample_comments)

    def test_calculate_engagement_quality(self, analyzer):
        """测试互动质量分数计算"""
        sentiment_dist = {"positive": 8, "negative": 1, "neutral": 1}
        quality_score = analyzer._calculate_engagement_quality(0.2, 10, sentiment_dist)

        assert 0 <= quality_score <= 100
        assert isinstance(quality_score, float)

    def test_calculate_overall_engagement_score(self, analyzer):
        """测试总体互动分数计算"""
        score = analyzer._calculate_overall_engagement_score(0.001, 0.3, 5.0)

        assert isinstance(score, float)
        assert score >= 0

    @pytest.mark.asyncio
    async def test_generate_recommendations(self, analyzer):
        """测试建议生成"""
        sentiment_dist = {"positive": 5, "negative": 3, "neutral": 2}
        themes = [
            CommentTheme("Quality", ["good", "great"], 3, {}),
            CommentTheme("Content", ["helpful", "useful"], 2, {}),
        ]
        author_engagement = AuthorEngagement(2, 0.2, None, {"positive": 2}, 75.0)
        engagement_metrics = {"comment_to_view_ratio": 0.001, "engagement_score": 50}

        result = await analyzer._generate_recommendations(
            sentiment_dist, themes, author_engagement, engagement_metrics
        )

        assert isinstance(result, list)
        assert len(result) <= 5
        assert all(isinstance(rec, str) for rec in result)

    def test_parse_json_response(self, analyzer):
        """测试JSON响应解析"""
        response = '{"positive": 5, "negative": 2}'
        result = analyzer._parse_json_response(response)
        assert result == {"positive": 5, "negative": 2}

        response = (
            'Here is the analysis: {"positive": 3, "negative": 1} Hope this helps!'
        )
        result = analyzer._parse_json_response(response)
        assert result == {"positive": 3, "negative": 1}

        response = "This is not JSON"
        result = analyzer._parse_json_response(response)
        assert result == {}

    def test_empty_insights(self, analyzer):
        """测试空分析结果"""
        result = analyzer._empty_insights()

        assert isinstance(result, CommentInsights)
        assert result.total_comments == 0
        assert result.sentiment_distribution == {
            "positive": 0,
            "negative": 0,
            "neutral": 0,
        }
        assert len(result.main_themes) == 0
        assert result.author_engagement.total_replies == 0
        assert result.recommendations == ["暂无评论数据可供分析"]

    def test_analyzer_initialization_without_api_key(self):
        """测试没有API密钥时的初始化"""
        with patch("app.services.comment_analyzer.settings") as mock_settings:
            mock_settings.openai_api_key = None

            with pytest.raises(AnalysisError, match="OpenAI API key is required"):
                CommentAnalyzer()


class TestCommentAnalyzerIntegration:
    """CommentAnalyzer集成测试"""

    @pytest.mark.asyncio
    async def test_full_analysis_workflow(
        self, analyzer, sample_comments, sample_video_info
    ):
        """测试完整的分析工作流程"""
        mock_responses = [
            Mock(
                choices=[
                    Mock(
                        message=Mock(
                            content='{"positive": 2, "negative": 1, "neutral": 1}'
                        )
                    )
                ]
            ),
            Mock(
                choices=[
                    Mock(
                        message=Mock(
                            content='{"themes": [{"theme": "Quality", '
                            '"keywords": ["good"], "comment_count": 1}]}'
                        )
                    )
                ]
            ),
            Mock(
                choices=[
                    Mock(
                        message=Mock(
                            content='{"positive": 1, "negative": 0, "neutral": 0}'
                        )
                    )
                ]
            ),
        ]

        with patch.object(analyzer.client.chat.completions, "create") as mock_create:
            mock_create.side_effect = mock_responses

            result = await analyzer.analyze_comments(sample_comments, sample_video_info)

            assert isinstance(result, CommentInsights)
            assert result.total_comments > 0
            assert isinstance(result.sentiment_distribution, dict)
            assert isinstance(result.main_themes, list)
            assert isinstance(result.author_engagement, AuthorEngagement)
            assert isinstance(result.top_comments, list)
            assert isinstance(result.spam_detection, dict)
            assert isinstance(result.engagement_metrics, dict)
            assert isinstance(result.recommendations, list)

            assert mock_create.call_count >= 2  # 至少调用情感分析和主题提取
