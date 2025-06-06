# Task 6: 内容分析模块 - Sub-Session Prompt

## 必读文档

**重要提示**: 开始此任务前，你必须阅读并理解以下文档：

### 核心协调文档
- `docs/TASK_COORDINATION.md` - 整体任务依赖关系和项目结构
- `docs/ARCHITECTURE_OVERVIEW.md` - 系统架构和技术栈
- `docs/CODING_STANDARDS.md` - 代码格式、命名规范和最佳实践
- `docs/API_SPECIFICATIONS.md` - 完整API接口定义

### 任务专用文档
- `docs/tasks/TASK_06_CONTENT_ANALYSIS.md` - 详细任务要求和验收标准
- `docs/contracts/content_analysis_contract.md` - 内容分析接口规范

### 参考文档
- `docs/DEVELOPMENT_SETUP.md` - 开发环境配置
- `docs/PROGRESS_TRACKER.md` - 进度跟踪和任务状态更新

### 依赖关系
- Task 1 (项目配置) 必须先完成
- Task 2 (后端API) 必须先完成
- Task 5 (音频转录) 必须先完成
- 查看 `docs/contracts/project_config_contract.md` 了解配置接口
- 查看 `docs/contracts/api_framework_contract.md` 了解API接口
- 查看 `docs/contracts/transcription_contract.md` 了解转录数据接口

## 项目背景

你正在为YouTube视频分析工具构建内容分析模块。这个模块需要：
- 使用LLM对转录文本进行深度分析
- 提取关键要点和主题
- 进行情感分析和内容分类
- 生成结构化的分析报告

## 任务目标

实现完整的内容分析服务，包括LLM集成、多维度分析、结构化输出和可扩展的分析器架构。

## 具体要求

### 1. 内容分析器核心实现
参考 <ref_file file="/home/ubuntu/repos/generic-ai-agent/src/agent_core/response_router.py" /> 的插件化架构模式：

