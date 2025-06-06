# 评论分析接口契约

**提供方**: TASK_07 (评论分析模块)  
**使用方**: TASK_08 (分析编排器)  
**版本**: v1.0.0

## 概述

定义评论分析模块的接口规范，包括评论情感分析、主题提取、作者互动分析和观众反馈洞察。

## 数据模型定义

### CommentInsights 数据结构

```python
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class SentimentType(Enum):
    """情感类型"""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"

class CommentSentiment(BaseModel):
    """评论情感分析"""
    comment_id: str
    sentiment: SentimentType
    confidence: float  # 0.0-1.0
    sentiment_score: float  # -1.0 to 1.0
    emotional_keywords: List[str] = []
    
    def is_strong_sentiment(self) -> bool:
        """是否为强烈情感"""
        return abs(self.sentiment_score) > 0.7

class ThemeCluster(BaseModel):
    """主题聚类"""
    theme_id: str
    theme_name: str
    description: str
    comment_count: int
    keywords: List[str]
    representative_comments: List[str]  # 代表性评论
    sentiment_distribution: Dict[str, float]
    
    def get_dominant_sentiment(self) -> str:
        """获取主导情感"""
        return max(self.sentiment_distribution, key=self.sentiment_distribution.get)

class AuthorEngagement(BaseModel):
    """作者互动分析"""
    total_author_replies: int
    reply_rate: float  # 回复率 0.0-1.0
    avg_reply_time: Optional[float] = None  # 平均回复时间（小时）
    reply_sentiment_distribution: Dict[str, float]
    engagement_quality_score: float  # 互动质量分数 0.0-1.0
    
    # 作者回复特征
    author_reply_themes: List[str]
    author_tone: str  # 作者语调：professional, friendly, defensive等
    
    def is_highly_engaged(self) -> bool:
        """是否高度参与"""
        return self.reply_rate > 0.1 and self.engagement_quality_score > 0.7

class AudienceInsights(BaseModel):
    """观众洞察"""
    audience_sentiment_summary: str
    engagement_level: str  # high, medium, low
    controversial_topics: List[str]
    positive_feedback_themes: List[str]
    negative_feedback_themes: List[str]
    constructive_criticism: List[str]
    
    # 观众行为模式
    comment_patterns: Dict[str, Any]
    peak_engagement_times: List[str]
    audience_demographics_hints: Dict[str, Any]

class SpamDetection(BaseModel):
    """垃圾评论检测"""
    total_spam_count: int
    spam_ratio: float  # 垃圾评论比例
    spam_patterns: List[str]
    bot_detection_results: Dict[str, Any]
    
    def is_spam_heavy(self) -> bool:
        """是否垃圾评论较多"""
        return self.spam_ratio > 0.2

class CommentInsights(BaseModel):
    """评论分析结果"""
    # 基本信息
    video_id: str
    analysis_id: str
    total_comments: int
    analyzed_comments: int
    
    # 情感分析
    sentiment_distribution: Dict[str, float]  # 整体情感分布
    comment_sentiments: List[CommentSentiment]
    sentiment_trends: List[Dict[str, Any]]  # 情感趋势
    
    # 主题分析
    theme_clusters: List[ThemeCluster]
    trending_topics: List[str]
    topic_evolution: List[Dict[str, Any]]  # 话题演变
    
    # 作者互动
    author_engagement: AuthorEngagement
    
    # 观众洞察
    audience_insights: AudienceInsights
    
    # 质量控制
    spam_detection: SpamDetection
    
    # 综合评估
    overall_reception: str  # 整体接受度
    community_health_score: float  # 社区健康度 0.0-1.0
    engagement_quality: str  # 互动质量评级
    
    # 元数据
    analysis_model: str
    analysis_version: str
    processing_time: float
    confidence_score: float
    created_at: datetime
    
    def get_positive_ratio(self) -> float:
        """获取积极评论比例"""
        return self.sentiment_distribution.get('positive', 0.0)
    
    def get_top_themes(self, limit: int = 5) -> List[ThemeCluster]:
        """获取热门主题"""
        return sorted(self.theme_clusters, key=lambda x: x.comment_count, reverse=True)[:limit]
    
    def is_controversial(self) -> bool:
        """是否存在争议"""
        negative_ratio = self.sentiment_distribution.get('negative', 0.0)
        return negative_ratio > 0.3 and len(self.audience_insights.controversial_topics) > 0
    
    def to_summary_dict(self) -> Dict[str, Any]:
        """转换为摘要字典"""
        return {
            "total_comments": self.total_comments,
            "sentiment_summary": {
                "positive": f"{self.get_positive_ratio()*100:.1f}%",
                "negative": f"{self.sentiment_distribution.get('negative', 0.0)*100:.1f}%",
                "neutral": f"{self.sentiment_distribution.get('neutral', 0.0)*100:.1f}%"
            },
            "author_engagement": {
                "reply_rate": f"{self.author_engagement.reply_rate*100:.1f}%",
                "engagement_quality": self.author_engagement.engagement_quality_score
            },
            "top_themes": [theme.theme_name for theme in self.get_top_themes(3)],
            "overall_reception": self.overall_reception,
            "community_health": self.community_health_score
        }
```

