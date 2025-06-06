# 内容分析接口契约

**提供方**: TASK_06 (内容分析模块)  
**使用方**: TASK_08 (分析编排器)  
**版本**: v1.0.0

## 概述

定义内容分析模块的接口规范，包括转录文本的深度分析、关键要点提取、主题分析和结构化报告生成。

## 数据模型定义

### ContentInsights 数据结构

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
    MIXED = "mixed"

class KeyPoint(BaseModel):
    """关键要点"""
    id: str
    text: str
    importance_score: float  # 0.0-1.0
    timestamp_start: Optional[float] = None  # 对应视频时间戳
    timestamp_end: Optional[float] = None
    category: Optional[str] = None
    supporting_evidence: List[str] = []
    
    def __str__(self):
        return f"KeyPoint({self.importance_score:.2f}): {self.text[:50]}..."

class TopicAnalysis(BaseModel):
    """主题分析"""
    main_topic: str
    sub_topics: List[str]
    keywords: List[str]
    topic_coherence_score: float  # 0.0-1.0
    topic_distribution: Dict[str, float]  # 主题分布
    
    def get_top_keywords(self, limit: int = 10) -> List[str]:
        """获取顶级关键词"""
        return self.keywords[:limit]

class SentimentAnalysis(BaseModel):
    """情感分析"""
    overall_sentiment: SentimentType
    sentiment_score: float  # -1.0 to 1.0
    sentiment_distribution: Dict[str, float]  # 各情感类型分布
    emotional_arc: List[Dict[str, Any]]  # 情感变化轨迹
    
    def is_positive(self) -> bool:
        return self.overall_sentiment == SentimentType.POSITIVE
    
    def get_sentiment_intensity(self) -> str:
        """获取情感强度描述"""
        abs_score = abs(self.sentiment_score)
        if abs_score >= 0.7:
            return "强烈"
        elif abs_score >= 0.4:
            return "中等"
        else:
            return "轻微"

class StructuralAnalysis(BaseModel):
    """结构分析"""
    sections: List[Dict[str, Any]]  # 内容段落
    narrative_flow: str  # 叙述流程描述
    content_type: str  # 内容类型：教育、娱乐、新闻等
    presentation_style: str  # 表达风格
    
    def get_section_count(self) -> int:
        return len(self.sections)

class QualityMetrics(BaseModel):
    """质量指标"""
    content_depth_score: float  # 内容深度 0.0-1.0
    clarity_score: float  # 清晰度 0.0-1.0
    engagement_score: float  # 参与度 0.0-1.0
    informativeness_score: float  # 信息量 0.0-1.0
    overall_quality_score: float  # 整体质量 0.0-1.0
    
    def get_quality_rating(self) -> str:
        """获取质量等级"""
        if self.overall_quality_score >= 0.8:
            return "优秀"
        elif self.overall_quality_score >= 0.6:
            return "良好"
        elif self.overall_quality_score >= 0.4:
            return "一般"
        else:
            return "较差"

class ContentInsights(BaseModel):
    """内容分析结果"""
    # 基本信息
    video_id: str
    analysis_id: str
    
    # 核心分析结果
    summary: str  # 内容摘要
    key_points: List[KeyPoint]
    topic_analysis: TopicAnalysis
    sentiment_analysis: SentimentAnalysis
    structural_analysis: StructuralAnalysis
    quality_metrics: QualityMetrics
    
    # 深度洞察
    insights: List[str]  # 深度洞察
    recommendations: List[str]  # 改进建议
    target_audience: str  # 目标受众
    content_value: str  # 内容价值评估
    
    # 元数据
    analysis_model: str  # 使用的分析模型
    analysis_version: str
    processing_time: float  # 处理时间（秒）
    confidence_score: float  # 整体置信度 0.0-1.0
    created_at: datetime
    
    def get_top_insights(self, limit: int = 5) -> List[str]:
        """获取顶级洞察"""
        return self.insights[:limit]
    
    def get_actionable_recommendations(self) -> List[str]:
        """获取可执行建议"""
        return [rec for rec in self.recommendations if "建议" in rec or "可以" in rec]
    
    def to_summary_dict(self) -> Dict[str, Any]:
        """转换为摘要字典"""
        return {
            "summary": self.summary,
            "main_topic": self.topic_analysis.main_topic,
            "sentiment": self.sentiment_analysis.overall_sentiment.value,
            "quality_rating": self.quality_metrics.get_quality_rating(),
            "key_points_count": len(self.key_points),
            "insights_count": len(self.insights),
            "confidence": self.confidence_score
        }
```

## 服务接口定义

### 内容分析器接口

```python
from abc import ABC, abstractmethod