```python
# backend/app/services/content_analyzer.py
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import openai
import logging
from enum import Enum

from app.core.config import settings
from app.utils.exceptions import ExternalServiceError

class ContentType(str, Enum):
    EDUCATIONAL = "educational"
    ENTERTAINMENT = "entertainment"
    NEWS = "news"
    REVIEW = "review"
    TUTORIAL = "tutorial"
    DISCUSSION = "discussion"
    OTHER = "other"

class SentimentType(str, Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    MIXED = "mixed"

@dataclass
class KeyPoint:
    text: str
    importance: float  # 0-1
    timestamp_start: Optional[float] = None
    timestamp_end: Optional[float] = None
    category: Optional[str] = None

@dataclass
class TopicAnalysis:
    main_topic: str
    sub_topics: List[str]
    keywords: List[str]
    content_type: ContentType
    confidence: float

@dataclass
class SentimentAnalysis:
    overall_sentiment: SentimentType
    sentiment_score: float  # -1 to 1
    emotional_tone: List[str]
    sentiment_progression: List[Dict[str, Any]]

@dataclass
class ContentStructure:
    introduction_end: Optional[float]
    main_content_segments: List[Dict[str, Any]]
    conclusion_start: Optional[float]
    call_to_action: Optional[str]

@dataclass
class ContentInsights:
    key_points: List[KeyPoint]
    topic_analysis: TopicAnalysis
    sentiment_analysis: SentimentAnalysis
    content_structure: ContentStructure
    summary: str
    recommendations: List[str]
    quality_score: float

class BaseContentAnalyzer(ABC):
    """内容分析器基类"""
    
    @abstractmethod
    async def analyze(self, transcript_data: Dict[str, Any], video_info: Dict[str, Any]) -> ContentInsights:
        pass

class LLMContentAnalyzer(BaseContentAnalyzer):
    """基于LLM的内容分析器"""
    
    def __init__(self):
        self.client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model or "gpt-4"
    
    async def analyze(self, transcript_data: Dict[str, Any], video_info: Dict[str, Any]) -> ContentInsights:
        """执行完整的内容分析"""
        try:
            full_text = transcript_data.get('full_text', '')
            segments = transcript_data.get('segments', [])
            
            if not full_text:
                raise ValueError("转录文本为空")
            
            # 并行执行多个分析任务
            import asyncio
            
            tasks = [
                self._extract_key_points(full_text, segments),
                self._analyze_topics(full_text, video_info),
                self._analyze_sentiment(full_text, segments),
                self._analyze_structure(full_text, segments),
                self._generate_summary(full_text, video_info),
                self._generate_recommendations(full_text, video_info)
            ]
            
            results = await asyncio.gather(*tasks)
            
            key_points, topic_analysis, sentiment_analysis, content_structure, summary, recommendations = results
            
            # 计算质量分数
            quality_score = self._calculate_quality_score(
                key_points, topic_analysis, sentiment_analysis, len(full_text.split())
            )
            
            return ContentInsights(
                key_points=key_points,
                topic_analysis=topic_analysis,
                sentiment_analysis=sentiment_analysis,
                content_structure=content_structure,
                summary=summary,
                recommendations=recommendations,
                quality_score=quality_score
            )
            
        except Exception as e:
            logging.error(f"Content analysis failed: {e}")
            raise ExternalServiceError(f"内容分析失败: {e}")
    
    async def _extract_key_points(self, text: str, segments: List[Dict]) -> List[KeyPoint]:
        """提取关键要点"""
        prompt = f"""
        请分析以下视频转录文本，提取最重要的关键要点。

        转录文本：
        {text[:4000]}  # 限制长度避免token超限

        请按重要性排序，提取5-10个关键要点，每个要点包含：
        1. 要点内容（简洁明了）
        2. 重要性评分（0-1）
        3. 所属类别（如果适用）

        请以JSON格式返回：
        {{
            "key_points": [
                {{
                    "text": "要点内容",
                    "importance": 0.9,
                    "category": "类别名称"
                }}
            ]
        }}
        """
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=1000
            )
            
            import json
            result = json.loads(response.choices[0].message.content)
            
            key_points = []
            for point_data in result.get('key_points', []):
                # 尝试匹配时间戳
                timestamp_start, timestamp_end = self._find_timestamp_for_text(
                    point_data['text'], segments
                )
                
                key_points.append(KeyPoint(
                    text=point_data['text'],
                    importance=point_data.get('importance', 0.5),
                    category=point_data.get('category'),
                    timestamp_start=timestamp_start,
                    timestamp_end=timestamp_end
                ))
            
            return key_points
            
        except Exception as e:
            logging.error(f"Key points extraction failed: {e}")
            return []
    
    async def _analyze_topics(self, text: str, video_info: Dict) -> TopicAnalysis:
        """分析主题和内容类型"""
        prompt = f"""
        请分析以下视频的主题和内容类型。

        视频标题：{video_info.get('title', '')}
        视频描述：{video_info.get('description', '')[:500]}
        转录文本：{text[:3000]}

        请分析：
        1. 主要主题
        2. 子主题（3-5个）
        3. 关键词（5-10个）
        4. 内容类型（educational/entertainment/news/review/tutorial/discussion/other）
        5. 分析置信度（0-1）

        请以JSON格式返回：
        {{
            "main_topic": "主要主题",
            "sub_topics": ["子主题1", "子主题2"],
            "keywords": ["关键词1", "关键词2"],
            "content_type": "educational",
            "confidence": 0.85
        }}
        """
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=800
            )
            
            import json
            result = json.loads(response.choices[0].message.content)
            
            return TopicAnalysis(
                main_topic=result.get('main_topic', '未知主题'),
                sub_topics=result.get('sub_topics', []),
                keywords=result.get('keywords', []),
                content_type=ContentType(result.get('content_type', 'other')),
                confidence=result.get('confidence', 0.5)
            )
            
        except Exception as e:
            logging.error(f"Topic analysis failed: {e}")
            return TopicAnalysis(
                main_topic="分析失败",
                sub_topics=[],
                keywords=[],
                content_type=ContentType.OTHER,
                confidence=0.0
            )
    
    async def _analyze_sentiment(self, text: str, segments: List[Dict]) -> SentimentAnalysis:
        """分析情感和语调"""
        prompt = f"""
        请分析以下视频转录文本的情感和语调。

        转录文本：
        {text[:3000]}

        请分析：
        1. 整体情感倾向（positive/negative/neutral/mixed）
        2. 情感强度评分（-1到1，-1最负面，1最正面）
        3. 情感语调特征（如：enthusiastic, calm, serious, humorous等）
        4. 情感变化趋势（如果文本较长）

        请以JSON格式返回：
        {{
            "overall_sentiment": "positive",
            "sentiment_score": 0.7,
            "emotional_tone": ["enthusiastic", "informative"],
            "sentiment_progression": [
                {{"segment": "开头", "sentiment": "neutral", "score": 0.1}},
                {{"segment": "中间", "sentiment": "positive", "score": 0.8}}
            ]
        }}
        """
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=600
            )
            
            import json
            result = json.loads(response.choices[0].message.content)
            
            return SentimentAnalysis(
                overall_sentiment=SentimentType(result.get('overall_sentiment', 'neutral')),
                sentiment_score=result.get('sentiment_score', 0.0),
                emotional_tone=result.get('emotional_tone', []),
                sentiment_progression=result.get('sentiment_progression', [])
            )
            
        except Exception as e:
            logging.error(f"Sentiment analysis failed: {e}")
            return SentimentAnalysis(
                overall_sentiment=SentimentType.NEUTRAL,
                sentiment_score=0.0,
                emotional_tone=[],
                sentiment_progression=[]
            )
    
    async def _analyze_structure(self, text: str, segments: List[Dict]) -> ContentStructure:
        """分析内容结构"""
        prompt = f"""
        请分析以下视频转录文本的结构组织。

        转录文本：
        {text[:3000]}

        请识别：
        1. 介绍部分结束时间点
        2. 主要内容段落划分
        3. 结论部分开始时间点
        4. 行动号召（如果有）

        请以JSON格式返回：
        {{
            "introduction_end": 30.5,
            "main_content_segments": [
                {{"title": "段落标题", "start": 30.5, "end": 120.0, "summary": "段落摘要"}}
            ],
            "conclusion_start": 450.0,
            "call_to_action": "订阅频道"
        }}
        """
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=800
            )
            
            import json
            result = json.loads(response.choices[0].message.content)
            
            return ContentStructure(
                introduction_end=result.get('introduction_end'),
                main_content_segments=result.get('main_content_segments', []),
                conclusion_start=result.get('conclusion_start'),
                call_to_action=result.get('call_to_action')
            )
            
        except Exception as e:
            logging.error(f"Structure analysis failed: {e}")
            return ContentStructure(
                introduction_end=None,
                main_content_segments=[],
                conclusion_start=None,
                call_to_action=None
            )
    
    async def _generate_summary(self, text: str, video_info: Dict) -> str:
        """生成内容摘要"""
        prompt = f"""
        请为以下YouTube视频生成一个简洁而全面的摘要。

        视频标题：{video_info.get('title', '')}
        转录文本：{text[:4000]}

        请生成一个200-300字的摘要，包含：
        1. 视频的主要内容
        2. 关键观点
        3. 主要结论或建议

        摘要应该客观、准确、易于理解。
        """
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=500
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logging.error(f"Summary generation failed: {e}")
            return "摘要生成失败"
    
    async def _generate_recommendations(self, text: str, video_info: Dict) -> List[str]:
        """生成改进建议"""
        prompt = f"""
        基于以下视频内容分析，请提供3-5个具体的改进建议。

        视频标题：{video_info.get('title', '')}
        视频时长：{video_info.get('duration', 0)}秒
        转录文本：{text[:3000]}

        请从以下角度提供建议：
        1. 内容组织和结构
        2. 观众参与度
        3. 信息传达效果
        4. 技术质量

        请以JSON格式返回：
        {{
            "recommendations": [
                "具体建议1",
                "具体建议2"
            ]
        }}
        """
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.4,
                max_tokens=600
            )
            
            import json
            result = json.loads(response.choices[0].message.content)
            return result.get('recommendations', [])
            
        except Exception as e:
            logging.error(f"Recommendations generation failed: {e}")
            return []
    
    def _find_timestamp_for_text(self, text: str, segments: List[Dict]) -> tuple:
        """为文本查找对应的时间戳"""
        # 简单的文本匹配逻辑
        for segment in segments:
            if text.lower() in segment.get('text', '').lower():
                return segment.get('start'), segment.get('end')
        return None, None
    
    def _calculate_quality_score(self, key_points: List[KeyPoint], topic_analysis: TopicAnalysis, 
                                sentiment_analysis: SentimentAnalysis, word_count: int) -> float:
        """计算内容质量分数"""
        score = 0.0
        
        # 关键要点质量
        if key_points:
            avg_importance = sum(kp.importance for kp in key_points) / len(key_points)
            score += avg_importance * 0.3
        
        # 主题分析置信度
        score += topic_analysis.confidence * 0.2
        
        # 内容长度适中性
        if 500 <= word_count <= 3000:
            score += 0.2
        elif word_count > 100:
            score += 0.1
        
        # 情感分析质量
        if abs(sentiment_analysis.sentiment_score) > 0.1:  # 有明确情感倾向
            score += 0.15
        
        # 结构完整性
        score += 0.15  # 基础分
        
        return min(score, 1.0)

# 全局实例
content_analyzer = LLMContentAnalyzer()
```

