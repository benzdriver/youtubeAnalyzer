# Task 7: 评论分析模块 - Sub-Session Prompt

## 项目背景

你正在为YouTube视频分析工具构建评论分析模块。这个模块需要：
- 分析YouTube视频评论的情感和主题
- 特别关注作者回复的识别和分析
- 提供观众反馈的客观评价
- 生成评论洞察和互动质量报告

## 任务目标

实现完整的评论分析服务，包括情感分析、主题提取、作者互动分析和评论质量评估。

## 具体要求

### 1. 评论分析器核心实现

```python
# backend/app/services/comment_analyzer.py
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from collections import Counter
import openai
import logging
from datetime import datetime
import re

from app.core.config import settings
from app.utils.exceptions import ExternalServiceError

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
        self.client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model or "gpt-4"
    
    async def analyze_comments(self, comments_data: List[Dict[str, Any]], 
                             video_info: Dict[str, Any]) -> CommentInsights:
        """分析评论数据"""
        try:
            if not comments_data:
                return self._empty_insights()
            
            # 预处理评论数据
            processed_comments = self._preprocess_comments(comments_data)
            
            # 并行执行分析任务
            import asyncio
            
            tasks = [
                self._analyze_sentiment_distribution(processed_comments),
                self._extract_themes(processed_comments),
                self._analyze_author_engagement(processed_comments, video_info),
                self._identify_top_comments(processed_comments),
                self._detect_spam(processed_comments),
                self._calculate_engagement_metrics(processed_comments, video_info)
            ]
            
            results = await asyncio.gather(*tasks)
            
            (sentiment_dist, themes, author_engagement, 
             top_comments, spam_detection, engagement_metrics) = results
            
            # 生成建议
            recommendations = await self._generate_recommendations(
                sentiment_dist, themes, author_engagement, engagement_metrics
            )
            
            return CommentInsights(
                total_comments=len(processed_comments),
                sentiment_distribution=sentiment_dist,
                main_themes=themes,
                author_engagement=author_engagement,
                top_comments=top_comments,
                spam_detection=spam_detection,
                engagement_metrics=engagement_metrics,
                recommendations=recommendations
            )
            
        except Exception as e:
            logging.error(f"Comment analysis failed: {e}")
            raise ExternalServiceError(f"评论分析失败: {e}")
    
    async def _analyze_author_engagement(self, comments: List[Dict], 
                                       video_info: Dict) -> AuthorEngagement:
        """分析作者互动情况"""
        author_channel_id = video_info.get('channel_id')
        author_replies = [c for c in comments if c.get('is_author_reply', False)]
        
        total_replies = len(author_replies)
        total_comments = len([c for c in comments if not c.get('parent_id')])  # 主评论数
        reply_rate = total_replies / max(total_comments, 1)
        
        # 分析作者回复的情感
        if author_replies:
            reply_texts = [r['text'] for r in author_replies[:20]]  # 分析前20个回复
            
            prompt = f"""
            请分析以下YouTube视频作者的回复评论的情感分布和互动质量。

            作者回复：
            {chr(10).join([f"{i+1}. {text[:200]}" for i, text in enumerate(reply_texts)])}

            请分析：
            1. 回复的整体情感分布
            2. 互动质量评分（0-1，考虑回复的有用性、友好度、专业性）
            3. 回复风格特征

            请以JSON格式返回：
            {{
                "sentiment_distribution": {{"positive": 15, "negative": 2, "neutral": 8}},
                "engagement_quality": 0.85,
                "interaction_style": ["friendly", "informative", "responsive"]
            }}
            """
            
            try:
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.2,
                    max_tokens=500
                )
                
                import json
                result = json.loads(response.choices[0].message.content)
                
                sentiment_in_replies = result.get('sentiment_distribution', {})
                engagement_quality = result.get('engagement_quality', 0.5)
                
            except Exception as e:
                logging.error(f"Author engagement analysis failed: {e}")
                sentiment_in_replies = {"positive": 0, "negative": 0, "neutral": 0}
                engagement_quality = 0.5
        else:
            sentiment_in_replies = {"positive": 0, "negative": 0, "neutral": 0}
            engagement_quality = 0.0
        
        return AuthorEngagement(
            total_replies=total_replies,
            reply_rate=reply_rate,
            avg_response_time=None,  # 需要时间戳计算
            sentiment_in_replies=sentiment_in_replies,
            engagement_quality=engagement_quality
        )
    
    def _preprocess_comments(self, comments_data: List[Dict]) -> List[Dict]:
        """预处理评论数据"""
        processed = []
        
        for comment in comments_data:
            # 清理文本
            text = self._clean_comment_text(comment.get('text', ''))
            
            if len(text.strip()) < 3:  # 过滤过短的评论
                continue
            
            processed_comment = {
                'id': comment.get('id'),
                'text': text,
                'author': comment.get('author'),
                'author_channel_id': comment.get('author_channel_id'),
                'like_count': comment.get('like_count', 0),
                'reply_count': comment.get('reply_count', 0),
                'published_at': comment.get('published_at'),
                'is_author_reply': comment.get('is_author_reply', False),
                'parent_id': comment.get('parent_id'),
                'word_count': len(text.split())
            }
            
            processed.append(processed_comment)
        
        return processed
    
    def _clean_comment_text(self, text: str) -> str:
        """清理评论文本"""
        # 移除多余的空白字符
        text = re.sub(r'\s+', ' ', text)
        
        # 移除过多的重复字符
        text = re.sub(r'(.)\1{3,}', r'\1\1\1', text)
        
        # 移除URL
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
        
        return text.strip()

# 全局实例
comment_analyzer = CommentAnalyzer()
```