class ContentAnalyzer(ABC):
    """内容分析器接口"""
    
    @abstractmethod
    async def analyze_content(self, transcript_result: 'TranscriptResult', 
                            video_info: 'VideoInfo', 
                            options: dict = None) -> ContentInsights:
        """分析视频内容"""
        pass
    
    @abstractmethod
    async def extract_key_points(self, text: str, max_points: int = 10) -> List[KeyPoint]:
        """提取关键要点"""
        pass
    
    @abstractmethod
    async def analyze_topics(self, text: str) -> TopicAnalysis:
        """分析主题"""
        pass
    
    @abstractmethod
    async def analyze_sentiment(self, text: str) -> SentimentAnalysis:
        """分析情感"""
        pass
    
    @abstractmethod
    async def analyze_structure(self, transcript_result: 'TranscriptResult') -> StructuralAnalysis:
        """分析结构"""
        pass
    
    @abstractmethod
    async def calculate_quality_metrics(self, content_insights: ContentInsights) -> QualityMetrics:
        """计算质量指标"""
        pass
```

### LLM内容分析器实现

```python
import openai
from typing import List, Dict, Any
import json
import re

class LLMContentAnalyzer(ContentAnalyzer):
    """基于LLM的内容分析器"""
    
    def __init__(self, model_name: str = "gpt-4", api_key: str = None):
        self.model_name = model_name
        self.client = openai.AsyncOpenAI(api_key=api_key)
    
    async def analyze_content(self, transcript_result: 'TranscriptResult', 
                            video_info: 'VideoInfo', 
                            options: dict = None) -> ContentInsights:
        """分析视频内容"""
        options = options or {}
        start_time = time.time()
        
        try:
            # 并行执行各项分析
            tasks = [
                self._generate_summary(transcript_result.full_text, video_info),
                self.extract_key_points(transcript_result.full_text, options.get('max_key_points', 10)),
                self.analyze_topics(transcript_result.full_text),
                self.analyze_sentiment(transcript_result.full_text),
                self.analyze_structure(transcript_result)
            ]
            
            summary, key_points, topic_analysis, sentiment_analysis, structural_analysis = await asyncio.gather(*tasks)
            
            # 计算质量指标
            quality_metrics = await self._calculate_quality_metrics(
                transcript_result.full_text, key_points, topic_analysis, sentiment_analysis
            )
            
            # 生成深度洞察和建议
            insights = await self._generate_insights(
                summary, key_points, topic_analysis, sentiment_analysis, video_info
            )
            recommendations = await self._generate_recommendations(
                quality_metrics, topic_analysis, sentiment_analysis, video_info
            )
            
            # 分析目标受众和内容价值
            target_audience = await self._analyze_target_audience(
                topic_analysis, sentiment_analysis, video_info
            )
            content_value = await self._assess_content_value(
                key_points, quality_metrics, video_info
            )
            
            processing_time = time.time() - start_time
            
            return ContentInsights(
                video_id=video_info.id,
                analysis_id=str(uuid.uuid4()),
                summary=summary,
                key_points=key_points,
                topic_analysis=topic_analysis,
                sentiment_analysis=sentiment_analysis,
                structural_analysis=structural_analysis,
                quality_metrics=quality_metrics,
                insights=insights,
                recommendations=recommendations,
                target_audience=target_audience,
                content_value=content_value,
                analysis_model=self.model_name,
                analysis_version="1.0.0",
                processing_time=processing_time,
                confidence_score=self._calculate_confidence_score(quality_metrics),
                created_at=datetime.utcnow()
            )
            
        except Exception as e:
            raise ContentAnalysisError(f"内容分析失败: {e}")
    
    async def _generate_summary(self, text: str, video_info: 'VideoInfo') -> str:
        """生成内容摘要"""
        prompt = f"""
        请为以下视频内容生成一个简洁而全面的摘要：

        视频标题: {video_info.title}
        频道: {video_info.channel_title}
        时长: {video_info.duration}秒

        转录内容:
        {text[:4000]}  # 限制长度

        要求:
        1. 摘要应该在150-300字之间
        2. 突出主要观点和核心信息
        3. 保持客观和准确
        4. 使用清晰易懂的语言
        """
        
        response = await self.client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,
            temperature=0.3
        )
        
        return response.choices[0].message.content.strip()
    
    async def extract_key_points(self, text: str, max_points: int = 10) -> List[KeyPoint]:
        """提取关键要点"""
        prompt = f"""
        请从以下文本中提取{max_points}个最重要的关键要点：

        {text[:3000]}

        要求:
        1. 每个要点应该是完整的句子或短语
        2. 按重要性排序
        3. 避免重复内容
        4. 返回JSON格式，包含text和importance_score字段

        格式示例:
        [
            {{"text": "关键要点1", "importance_score": 0.95}},
            {{"text": "关键要点2", "importance_score": 0.87}}
        ]
        """
        
        response = await self.client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1000,
            temperature=0.2
        )
        
        try:
            points_data = json.loads(response.choices[0].message.content)
            return [
                KeyPoint(
                    id=str(uuid.uuid4()),
                    text=point["text"],
                    importance_score=point["importance_score"],
                    category=await self._categorize_key_point(point["text"])
                )
                for point in points_data[:max_points]
            ]
        except (json.JSONDecodeError, KeyError) as e:
            raise ContentAnalysisError(f"关键要点提取失败: {e}")
    
    async def analyze_topics(self, text: str) -> TopicAnalysis:
        """分析主题"""
        prompt = f"""
        请分析以下文本的主题结构：

        {text[:3000]}

        要求:
        1. 识别主要主题
        2. 列出3-5个子主题
        3. 提取10-15个关键词
        4. 评估主题连贯性(0-1分)
        5. 返回JSON格式

        格式示例:
        {{
            "main_topic": "主要主题",
            "sub_topics": ["子主题1", "子主题2"],
            "keywords": ["关键词1", "关键词2"],
            "topic_coherence_score": 0.85
        }}
        """
        
        response = await self.client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=800,
            temperature=0.3
        )
        
        try:
            topic_data = json.loads(response.choices[0].message.content)
            return TopicAnalysis(
                main_topic=topic_data["main_topic"],
                sub_topics=topic_data["sub_topics"],
                keywords=topic_data["keywords"],
                topic_coherence_score=topic_data["topic_coherence_score"],
                topic_distribution=await self._calculate_topic_distribution(topic_data["sub_topics"])
            )
        except (json.JSONDecodeError, KeyError) as e:
            raise ContentAnalysisError(f"主题分析失败: {e}")
    
    async def analyze_sentiment(self, text: str) -> SentimentAnalysis:
        """分析情感"""
        prompt = f"""
        请分析以下文本的情感特征：

        {text[:3000]}

        要求:
        1. 判断整体情感倾向(positive/negative/neutral/mixed)
        2. 给出情感分数(-1到1)
        3. 分析情感分布
        4. 描述情感变化轨迹
        5. 返回JSON格式

        格式示例:
        {{
            "overall_sentiment": "positive",
            "sentiment_score": 0.65,
            "sentiment_distribution": {{"positive": 0.6, "neutral": 0.3, "negative": 0.1}},
            "emotional_arc": [
                {{"timestamp": 0, "sentiment": "neutral", "score": 0.1}},
                {{"timestamp": 30, "sentiment": "positive", "score": 0.7}}
            ]
        }}
        """
        
        response = await self.client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=800,
            temperature=0.2
        )
        
        try:
            sentiment_data = json.loads(response.choices[0].message.content)
            return SentimentAnalysis(
                overall_sentiment=SentimentType(sentiment_data["overall_sentiment"]),
                sentiment_score=sentiment_data["sentiment_score"],
                sentiment_distribution=sentiment_data["sentiment_distribution"],
                emotional_arc=sentiment_data["emotional_arc"]
            )
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            raise ContentAnalysisError(f"情感分析失败: {e}")
```

## 错误处理规范

### 异常类型定义

```python
class ContentAnalysisError(Exception):
    """内容分析错误基类"""
    pass

