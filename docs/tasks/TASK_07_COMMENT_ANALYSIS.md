# Task 7: 评论分析模块

## 任务概述

实现YouTube评论分析模块，重点分析用户评论和作者回复，提供情感分析、主题提取和互动洞察。特别关注YouTube主播回复的部分，为视频内容提供更客观的评价维度。

## 目标

- 分析用户评论的情感倾向和主题
- 识别和重点分析作者回复内容
- 提取评论中的关键观点和反馈
- 分析评论与视频内容的相关性
- 生成评论洞察报告

## 可交付成果

### 1. 评论分析器核心实现

```python
# backend/app/services/comment_analyzer.py
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
import openai
import asyncio
import logging

from app.core.config import settings
from app.utils.exceptions import ExternalServiceError, AnalysisError

@dataclass
class CommentAnalysis:
    total_comments: int
    sentiment_distribution: Dict[str, int]
    avg_sentiment: float
    author_reply_analysis: Dict[str, Any]
    top_themes: List[Dict[str, Any]]
    controversial_topics: List[str]
    engagement_metrics: Dict[str, Any]
    insights: List[Dict[str, Any]]
    metadata: Dict[str, Any]

class BaseCommentAnalyzer(ABC):
    """评论分析器基类"""
    
    def __init__(self, name: str, version: str):
        self.name = name
        self.version = version
    
    @abstractmethod
    async def analyze(self, comments_data: List[Dict[str, Any]], video_info: Dict[str, Any]) -> CommentAnalysis:
        """执行评论分析"""
        pass
    
    @abstractmethod
    def get_progress_steps(self) -> List[str]:
        """返回分析步骤列表"""
        pass

class LLMCommentAnalyzer(BaseCommentAnalyzer):
    """基于LLM的评论分析器"""
    
    def __init__(self):
        super().__init__("llm_comment_analyzer", "1.0.0")
        self.client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model or "gpt-4"
    
    async def analyze(self, comments_data: List[Dict[str, Any]], video_info: Dict[str, Any]) -> CommentAnalysis:
        """执行完整的评论分析"""
        try:
            if not comments_data:
                return self._create_empty_analysis()
            
            # 预处理评论数据
            processed_comments = self._preprocess_comments(comments_data)
            
            # 并行执行各种分析
            tasks = [
                self._analyze_comment_sentiments(processed_comments),
                self._analyze_author_replies(processed_comments),
                self._extract_comment_themes(processed_comments),
                self._analyze_engagement_metrics(processed_comments)
            ]
            
            sentiment_results, author_analysis, themes, engagement = await asyncio.gather(*tasks)
            
            # 识别争议话题
            controversial_topics = await self._identify_controversial_topics(processed_comments)
            
            return CommentAnalysis(
                total_comments=len(processed_comments),
                sentiment_distribution=self._calculate_sentiment_distribution(sentiment_results),
                avg_sentiment=sum(r.get('sentiment_score', 0) for r in sentiment_results) / len(sentiment_results) if sentiment_results else 0,
                author_reply_analysis=author_analysis,
                top_themes=themes,
                controversial_topics=controversial_topics,
                engagement_metrics=engagement,
                insights=sentiment_results[:20],
                metadata={
                    "analysis_model": self.model,
                    "video_title": video_info.get('title', ''),
                    "analysis_timestamp": asyncio.get_event_loop().time()
                }
            )
            
        except Exception as e:
            logging.error(f"Comment analysis failed: {e}")
            raise AnalysisError(f"Comment analysis failed: {str(e)}")
    
    def _preprocess_comments(self, comments_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """预处理评论数据，过滤垃圾评论"""
        processed = []
        
        for comment in comments_data:
            text = comment.get('text', '').strip()
            if len(text) < 10 or self._is_spam_comment(text):
                continue
            
            processed.append({
                'id': comment.get('id', ''),
                'text': text,
                'author': comment.get('author', ''),
                'is_author_reply': comment.get('is_author_reply', False),
                'like_count': comment.get('like_count', 0),
                'reply_count': comment.get('reply_count', 0)
            })
        
        return processed
    
    def _is_spam_comment(self, text: str) -> bool:
        """检测垃圾评论"""
        spam_indicators = ['subscribe', '订阅', 'first', '沙发', 'check out my channel']
        text_lower = text.lower()
        return sum(1 for indicator in spam_indicators if indicator in text_lower) >= 2
    
    async def _analyze_author_replies(self, comments: List[Dict[str, Any]]) -> Dict[str, Any]:
        """重点分析作者回复"""
        author_replies = [c for c in comments if c.get('is_author_reply', False)]
        total_replies = len(author_replies)
        
        if total_replies == 0:
            return {
                'total_replies': 0,
                'reply_rate': 0,
                'avg_sentiment': 0,
                'common_topics': [],
                'engagement_quality': 0
            }
        
        # 分析作者回复内容
        reply_texts = [reply['text'] for reply in author_replies[:10]]
        
        prompt = f"""
        分析YouTube视频作者的回复内容，评估作者的互动质量。

        作者回复：
        {chr(10).join([f"{i+1}. {text}" for i, text in enumerate(reply_texts)])}

        请分析：
        1. 整体情感倾向（-1到1）
        2. 常见主题（最多5个）
        3. 互动质量评分（0-1）

        以JSON格式返回。
        """
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1000,
                temperature=0.3
            )
            
            import json
            result = json.loads(response.choices[0].message.content)
            
            return {
                'total_replies': total_replies,
                'reply_rate': total_replies / len(comments) if comments else 0,
                'avg_sentiment': result.get("avg_sentiment", 0),
                'common_topics': result.get("common_topics", []),
                'engagement_quality': result.get("engagement_quality", 0.5)
            }
            
        except Exception as e:
            logging.error(f"Author reply analysis failed: {e}")
            return {
                'total_replies': total_replies,
                'reply_rate': total_replies / len(comments) if comments else 0,
                'avg_sentiment': 0,
                'common_topics': [],
                'engagement_quality': 0.5
            }
    
    def get_progress_steps(self) -> List[str]:
        return [
            "预处理评论数据",
            "分析评论情感",
            "分析作者回复",
            "提取讨论主题",
            "计算互动指标"
        ]

# 评论分析器注册中心
class CommentAnalyzerRegistry:
    def __init__(self):
        self._analyzers: Dict[str, BaseCommentAnalyzer] = {}
    
    def register(self, analyzer: BaseCommentAnalyzer):
        self._analyzers[analyzer.name] = analyzer
    
    def get_default_analyzer(self) -> BaseCommentAnalyzer:
        if "llm_comment_analyzer" in self._analyzers:
            return self._analyzers["llm_comment_analyzer"]
        raise AnalysisError("No comment analyzer available")

comment_analyzer_registry = CommentAnalyzerRegistry()
comment_analyzer_registry.register(LLMCommentAnalyzer())
```

