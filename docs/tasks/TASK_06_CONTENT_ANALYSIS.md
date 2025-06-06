# Task 6: 内容分析模块

## 任务概述

实现视频内容分析模块，使用LLM对转录文本进行深度分析，提取关键要点、主题分类、情感分析和内容结构识别。这是整个分析流程的核心组件，为用户提供有价值的内容洞察。

## 目标

- 集成LLM进行智能内容分析
- 实现关键要点提取和主题分类
- 进行情感分析和语调识别
- 分析内容结构和组织方式
- 生成结构化的分析报告

## 可交付成果

### 1. 内容分析器核心实现

基于 <ref_file file="/home/ubuntu/repos/generic-ai-agent/src/agent_core/response_router.py" /> 的插件化架构模式：

```python
# backend/app/services/content_analyzer.py
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
import openai
import asyncio
import logging

from app.core.config import settings
from app.utils.exceptions import ExternalServiceError, AnalysisError

class ContentType(str, Enum):
    EDUCATIONAL = "educational"
    ENTERTAINMENT = "entertainment"
    NEWS = "news"
    REVIEW = "review"
    TUTORIAL = "tutorial"
    DISCUSSION = "discussion"
    OTHER = "other"

@dataclass
class KeyPoint:
    text: str
    timestamp: float
    importance: float  # 0-1
    category: str

@dataclass
class ContentAnalysis:
    key_points: List[KeyPoint]
    topics: List[Dict[str, Any]]
    sentiment: Dict[str, Any]
    structure: Dict[str, Any]
    summary: str
    metadata: Dict[str, Any]

class BaseContentAnalyzer(ABC):
    """内容分析器基类，遵循插件化架构"""
    
    def __init__(self, name: str, version: str):
        self.name = name
        self.version = version
        self.config = {}
    
    @abstractmethod
    async def analyze(self, transcript_data: Dict[str, Any], video_info: Dict[str, Any]) -> ContentAnalysis:
        """执行内容分析"""
        pass
    
    @abstractmethod
    def get_progress_steps(self) -> List[str]:
        """返回分析步骤列表"""
        pass

class LLMContentAnalyzer(BaseContentAnalyzer):
    """基于LLM的内容分析器"""
    
    def __init__(self):
        super().__init__("llm_content_analyzer", "1.0.0")
        self.client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model or "gpt-4"
    
    async def analyze(self, transcript_data: Dict[str, Any], video_info: Dict[str, Any]) -> ContentAnalysis:
        """执行完整的内容分析"""
        try:
            full_text = transcript_data.get('full_text', '')
            
            # 并行执行各种分析
            tasks = [
                self._extract_key_points(full_text, video_info),
                self._analyze_topics(full_text),
                self._analyze_sentiment(full_text),
                self._analyze_structure(full_text, video_info)
            ]
            
            key_points, topics, sentiment, structure = await asyncio.gather(*tasks)
            
            # 生成总结
            summary = await self._generate_summary(full_text, video_info, key_points)
            
            return ContentAnalysis(
                key_points=key_points,
                topics=topics,
                sentiment=sentiment,
                structure=structure,
                summary=summary,
                metadata={
                    "analysis_model": self.model,
                    "transcript_language": transcript_data.get('language'),
                    "analysis_timestamp": asyncio.get_event_loop().time()
                }
            )
            
        except Exception as e:
            logging.error(f"Content analysis failed: {e}")
            raise AnalysisError(f"Content analysis failed: {str(e)}")
    
    async def _extract_key_points(self, text: str, video_info: Dict[str, Any]) -> List[KeyPoint]:
        """提取关键要点"""
        prompt = f"""
        分析以下视频转录内容，提取最重要的关键要点。

        视频标题: {video_info.get('title', '')}
        转录内容: {text}

        请提取5-10个最重要的关键要点，每个要点包括：
        1. 要点内容（简洁明了）
        2. 重要性评分（0-1）
        3. 所属类别
        4. 大概出现的时间点

        以JSON格式返回。
        """
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2000,
                temperature=0.3
            )
            
            import json
            result = json.loads(response.choices[0].message.content)
            
            key_points = []
            for kp in result.get("key_points", []):
                key_points.append(KeyPoint(
                    text=kp.get("text", ""),
                    timestamp=kp.get("timestamp", 0),
                    importance=kp.get("importance", 0.5),
                    category=kp.get("category", "其他")
                ))
            
            return key_points
            
        except Exception as e:
            logging.error(f"Key points extraction failed: {e}")
            return []
    
    def get_progress_steps(self) -> List[str]:
        """返回分析步骤"""
        return [
            "提取关键要点",
            "分析主题内容", 
            "情感倾向分析",
            "内容结构分析",
            "生成内容总结"
        ]

# 分析器注册中心
class ContentAnalyzerRegistry:
    def __init__(self):
        self._analyzers: Dict[str, BaseContentAnalyzer] = {}
    
    def register(self, analyzer: BaseContentAnalyzer):
        self._analyzers[analyzer.name] = analyzer
    
    def get_analyzer(self, name: str) -> Optional[BaseContentAnalyzer]:
        return self._analyzers.get(name)
    
    def get_default_analyzer(self) -> BaseContentAnalyzer:
        if "llm_content_analyzer" in self._analyzers:
            return self._analyzers["llm_content_analyzer"]
        raise AnalysisError("No content analyzer available")

# 全局注册中心实例
content_analyzer_registry = ContentAnalyzerRegistry()
content_analyzer_registry.register(LLMContentAnalyzer())
```