### 2. Celery任务集成

```python
# backend/app/tasks/comment_analysis.py
from celery import current_task
from app.core.celery_app import celery_app
from app.services.comment_analyzer import comment_analyzer
from app.api.v1.websocket import send_progress_update
from app.models.task import AnalysisTask, TaskStatus
from app.core.database import get_db_session
from sqlalchemy import update, select
import logging

@celery_app.task(bind=True)
def analyze_comments_task(self, task_id: str, comments_data: List[Dict], video_info: Dict, options: dict):
    """评论分析Celery任务"""
    
    async def _analyze():
        try:
            async with get_db_session() as db:
                await db.execute(
                    update(AnalysisTask)
                    .where(AnalysisTask.id == task_id)
                    .values(
                        status=TaskStatus.PROCESSING,
                        current_step="评论分析"
                    )
                )
                await db.commit()
            
            await send_progress_update(task_id, 10, "预处理评论数据")
            
            # 执行评论分析
            comment_insights = await comment_analyzer.analyze_comments(
                comments_data, video_info
            )
            
            await send_progress_update(task_id, 90, "保存分析结果")
            
            # 构建结果数据
            analysis_result = {
                'total_comments': comment_insights.total_comments,
                'sentiment_distribution': comment_insights.sentiment_distribution,
                'main_themes': [
                    {
                        'theme': theme.theme,
                        'keywords': theme.keywords,
                        'comment_count': theme.comment_count,
                        'sentiment_distribution': theme.sentiment_distribution
                    }
                    for theme in comment_insights.main_themes
                ],
                'author_engagement': {
                    'total_replies': comment_insights.author_engagement.total_replies,
                    'reply_rate': comment_insights.author_engagement.reply_rate,
                    'sentiment_in_replies': comment_insights.author_engagement.sentiment_in_replies,
                    'engagement_quality': comment_insights.author_engagement.engagement_quality
                },
                'top_comments': comment_insights.top_comments,
                'spam_detection': comment_insights.spam_detection,
                'engagement_metrics': comment_insights.engagement_metrics,
                'recommendations': comment_insights.recommendations
            }
            
            # 保存到数据库
            async with get_db_session() as db:
                result = await db.execute(
                    select(AnalysisTask).where(AnalysisTask.id == task_id)
                )
                task = result.scalar_one()
                
                current_result = task.result_data or {}
                current_result['comment_insights'] = analysis_result
                
                await db.execute(
                    update(AnalysisTask)
                    .where(AnalysisTask.id == task_id)
                    .values(result_data=current_result)
                )
                await db.commit()
            
            await send_progress_update(task_id, 100, "评论分析完成")
            
            return analysis_result
            
        except Exception as e:
            logging.error(f"Comment analysis failed for task {task_id}: {e}")
            
            async with get_db_session() as db:
                await db.execute(
                    update(AnalysisTask)
                    .where(AnalysisTask.id == task_id)
                    .values(
                        status=TaskStatus.FAILED,
                        error_message=f"评论分析失败: {str(e)}"
                    )
                )
                await db.commit()
            
            raise
    
    import asyncio
    return asyncio.run(_analyze())
```

