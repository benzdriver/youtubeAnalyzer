import openai
import logging
import asyncio
import re
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from collections import Counter

from app.core.config import settings
from app.utils.exceptions import AnalysisError


@dataclass
class CommentTheme:
    theme: str
    keywords: List[str]
    comment_count: int
    sentiment_distribution: Dict[str, int]


@dataclass
class AuthorEngagement:
    total_replies: int
    reply_rate: float
    avg_response_time: Optional[float]
    sentiment_in_replies: Dict[str, int]
    engagement_quality: float


@dataclass
class CommentInsights:
    total_comments: int
    sentiment_distribution: Dict[str, int]
    main_themes: List[CommentTheme]
    author_engagement: AuthorEngagement
    top_comments: List[Dict[str, Any]]
    spam_detection: Dict[str, Any]
    engagement_metrics: Dict[str, Any]
    recommendations: List[str]


class CommentAnalyzer:
    """评论分析器"""

    def __init__(self):
        if not settings.openai_api_key:
            raise AnalysisError("OpenAI API key is required for comment analysis")

        self.client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = "gpt-4"

    async def analyze_comments(
        self,
        comments_data: List[Dict[str, Any]],
        video_info: Dict[str, Any],
    ) -> CommentInsights:
        """分析评论数据"""
        try:
            if not comments_data:
                return self._empty_insights()

            processed_comments = self._preprocess_comments(comments_data)

            tasks = [
                self._analyze_sentiment_distribution(processed_comments),
                self._extract_themes(processed_comments),
                self._analyze_author_engagement(processed_comments, video_info),
                self._identify_top_comments(processed_comments),
                self._detect_spam(processed_comments),
                self._calculate_engagement_metrics(processed_comments, video_info),
            ]

            results = await asyncio.gather(*tasks)

            (
                sentiment_dist,
                themes,
                author_engagement,
                top_comments,
                spam_detection,
                engagement_metrics,
            ) = results

            recommendations = await self._generate_recommendations(
                sentiment_dist,
                themes,
                author_engagement,
                engagement_metrics,
            )

            return CommentInsights(
                total_comments=len(processed_comments),
                sentiment_distribution=sentiment_dist,
                main_themes=themes,
                author_engagement=author_engagement,
                top_comments=top_comments,
                spam_detection=spam_detection,
                engagement_metrics=engagement_metrics,
                recommendations=recommendations,
            )

        except Exception as e:
            logging.error(f"Comment analysis failed: {e}")
            raise AnalysisError(f"评论分析失败: {e}")

    def _preprocess_comments(
        self, comments_data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """预处理评论数据"""
        processed = []

        for comment in comments_data:
            clean_text = self._clean_comment_text(comment.get("text", ""))

            if len(clean_text.strip()) < 3:  # 跳过过短的评论
                continue

            processed_comment = {
                "id": comment.get("id", ""),
                "text": clean_text,
                "author": comment.get("author", ""),
                "author_channel_id": comment.get("author_channel_id", ""),
                "like_count": comment.get("like_count", 0),
                "reply_count": comment.get("reply_count", 0),
                "published_at": comment.get("published_at", ""),
                "is_author_reply": comment.get("is_author_reply", False),
                "parent_id": comment.get("parent_id"),
            }
            processed.append(processed_comment)

        return processed

    def _clean_comment_text(self, text: str) -> str:
        """清理评论文本"""
        url_pattern = (
            r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|"
            r"(?:%[0-9a-fA-F][0-9a-fA-F]))+"
        )
        text = re.sub(url_pattern, "", text)

        text = re.sub(r"(.)\1{3,}", r"\1\1\1", text)

        text = re.sub(r"\s+", " ", text)

        return text.strip()

    async def _analyze_sentiment_distribution(
        self, comments: List[Dict]
    ) -> Dict[str, int]:
        """分析情感分布"""
        try:
            sample_size = min(50, len(comments))
            sample_comments = comments[:sample_size]

            comment_texts = [c["text"] for c in sample_comments]

            prompt = f"""
            分析以下评论的情感倾向，返回JSON格式：
            {{
                "positive": 正面评论数量,
                "negative": 负面评论数量,
                "neutral": 中性评论数量
            }}
            
            评论列表：
            {chr(10).join([f"{i+1}. {text}" for i, text in enumerate(comment_texts)])}
            """

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
            )

            result = self._parse_json_response(response.choices[0].message.content)

            total_analyzed = sum(result.values())
            if total_analyzed > 0:
                scale_factor = len(comments) / total_analyzed
                return {key: int(value * scale_factor) for key, value in result.items()}

            return {"positive": 0, "negative": 0, "neutral": len(comments)}

        except Exception as e:
            logging.error(f"Sentiment analysis failed: {e}")
            return {"positive": 0, "negative": 0, "neutral": len(comments)}

    async def _extract_themes(self, comments: List[Dict]) -> List[CommentTheme]:
        """提取主题"""
        try:
            sample_size = min(100, len(comments))
            sample_comments = comments[:sample_size]

            comment_texts = [c["text"] for c in sample_comments]

            prompt = f"""
            分析以下评论，提取主要讨论主题，返回JSON格式：
            {{
                "themes": [
                    {{
                        "theme": "主题名称",
                        "keywords": ["关键词1", "关键词2"],
                        "comment_count": 相关评论数量
                    }}
                ]
            }}
            
            评论列表：
            {chr(10).join([f"{i+1}. {text}" for i, text in enumerate(comment_texts)])}
            """

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
            )

            result = self._parse_json_response(response.choices[0].message.content)

            themes = []
            for theme_data in result.get("themes", []):
                theme = CommentTheme(
                    theme=theme_data.get("theme", ""),
                    keywords=theme_data.get("keywords", []),
                    comment_count=theme_data.get("comment_count", 0),
                    sentiment_distribution={"positive": 0, "negative": 0, "neutral": 0},
                )
                themes.append(theme)

            return themes[:5]  # 返回前5个主题

        except Exception as e:
            logging.error(f"Theme extraction failed: {e}")
            return []

    async def _analyze_author_engagement(
        self, comments: List[Dict], video_info: Dict
    ) -> AuthorEngagement:
        """分析作者互动情况"""
        try:
            author_replies = [c for c in comments if c.get("is_author_reply", False)]

            total_replies = len(author_replies)
            total_comments = len(
                [c for c in comments if not c.get("is_author_reply", False)]
            )
            reply_rate = total_replies / max(total_comments, 1)

            sentiment_in_replies = {"positive": 0, "negative": 0, "neutral": 0}
            if author_replies:
                reply_texts = [r["text"] for r in author_replies[:20]]  # 分析前20条回复

                prompt = f"""
                分析作者回复的情感倾向，返回JSON格式：
                {{
                    "positive": 正面回复数量,
                    "negative": 负面回复数量,
                    "neutral": 中性回复数量
                }}
                
                作者回复：
                {chr(10).join([f"{i+1}. {text}" for i, text in enumerate(reply_texts)])}
                """

                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.1,
                )

                sentiment_in_replies = self._parse_json_response(
                    response.choices[0].message.content
                )

            engagement_quality = self._calculate_engagement_quality(
                reply_rate, total_replies, sentiment_in_replies
            )

            return AuthorEngagement(
                total_replies=total_replies,
                reply_rate=reply_rate,
                avg_response_time=None,  # 需要时间戳计算
                sentiment_in_replies=sentiment_in_replies,
                engagement_quality=engagement_quality,
            )

        except Exception as e:
            logging.error(f"Author engagement analysis failed: {e}")
            return AuthorEngagement(
                total_replies=0,
                reply_rate=0.0,
                avg_response_time=None,
                sentiment_in_replies={"positive": 0, "negative": 0, "neutral": 0},
                engagement_quality=0.0,
            )

    def _calculate_engagement_quality(
        self, reply_rate: float, total_replies: int, sentiment_dist: Dict[str, int]
    ) -> float:
        """计算互动质量分数"""
        base_score = min(reply_rate * 100, 50)  # 最高50分

        reply_bonus = min(total_replies * 2, 30)  # 最高30分

        total_sentiment = sum(sentiment_dist.values())
        if total_sentiment > 0:
            positive_ratio = sentiment_dist.get("positive", 0) / total_sentiment
            sentiment_bonus = positive_ratio * 20  # 最高20分
        else:
            sentiment_bonus = 0

        return min(base_score + reply_bonus + sentiment_bonus, 100)

    async def _identify_top_comments(
        self, comments: List[Dict]
    ) -> List[Dict[str, Any]]:
        """识别热门评论"""
        try:
            sorted_comments = sorted(
                comments, key=lambda x: x.get("like_count", 0), reverse=True
            )

            top_comments = []
            for comment in sorted_comments[:10]:  # 取前10条
                top_comments.append(
                    {
                        "id": comment["id"],
                        "text": (
                            comment["text"][:200] + "..."
                            if len(comment["text"]) > 200
                            else comment["text"]
                        ),
                        "author": comment["author"],
                        "like_count": comment["like_count"],
                        "is_author_reply": comment.get("is_author_reply", False),
                    }
                )

            return top_comments

        except Exception as e:
            logging.error(f"Top comments identification failed: {e}")
            return []

    async def _detect_spam(self, comments: List[Dict]) -> Dict[str, Any]:
        """检测垃圾评论"""
        try:
            spam_indicators = {
                "duplicate_comments": 0,
                "suspicious_patterns": 0,
                "spam_ratio": 0.0,
            }

            text_counts = Counter([c["text"] for c in comments])
            duplicates = sum(1 for count in text_counts.values() if count > 1)
            spam_indicators["duplicate_comments"] = duplicates

            suspicious_patterns = [
                r"(check out|visit|click).*(link|channel)",
                r"(subscribe|follow).*(back|me)",
                r"(free|win|prize|gift).*(click|link)",
                r"(bot|spam|fake)",
            ]

            suspicious_count = 0
            for comment in comments:
                text = comment["text"].lower()
                for pattern in suspicious_patterns:
                    if re.search(pattern, text):
                        suspicious_count += 1
                        break

            spam_indicators["suspicious_patterns"] = suspicious_count
            spam_indicators["spam_ratio"] = suspicious_count / max(len(comments), 1)

            return spam_indicators

        except Exception as e:
            logging.error(f"Spam detection failed: {e}")
            return {
                "duplicate_comments": 0,
                "suspicious_patterns": 0,
                "spam_ratio": 0.0,
            }

    async def _calculate_engagement_metrics(
        self, comments: List[Dict], video_info: Dict
    ) -> Dict[str, Any]:
        """计算互动指标"""
        try:
            total_comments = len(comments)
            total_likes = sum(c.get("like_count", 0) for c in comments)
            avg_likes_per_comment = total_likes / max(total_comments, 1)

            comments_with_replies = len(
                [c for c in comments if c.get("reply_count", 0) > 0]
            )
            reply_engagement_rate = comments_with_replies / max(total_comments, 1)

            view_count = video_info.get("view_count", 1)
            comment_to_view_ratio = total_comments / view_count if view_count > 0 else 0

            return {
                "total_comments": total_comments,
                "total_likes": total_likes,
                "avg_likes_per_comment": round(avg_likes_per_comment, 2),
                "reply_engagement_rate": round(reply_engagement_rate, 3),
                "comment_to_view_ratio": round(comment_to_view_ratio, 6),
                "engagement_score": self._calculate_overall_engagement_score(
                    comment_to_view_ratio, reply_engagement_rate, avg_likes_per_comment
                ),
            }

        except Exception as e:
            logging.error(f"Engagement metrics calculation failed: {e}")
            return {
                "total_comments": len(comments),
                "total_likes": 0,
                "avg_likes_per_comment": 0,
                "reply_engagement_rate": 0,
                "comment_to_view_ratio": 0,
                "engagement_score": 0,
            }

    def _calculate_overall_engagement_score(
        self, comment_ratio: float, reply_rate: float, avg_likes: float
    ) -> float:
        """计算总体互动分数"""
        comment_score = min(comment_ratio * 10000, 50)  # 评论率分数
        reply_score = reply_rate * 30  # 回复率分数
        likes_score = min(avg_likes * 2, 20)  # 点赞分数

        return round(comment_score + reply_score + likes_score, 2)

    async def _generate_recommendations(
        self,
        sentiment_dist: Dict[str, int],
        themes: List[CommentTheme],
        author_engagement: AuthorEngagement,
        engagement_metrics: Dict[str, Any],
    ) -> List[str]:
        """生成改进建议"""
        try:
            recommendations = []

            total_sentiment = sum(sentiment_dist.values())
            if total_sentiment > 0:
                negative_ratio = sentiment_dist.get("negative", 0) / total_sentiment
                if negative_ratio > 0.3:
                    recommendations.append(
                        "负面评论较多，建议关注观众反馈并改进内容质量"
                    )
                elif negative_ratio < 0.1:
                    recommendations.append("观众反馈非常积极，可以继续保持当前内容风格")

            if author_engagement.reply_rate < 0.1:
                recommendations.append("作者回复率较低，建议增加与观众的互动")
            elif author_engagement.reply_rate > 0.3:
                recommendations.append("作者互动积极，有助于建立良好的社区氛围")

            if engagement_metrics.get("comment_to_view_ratio", 0) < 0.001:
                recommendations.append("评论参与度较低，可以在视频中鼓励观众留言互动")

            if len(themes) > 3:
                recommendations.append("评论话题丰富，说明内容引发了多方面讨论")
            elif len(themes) < 2:
                recommendations.append(
                    "评论话题较为单一，可以尝试在内容中加入更多讨论点"
                )

            return recommendations[:5]  # 最多返回5条建议

        except Exception as e:
            logging.error(f"Recommendation generation failed: {e}")
            return ["评论分析完成，建议关注观众反馈以改进内容质量"]

    def _parse_json_response(self, response_text: str) -> Dict[str, Any]:
        """解析JSON响应"""
        try:
            import json

            start_idx = response_text.find("{")
            end_idx = response_text.rfind("}") + 1

            if start_idx >= 0 and end_idx > start_idx:
                json_str = response_text[start_idx:end_idx]
                return json.loads(json_str)

            return {}

        except Exception as e:
            logging.error(f"JSON parsing failed: {e}")
            return {}

    def _empty_insights(self) -> CommentInsights:
        """返回空的分析结果"""
        return CommentInsights(
            total_comments=0,
            sentiment_distribution={"positive": 0, "negative": 0, "neutral": 0},
            main_themes=[],
            author_engagement=AuthorEngagement(
                total_replies=0,
                reply_rate=0.0,
                avg_response_time=None,
                sentiment_in_replies={"positive": 0, "negative": 0, "neutral": 0},
                engagement_quality=0.0,
            ),
            top_comments=[],
            spam_detection={
                "duplicate_comments": 0,
                "suspicious_patterns": 0,
                "spam_ratio": 0.0,
            },
            engagement_metrics={
                "total_comments": 0,
                "total_likes": 0,
                "avg_likes_per_comment": 0,
                "reply_engagement_rate": 0,
                "comment_to_view_ratio": 0,
                "engagement_score": 0,
            },
            recommendations=["暂无评论数据可供分析"],
        )