### 2. Celery任务集成

```python
# backend/app/tasks/content_analysis.py
from celery import current_task
from app.core.celery_app import celery_app
from app.services.content_analyzer import content_analyzer_registry
from app.api.v1.websocket import send_progress_update
from app.models.task import AnalysisTask, TaskStatus
from app.core.database import get_db_session
from sqlalchemy import update, select
import logging

@celery_app.task(bind=True)
def analyze_content_task(self, task_id: str, options: dict):
    """内容分析Celery任务"""
    
    async def _analyze():
        try:
            analyzer = content_analyzer_registry.get_default_analyzer()
            
            # 更新任务状态
            async with get_db_session() as db:
                await db.execute(
                    update(AnalysisTask)
                    .where(AnalysisTask.id == task_id)
                    .values(
                        status=TaskStatus.PROCESSING,
                        current_step="内容分析"
                    )
                )
                await db.commit()
            
            # 获取转录结果和视频信息
            async with get_db_session() as db:
                result = await db.execute(
                    select(AnalysisTask.result_data).where(AnalysisTask.id == task_id)
                )
                task_data = result.scalar()
                
                if not task_data or 'transcription' not in task_data:
                    raise AnalysisError("Transcription data not found")
                
                transcript_data = task_data['transcription']['transcript']
                video_info_data = task_data.get('video_info', {})
            
            # 执行分析，跟踪进度
            progress_steps = analyzer.get_progress_steps()
            step_progress = 80 // len(progress_steps)
            
            for i, step in enumerate(progress_steps):
                await send_progress_update(
                    task_id, 
                    10 + (i * step_progress), 
                    step
                )
            
            # 执行分析
            analysis_result = await analyzer.analyze(transcript_data, video_info_data)
            
            await send_progress_update(task_id, 90, "保存分析结果")
            
            # 序列化结果
            content_analysis_data = {
                'key_points': [
                    {
                        'text': kp.text,
                        'timestamp': kp.timestamp,
                        'importance': kp.importance,
                        'category': kp.category
                    }
                    for kp in analysis_result.key_points
                ],
                'topics': analysis_result.topics,
                'sentiment': analysis_result.sentiment,
                'structure': analysis_result.structure,
                'summary': analysis_result.summary,
                'metadata': analysis_result.metadata
            }
            
            # 更新数据库
            async with get_db_session() as db:
                result = await db.execute(
                    select(AnalysisTask.result_data).where(AnalysisTask.id == task_id)
                )
                existing_data = result.scalar() or {}
                
                existing_data['content_analysis'] = content_analysis_data
                
                await db.execute(
                    update(AnalysisTask)
                    .where(AnalysisTask.id == task_id)
                    .values(result_data=existing_data)
                )
                await db.commit()
            
            await send_progress_update(task_id, 100, "内容分析完成")
            
            return content_analysis_data
            
        except Exception as e:
            logging.error(f"Content analysis failed for task {task_id}: {e}")
            
            async with get_db_session() as db:
                await db.execute(
                    update(AnalysisTask)
                    .where(AnalysisTask.id == task_id)
                    .values(
                        status=TaskStatus.FAILED,
                        error_message=f"内容分析失败: {str(e)}"
                    )
                )
                await db.commit()
            
            raise
    
    import asyncio
    return asyncio.run(_analyze())
```