class LLMAPIError(ContentAnalysisError):
    """LLM API错误"""
    pass

class TextProcessingError(ContentAnalysisError):
    """文本处理错误"""
    pass

class QualityThresholdError(ContentAnalysisError):
    """质量阈值错误"""
    pass
```

### 错误响应格式

```json
{
  "error": "content_analysis_error",
  "error_type": "LLMAPIError",
  "message": "LLM API调用失败",
  "code": "LLM_API_FAILED",
  "details": {
    "model": "gpt-4",
    "error_details": "Rate limit exceeded",
    "retry_after": 60,
    "timestamp": "2025-06-06T01:00:00Z"
  }
}
```

## 质量保证要求

### 分析质量指标

```python
def validate_content_insights(insights: ContentInsights) -> bool:
    """验证内容分析结果质量"""
    # 检查必需字段
    if not insights.summary or len(insights.summary) < 50:
        raise QualityThresholdError("摘要过短")
    
    if len(insights.key_points) < 3:
        raise QualityThresholdError("关键要点过少")
    
    if insights.confidence_score < 0.6:
        raise QualityThresholdError("置信度过低")
    
    # 检查关键要点质量
    for point in insights.key_points:
        if point.importance_score < 0.3:
            raise QualityThresholdError(f"关键要点重要性过低: {point.text}")
    
    # 检查主题连贯性
    if insights.topic_analysis.topic_coherence_score < 0.5:
        raise QualityThresholdError("主题连贯性过低")
    
    return True