### 2. Celery任务集成

```python
# backend/app/tasks/comment_analysis.py
from celery import current_task
from app.core.celery_app import celery_app
from app.services.comment_analyzer import comment_analyzer_registry
from app.api.v1.websocket import send_progress_update
from app.models.task import AnalysisTask, TaskStatus
from app.core.database import get_db_session
from sqlalchemy import update, select
import logging

@celery_app.task(bind=True)
def analyze_comments_task(self, task_id: str, options: dict):
    """评论分析Celery任务"""
    
    async def _analyze():
        try:
            analyzer = comment_analyzer_registry.get_default_analyzer()
            
            # 获取评论数据
            async with get_db_session() as db:
                result = await db.execute(
                    select(AnalysisTask.result_data).where(AnalysisTask.id == task_id)
                )
                task_data = result.scalar()
                
                comments_data = task_data.get('comments', [])
                video_info_data = task_data.get('video_info', {})
            
            # 执行分析
            analysis_result = await analyzer.analyze(comments_data, video_info_data)
            
            # 保存结果
            comment_analysis_data = {
                'total_comments': analysis_result.total_comments,
                'sentiment_distribution': analysis_result.sentiment_distribution,
                'author_reply_analysis': analysis_result.author_reply_analysis,
                'top_themes': analysis_result.top_themes,
                'engagement_metrics': analysis_result.engagement_metrics,
                'metadata': analysis_result.metadata
            }
            
            # 更新数据库
            async with get_db_session() as db:
                result = await db.execute(
                    select(AnalysisTask.result_data).where(AnalysisTask.id == task_id)
                )
                existing_data = result.scalar() or {}
                existing_data['comment_analysis'] = comment_analysis_data
                
                await db.execute(
                    update(AnalysisTask)
                    .where(AnalysisTask.id == task_id)
                    .values(result_data=existing_data)
                )
                await db.commit()
            
            return comment_analysis_data
            
        except Exception as e:
            logging.error(f"Comment analysis failed for task {task_id}: {e}")
            raise
    
    import asyncio
    return asyncio.run(_analyze())
```