## 依赖关系

### 前置条件
- Task 1: 项目配置管理（必须完成）
- Task 2: 后端API框架（必须完成）
- Task 5: 音频转录服务（必须完成，需要转录文本）

### 阻塞任务
- Task 8: 分析编排器（需要内容分析服务）
- Task 9: 结果展示（需要分析结果）

## 验收标准

### 功能验收
- [ ] LLM集成正常工作
- [ ] 关键要点提取准确且有意义
- [ ] 主题分析覆盖主要内容
- [ ] 情感分析结果合理
- [ ] 内容结构识别正确
- [ ] 总结生成质量高

### 技术验收
- [ ] 分析准确率 ≥ 85%
- [ ] 处理时间 < 2分钟（标准视频）
- [ ] API调用成本控制合理
- [ ] 错误处理完善
- [ ] 插件化架构可扩展

### 质量验收
- [ ] 单元测试覆盖率 ≥ 80%
- [ ] 多语言内容测试通过
- [ ] 不同类型视频测试通过
- [ ] 长视频处理稳定
- [ ] 代码遵循项目规范

## 测试要求

### 单元测试
```python
# tests/test_content_analyzer.py
import pytest
from unittest.mock import Mock, patch, AsyncMock
from app.services.content_analyzer import LLMContentAnalyzer

@pytest.fixture
def analyzer():
    with patch('openai.AsyncOpenAI'):
        return LLMContentAnalyzer()

@pytest.mark.asyncio
async def test_extract_key_points(analyzer):
    """测试关键要点提取"""
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = '{"key_points": [{"text": "测试要点", "importance": 0.9, "category": "主要观点", "timestamp": 60}]}'
    
    with patch.object(analyzer.client.chat.completions, 'create', return_value=mock_response):
        result = await analyzer._extract_key_points("测试文本", {"title": "测试视频"})
        
        assert len(result) == 1
        assert result[0].text == "测试要点"
        assert result[0].importance == 0.9

@pytest.mark.asyncio
async def test_analyze_complete_flow(analyzer):
    """测试完整分析流程"""
    transcript_data = {
        'full_text': '这是一个测试视频的转录内容',
        'language': 'zh-CN'
    }
    video_info = {'title': '测试视频'}
    
    with patch.object(analyzer, '_extract_key_points', return_value=[]):
        with patch.object(analyzer, '_analyze_topics', return_value=[]):
            with patch.object(analyzer, '_analyze_sentiment', return_value={}):
                with patch.object(analyzer, '_analyze_structure', return_value={}):
                    with patch.object(analyzer, '_generate_summary', return_value="测试总结"):
                        result = await analyzer.analyze(transcript_data, video_info)
                        
                        assert result.summary == "测试总结"
                        assert result.metadata['analysis_model'] == analyzer.model
```

## 预估工作量

- **开发时间**: 3-4天
- **测试时间**: 1.5天
- **LLM提示优化**: 1天
- **文档时间**: 0.5天
- **总计**: 6天

## 关键路径

此任务在关键路径上，完成后将为Task 8（分析编排器）和Task 9（结果展示）提供核心分析能力。

## 交付检查清单

- [ ] 内容分析器核心功能已实现
- [ ] LLM集成已完成
- [ ] 关键要点提取已实现
- [ ] 主题分析已实现
- [ ] 情感分析已实现
- [ ] 内容结构分析已实现
- [ ] 总结生成已实现
- [ ] Celery任务集成已完成
- [ ] 插件化架构已实现
- [ ] 单元测试通过
- [ ] 代码已提交并通过CI检查

## 后续任务接口

完成此任务后，为后续任务提供：
- 结构化的内容分析结果
- 关键要点和主题数据
- 情感分析评分
- 内容总结文本
- 可扩展的分析器架构

这些将被Task 8（分析编排器）和Task 9（结果展示）直接使用。