```

## 性能要求

### 处理时间限制

- **短文本 (< 1000词)**: < 30秒
- **中等文本 (1000-5000词)**: < 60秒
- **长文本 (> 5000词)**: < 120秒

### 资源使用限制

- **内存使用**: < 1GB per analysis
- **API调用**: < 10 calls per analysis
- **并发分析**: 最多5个同时进行

## 测试用例

### 单元测试

```python
import pytest
from unittest.mock import Mock, patch

@pytest.mark.asyncio
async def test_extract_key_points():
    """测试关键要点提取"""
    analyzer = LLMContentAnalyzer()
    
    with patch.object(analyzer.client.chat.completions, 'create') as mock_create:
        mock_create.return_value.choices[0].message.content = json.dumps([
            {"text": "关键要点1", "importance_score": 0.9},
            {"text": "关键要点2", "importance_score": 0.8}
        ])
        
        key_points = await analyzer.extract_key_points("测试文本", max_points=5)
        
        assert len(key_points) == 2
        assert key_points[0].text == "关键要点1"
        assert key_points[0].importance_score == 0.9

@pytest.mark.asyncio
async def test_analyze_sentiment():
    """测试情感分析"""
    analyzer = LLMContentAnalyzer()
    
    with patch.object(analyzer.client.chat.completions, 'create') as mock_create:
        mock_create.return_value.choices[0].message.content = json.dumps({
            "overall_sentiment": "positive",
            "sentiment_score": 0.7,
            "sentiment_distribution": {"positive": 0.7, "neutral": 0.2, "negative": 0.1},
            "emotional_arc": []
        })
        
        sentiment = await analyzer.analyze_sentiment("积极的测试文本")
        
        assert sentiment.overall_sentiment == SentimentType.POSITIVE
        assert sentiment.sentiment_score == 0.7
        assert sentiment.is_positive()
```

### 集成测试

```python
@pytest.mark.integration
async def test_full_content_analysis():
    """测试完整内容分析流程"""
    analyzer = LLMContentAnalyzer()
    
    # 模拟转录结果
    transcript_result = Mock()
    transcript_result.full_text = "这是一个测试视频的转录内容..."
    transcript_result.segments = []
    
    # 模拟视频信息
    video_info = Mock()
    video_info.id = "test_video"
    video_info.title = "测试视频"
    video_info.channel_title = "测试频道"
    video_info.duration = 300
    
    # 执行分析
    result = await analyzer.analyze_content(transcript_result, video_info)
    
    # 验证结果
    assert isinstance(result, ContentInsights)
    assert result.video_id == "test_video"
    assert len(result.summary) > 50
    assert len(result.key_points) > 0
    assert result.confidence_score > 0
    
    # 验证质量
    validate_content_insights(result)
```

## 使用示例

### 基本使用

```python
from app.services.content_analyzer import LLMContentAnalyzer

async def analyze_video_content(transcript_result: TranscriptResult, 
                              video_info: VideoInfo) -> ContentInsights:
    """分析视频内容"""
    analyzer = LLMContentAnalyzer(model_name="gpt-4")
    
    try:
        # 执行内容分析
        insights = await analyzer.analyze_content(
            transcript_result, 
            video_info,
            options={
                'max_key_points': 10,
                'include_timestamps': True,
                'analysis_depth': 'detailed'
            }
        )
        
        # 质量验证
        validate_content_insights(insights)
        
        return insights
        
    except ContentAnalysisError as e:
        logger.error(f"内容分析失败: {e}")
        raise
```

### Celery任务集成

```python
@celery_app.task(bind=True)
def analyze_content_task(self, task_id: str, transcript_data: dict, video_data: dict):
    """内容分析任务"""
    
    async def _analyze():
        # 重建对象
        transcript_result = TranscriptResult(**transcript_data)
        video_info = VideoInfo(**video_data)
        
        analyzer = LLMContentAnalyzer()
        
        # 更新进度
        self.update_state(state='PROGRESS', meta={'progress': 10, 'message': '开始内容分析'})
        
        # 执行分析
        insights = await analyzer.analyze_content(transcript_result, video_info)
        
        self.update_state(state='PROGRESS', meta={'progress': 100, 'message': '内容分析完成'})
        
        return insights.dict()
    
    import asyncio
    return asyncio.run(_analyze())
```