## 依赖关系

### 前置条件
- Task 1: 项目配置管理（必须完成）
- Task 2: 后端API框架（必须完成）
- Task 4: YouTube数据提取（必须完成，需要评论数据）

### 阻塞任务
- Task 8: 分析编排器（需要评论分析服务）
- Task 9: 结果展示（需要分析结果）

## 验收标准

### 功能验收
- [ ] 评论情感分析准确
- [ ] 作者回复识别和分析正确
- [ ] 主题提取有意义
- [ ] 争议话题识别合理
- [ ] 互动指标计算准确
- [ ] 垃圾评论过滤有效

### 技术验收
- [ ] 分析准确率 ≥ 80%
- [ ] 处理时间 < 1分钟（1000条评论）
- [ ] 内存使用合理（< 2GB）
- [ ] 错误处理完善
- [ ] 插件化架构可扩展

### 质量验收
- [ ] 单元测试覆盖率 ≥ 80%
- [ ] 多语言评论测试通过
- [ ] 大量评论处理稳定
- [ ] 作者回复识别准确
- [ ] 代码遵循项目规范

## 测试要求

### 单元测试
```python
# tests/test_comment_analyzer.py
import pytest
from app.services.comment_analyzer import LLMCommentAnalyzer

@pytest.fixture
def analyzer():
    return LLMCommentAnalyzer()

@pytest.mark.asyncio
async def test_author_reply_analysis(analyzer):
    """测试作者回复分析"""
    comments = [
        {'text': '很棒的视频！', 'author': 'user1', 'is_author_reply': False},
        {'text': '谢谢支持！', 'author': 'channel_owner', 'is_author_reply': True}
    ]
    
    result = await analyzer._analyze_author_replies(comments)
    
    assert result['total_replies'] == 1
    assert result['reply_rate'] == 0.5

def test_spam_detection(analyzer):
    """测试垃圾评论检测"""
    spam_comment = "first! subscribe to my channel!"
    normal_comment = "这个视频很有帮助，学到了很多"
    
    assert analyzer._is_spam_comment(spam_comment) == True
    assert analyzer._is_spam_comment(normal_comment) == False
```

## 预估工作量

- **开发时间**: 3-4天
- **测试时间**: 1.5天
- **LLM提示优化**: 1天
- **文档时间**: 0.5天
- **总计**: 6天

## 关键路径

此任务与Task 6并行执行，完成后将为Task 8（分析编排器）提供评论分析能力。

## 交付检查清单

- [ ] 评论分析器核心功能已实现
- [ ] 作者回复重点分析已实现
- [ ] 情感分析已实现
- [ ] 主题提取已实现
- [ ] 垃圾评论过滤已实现
- [ ] Celery任务集成已完成
- [ ] 单元测试通过
- [ ] 代码已提交并通过CI检查

## 后续任务接口

完成此任务后，为后续任务提供：
- 结构化的评论分析结果
- 作者回复洞察数据
- 评论情感分布
- 互动质量评估
- 争议话题识别

这些将被Task 8（分析编排器）和Task 9（结果展示）直接使用。