## 服务接口定义

### 评论分析器接口

```python
from abc import ABC, abstractmethod

class CommentAnalyzer(ABC):
    """评论分析器接口"""
    
    @abstractmethod
    async def analyze_comments(self, comment_data: 'CommentData', 
                             video_info: 'VideoInfo',
                             options: dict = None) -> CommentInsights:
        """分析评论数据"""
        pass
    
    @abstractmethod
    async def analyze_sentiment(self, comments: List['Comment']) -> List[CommentSentiment]:
        """分析评论情感"""
        pass
    
    @abstractmethod
    async def extract_themes(self, comments: List['Comment']) -> List[ThemeCluster]:
        """提取评论主题"""
        pass
    
    @abstractmethod
    async def analyze_author_engagement(self, comments: List['Comment'], 
                                      channel_id: str) -> AuthorEngagement:
        """分析作者互动"""
        pass
    
    @abstractmethod
    async def detect_spam(self, comments: List['Comment']) -> SpamDetection:
        """检测垃圾评论"""
        pass
    
    @abstractmethod
    async def generate_audience_insights(self, comment_insights: CommentInsights) -> AudienceInsights:
        """生成观众洞察"""
        pass
```

### LLM评论分析器实现

```python
import openai
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np

class LLMCommentAnalyzer(CommentAnalyzer):
    """基于LLM的评论分析器"""
    
    def __init__(self, model_name: str = "gpt-4", api_key: str = None):
        self.model_name = model_name
        self.client = openai.AsyncOpenAI(api_key=api_key)
        self.vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
    
    async def analyze_comments(self, comment_data: 'CommentData', 
                             video_info: 'VideoInfo',
                             options: dict = None) -> CommentInsights:
        """分析评论数据"""
        options = options or {}
        start_time = time.time()
        
        try:
            # 过滤和预处理评论
            valid_comments = self._filter_valid_comments(comment_data.comments)
            
            # 并行执行各项分析
            tasks = [
                self.analyze_sentiment(valid_comments),
                self.extract_themes(valid_comments),
                self.analyze_author_engagement(valid_comments, video_info.channel_id),
                self.detect_spam(comment_data.comments)
            ]
            
            comment_sentiments, theme_clusters, author_engagement, spam_detection = await asyncio.gather(*tasks)
            
            # 计算情感分布
            sentiment_distribution = self._calculate_sentiment_distribution(comment_sentiments)
            
            # 生成观众洞察
            audience_insights = await self._generate_audience_insights(
                comment_sentiments, theme_clusters, author_engagement
            )
            
            # 综合评估
            overall_reception = self._assess_overall_reception(sentiment_distribution, theme_clusters)
            community_health_score = self._calculate_community_health(
                sentiment_distribution, spam_detection, author_engagement
            )
            
            processing_time = time.time() - start_time
            
            return CommentInsights(
                video_id=video_info.id,
                analysis_id=str(uuid.uuid4()),
                total_comments=len(comment_data.comments),
                analyzed_comments=len(valid_comments),
                sentiment_distribution=sentiment_distribution,
                comment_sentiments=comment_sentiments,
                sentiment_trends=await self._analyze_sentiment_trends(comment_sentiments),
                theme_clusters=theme_clusters,
                trending_topics=self._extract_trending_topics(theme_clusters),
                topic_evolution=[],  # 简化实现
                author_engagement=author_engagement,
                audience_insights=audience_insights,
                spam_detection=spam_detection,
                overall_reception=overall_reception,
                community_health_score=community_health_score,
                engagement_quality=self._assess_engagement_quality(author_engagement),
                analysis_model=self.model_name,
                analysis_version="1.0.0",
                processing_time=processing_time,
                confidence_score=self._calculate_confidence_score(len(valid_comments)),
                created_at=datetime.utcnow()
            )
            
        except Exception as e:
            raise CommentAnalysisError(f"评论分析失败: {e}")
    
    async def analyze_sentiment(self, comments: List['Comment']) -> List[CommentSentiment]:
        """分析评论情感"""
        sentiments = []
        
        # 批量处理评论
        batch_size = 20
        for i in range(0, len(comments), batch_size):
            batch = comments[i:i + batch_size]
            batch_texts = [comment.text for comment in batch]
            
            prompt = f"""
            请分析以下评论的情感倾向，为每条评论返回情感类型(positive/negative/neutral)和分数(-1到1)：

            评论列表:
            {json.dumps(batch_texts, ensure_ascii=False)}

            返回JSON格式:
            [
                {{"sentiment": "positive", "score": 0.8, "keywords": ["好", "棒"]}},
                {{"sentiment": "negative", "score": -0.6, "keywords": ["差", "糟糕"]}}
            ]
            """
            
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1000,
                temperature=0.2
            )
            
            try:
                batch_results = json.loads(response.choices[0].message.content)
                
                for j, result in enumerate(batch_results):
                    if i + j < len(comments):
                        sentiments.append(CommentSentiment(
                            comment_id=comments[i + j].id,
                            sentiment=SentimentType(result["sentiment"]),
                            confidence=0.8,  # 简化实现
                            sentiment_score=result["score"],
                            emotional_keywords=result.get("keywords", [])
                        ))
                        
            except (json.JSONDecodeError, KeyError, ValueError) as e:
                logger.warning(f"情感分析批次失败: {e}")
                # 使用默认值
                for j in range(len(batch)):
                    if i + j < len(comments):
                        sentiments.append(CommentSentiment(
                            comment_id=comments[i + j].id,
                            sentiment=SentimentType.NEUTRAL,
                            confidence=0.5,
                            sentiment_score=0.0,
                            emotional_keywords=[]
                        ))
        
        return sentiments
    
    async def extract_themes(self, comments: List['Comment']) -> List[ThemeCluster]:
        """提取评论主题"""
        if len(comments) < 5:
            return []
        
        # 提取文本特征
        comment_texts = [comment.text for comment in comments]
        
        try:
            # TF-IDF向量化
            tfidf_matrix = self.vectorizer.fit_transform(comment_texts)
            
            # K-means聚类
            n_clusters = min(8, len(comments) // 5)  # 动态确定聚类数
            kmeans = KMeans(n_clusters=n_clusters, random_state=42)
            cluster_labels = kmeans.fit_predict(tfidf_matrix)
            
            # 为每个聚类生成主题
            themes = []
            feature_names = self.vectorizer.get_feature_names_out()
            
            for cluster_id in range(n_clusters):
                cluster_comments = [comments[i] for i, label in enumerate(cluster_labels) if label == cluster_id]
                
                if len(cluster_comments) < 2:
                    continue
                
                # 获取聚类中心的关键词
                cluster_center = kmeans.cluster_centers_[cluster_id]
                top_indices = cluster_center.argsort()[-10:][::-1]
                keywords = [feature_names[i] for i in top_indices]
                
                # 使用LLM生成主题名称和描述
                theme_name, description = await self._generate_theme_description(
                    cluster_comments[:5], keywords
                )
                
                # 计算情感分布
                sentiment_dist = self._calculate_cluster_sentiment_distribution(cluster_comments)
                
                themes.append(ThemeCluster(
                    theme_id=str(uuid.uuid4()),
                    theme_name=theme_name,
                    description=description,
                    comment_count=len(cluster_comments),
                    keywords=keywords[:5],
                    representative_comments=[c.text for c in cluster_comments[:3]],
                    sentiment_distribution=sentiment_dist
                ))
            
            return sorted(themes, key=lambda x: x.comment_count, reverse=True)
            
        except Exception as e:
            logger.warning(f"主题提取失败: {e}")
            return []
    
    async def analyze_author_engagement(self, comments: List['Comment'], 
                                      channel_id: str) -> AuthorEngagement:
        """分析作者互动"""
        author_replies = [c for c in comments if c.author.id == channel_id]
        total_comments = len(comments)
        
        if total_comments == 0:
            return AuthorEngagement(
                total_author_replies=0,
                reply_rate=0.0,
                engagement_quality_score=0.0,
                author_reply_themes=[],
                author_tone="unknown",
                reply_sentiment_distribution={}
            )
        
        reply_rate = len(author_replies) / total_comments
        
        # 分析作者回复的情感分布
        if author_replies:
            reply_sentiments = await self.analyze_sentiment(author_replies)
            reply_sentiment_dist = self._calculate_sentiment_distribution(reply_sentiments)
            
            # 分析作者语调
            author_tone = await self._analyze_author_tone(author_replies)
            
            # 提取作者回复主题
            author_themes = await self._extract_author_reply_themes(author_replies)
        else:
            reply_sentiment_dist = {}
            author_tone = "unknown"
            author_themes = []
        
        # 计算互动质量分数
        engagement_quality = self._calculate_engagement_quality(
            reply_rate, len(author_replies), reply_sentiment_dist
        )
        
        return AuthorEngagement(
            total_author_replies=len(author_replies),
            reply_rate=reply_rate,
            reply_sentiment_distribution=reply_sentiment_dist,
            engagement_quality_score=engagement_quality,
            author_reply_themes=author_themes,
            author_tone=author_tone
        )
```