## 验收标准

### 功能验收
- [ ] LLM集成正常工作
- [ ] 关键要点提取准确
- [ ] 主题分析合理
- [ ] 情感分析准确
- [ ] 内容结构识别正确
- [ ] 摘要生成质量高

### 技术验收
- [ ] 分析时间 < 2分钟
- [ ] API调用成功率 > 95%
- [ ] 并发分析处理正常
- [ ] 错误处理机制完善
- [ ] 内存使用合理

### 质量验收
- [ ] 单元测试覆盖率 ≥ 80%
- [ ] 多种内容类型测试通过
- [ ] 不同语言内容测试通过
- [ ] 长短视频测试通过
- [ ] 代码遵循项目规范

## 测试要求

### 单元测试
```python
# tests/test_content_analyzer.py
import pytest
from unittest.mock import Mock, patch, AsyncMock
from app.services.content_analyzer import LLMContentAnalyzer, ContentInsights

@pytest.fixture
def analyzer():
    return LLMContentAnalyzer()

@pytest.mark.asyncio
async def test_analyze_content(analyzer):
    """测试内容分析"""
    transcript_data = {
        'full_text': 'This is a test video about machine learning.',
        'segments': [
            {'start': 0, 'end': 5, 'text': 'This is a test video'},
            {'start': 5, 'end': 10, 'text': 'about machine learning.'}
        ]
    }
    
    video_info = {
        'title': 'Machine Learning Tutorial',
        'description': 'Learn ML basics',
        'duration': 600
    }
    
    with patch.object(analyzer.client.chat.completions, 'create') as mock_create:
        mock_create.return_value = Mock(
            choices=[Mock(message=Mock(content='{"key_points": [{"text": "ML basics", "importance": 0.8}]}'))]
        )
        
        result = await analyzer.analyze(transcript_data, video_info)
        
        assert isinstance(result, ContentInsights)
        assert result.summary is not None
        assert len(result.key_points) > 0
```

## 交付物清单

- [ ] 内容分析器核心类 (app/services/content_analyzer.py)
- [ ] 数据模型定义 (ContentInsights, KeyPoint等)
- [ ] Celery任务实现 (app/tasks/content_analysis.py)
- [ ] LLM集成和提示工程
- [ ] 多维度分析功能
- [ ] 质量评分算法
- [ ] 错误处理和日志记录
- [ ] 单元测试文件
- [ ] 配置文件更新

## 关键接口

完成此任务后，需要为后续任务提供：
- 结构化的内容分析结果
- 关键要点和主题信息
- 情感分析数据
- 内容质量评分

## 预估时间

- 开发时间: 3-4天
- 测试时间: 1天
- 提示优化: 1天
- 文档时间: 0.5天
- 总计: 5.5-6.5天

## 注意事项

1. 确保LLM API调用的稳定性和错误处理
2. 优化提示词以获得更好的分析质量
3. 控制API调用成本和频率
4. 处理不同类型和质量的内容
5. 实现可扩展的分析器架构

这是核心的智能分析模块，请确保分析结果的准确性和有用性。