## 验收标准

### 功能验收
- [ ] 评论情感分析准确
- [ ] 主题提取合理
- [ ] 作者回复正确识别和分析
- [ ] 垃圾评论检测有效
- [ ] 互动质量评估合理
- [ ] 推荐建议有价值

### 技术验收
- [ ] 分析时间 < 1分钟（1000条评论）
- [ ] 大量评论处理稳定
- [ ] 内存使用合理
- [ ] 错误处理机制完善
- [ ] API调用成功率 > 95%

### 质量验收
- [ ] 单元测试覆盖率 ≥ 80%
- [ ] 多语言评论测试通过
- [ ] 不同类型视频测试通过
- [ ] 作者互动分析准确
- [ ] 代码遵循项目规范

## 测试要求

### 单元测试
```python
# tests/test_comment_analyzer.py
import pytest
from unittest.mock import Mock, patch, AsyncMock
from app.services.comment_analyzer import CommentAnalyzer, CommentInsights

@pytest.fixture
def analyzer():
    return CommentAnalyzer()

@pytest.mark.asyncio
async def test_analyze_comments(analyzer):
    """测试评论分析"""
    comments_data = [
        {
            'id': '1',
            'text': 'Great video! Very helpful.',
            'author': 'User1',
            'like_count': 5,
            'is_author_reply': False
        },
        {
            'id': '2',
            'text': 'Thanks for watching!',
            'author': 'Channel Owner',
            'like_count': 2,
            'is_author_reply': True
        }
    ]
    
    video_info = {
        'channel_id': 'channel123',
        'title': 'Test Video'
    }
    
    with patch.object(analyzer.client.chat.completions, 'create') as mock_create:
        mock_create.return_value = Mock(
            choices=[Mock(message=Mock(content='{"sentiment_distribution": {"positive": 2}}'))]
        )
        
        result = await analyzer.analyze_comments(comments_data, video_info)
        
        assert isinstance(result, CommentInsights)
        assert result.total_comments == 2
        assert result.author_engagement.total_replies == 1

def test_clean_comment_text(analyzer):
    """测试评论文本清理"""
    dirty_text = "Great    video!!! Check out https://example.com"
    clean_text = analyzer._clean_comment_text(dirty_text)
    
    assert "https://example.com" not in clean_text
    assert "Great video!!!" in clean_text
```

## 交付物清单

- [ ] 评论分析器核心类 (app/services/comment_analyzer.py)
- [ ] 数据模型定义 (CommentInsights, AuthorEngagement等)
- [ ] Celery任务实现 (app/tasks/comment_analysis.py)
- [ ] 情感分析功能
- [ ] 主题提取功能
- [ ] 作者互动分析功能
- [ ] 垃圾评论检测功能
- [ ] 评论质量评估功能
- [ ] 错误处理和日志记录
- [ ] 单元测试文件

## 关键接口

完成此任务后，需要为后续任务提供：
- 结构化的评论分析结果
- 作者互动质量数据
- 观众反馈洞察
- 评论主题和情感分布

## 预估时间

- 开发时间: 2-3天
- 测试时间: 1天
- 算法优化: 0.5天
- 文档时间: 0.5天
- 总计: 4-5天

## 注意事项

1. 确保作者回复识别的准确性
2. 处理多语言评论的情感分析
3. 实现有效的垃圾评论过滤
4. 优化大量评论的处理性能
5. 保护用户隐私和数据安全

这是提供客观视频评价的重要模块，请确保分析结果的准确性和有用性。