## 错误处理规范

### 异常类型定义

```python
class CommentAnalysisError(Exception):
    """评论分析错误基类"""
    pass

class InsufficientDataError(CommentAnalysisError):
    """数据不足错误"""
    pass

class SentimentAnalysisError(CommentAnalysisError):
    """情感分析错误"""
    pass

class ThemeExtractionError(CommentAnalysisError):
    """主题提取错误"""
    pass
```

## 性能要求

### 处理时间限制

- **少量评论 (< 100条)**: < 30秒
- **中等评论 (100-1000条)**: < 60秒
- **大量评论 (> 1000条)**: < 120秒

### 资源使用限制

- **内存使用**: < 1GB per analysis
- **API调用**: < 20 calls per analysis

## 测试用例

### 单元测试

```python
@pytest.mark.asyncio
async def test_analyze_sentiment():
    """测试情感分析"""
    analyzer = LLMCommentAnalyzer()
    
    comments = [
        Mock(id="1", text="这个视频太棒了！", author=Mock(id="user1")),
        Mock(id="2", text="内容很差劲", author=Mock(id="user2"))
    ]
    
    with patch.object(analyzer.client.chat.completions, 'create') as mock_create:
        mock_create.return_value.choices[0].message.content = json.dumps([
            {"sentiment": "positive", "score": 0.8, "keywords": ["棒"]},
            {"sentiment": "negative", "score": -0.6, "keywords": ["差"]}
        ])
        
        sentiments = await analyzer.analyze_sentiment(comments)
        
        assert len(sentiments) == 2
        assert sentiments[0].sentiment == SentimentType.POSITIVE
        assert sentiments[1].sentiment == SentimentType.NEGATIVE
```

## 使用示例

### 基本使用

```python
async def analyze_video_comments(comment_data: CommentData, 
                               video_info: VideoInfo) -> CommentInsights:
    """分析视频评论"""
    analyzer = LLMCommentAnalyzer()
    
    try:
        insights = await analyzer.analyze_comments(comment_data, video_info, {
            'include_spam_detection': True,
            'max_themes': 8,
            'sentiment_threshold': 0.6
        })
        
        return insights
        
    except CommentAnalysisError as e:
        logger.error(f"评论分析失败: {e}")
        raise
```
