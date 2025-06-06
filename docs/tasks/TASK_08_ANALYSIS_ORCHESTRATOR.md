# Task 8: 分析编排器

## 任务概述

实现分析编排器，协调和管理整个YouTube视频分析流程。负责任务调度、进度跟踪、错误处理和结果聚合，确保各个分析模块按正确顺序执行并生成最终的综合分析报告。

## 目标

- 协调YouTube数据提取、转录、内容分析和评论分析
- 实现智能任务调度和依赖管理
- 提供实时进度跟踪和状态更新
- 处理分析过程中的错误和异常
- 生成综合分析报告

## 可交付成果

### 1. 分析编排器核心实现

```python
# backend/app/services/analysis_orchestrator.py
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum
import asyncio
import logging
from datetime import datetime

from app.core.config import settings
from app.tasks.extraction import extract_youtube_data
from app.tasks.transcription import transcribe_audio_task
from app.tasks.content_analysis import analyze_content_task
from app.tasks.comment_analysis import analyze_comments_task
from app.api.v1.websocket import send_progress_update, send_task_completed, send_task_failed
from app.models.task import AnalysisTask, TaskStatus
from app.core.database import get_db_session
from app.utils.exceptions import AnalysisError

class AnalysisStep(str, Enum):
    EXTRACTION = "extraction"
    TRANSCRIPTION = "transcription"
    CONTENT_ANALYSIS = "content_analysis"
    COMMENT_ANALYSIS = "comment_analysis"
    FINALIZATION = "finalization"

@dataclass
class AnalysisProgress:
    current_step: AnalysisStep
    overall_progress: int  # 0-100
    step_progress: int     # 0-100
    estimated_time_remaining: int  # seconds
    message: str

class AnalysisOrchestrator:
    """分析编排器，协调整个分析流程"""
    
    def __init__(self):
        self.step_weights = {
            AnalysisStep.EXTRACTION: 20,
            AnalysisStep.TRANSCRIPTION: 30,
            AnalysisStep.CONTENT_ANALYSIS: 25,
            AnalysisStep.COMMENT_ANALYSIS: 20,
            AnalysisStep.FINALIZATION: 5
        }
    
    async def run_analysis(self, task_id: str, youtube_url: str, options: Dict[str, Any]):
        """运行完整的分析流程"""
        try:
            logging.info(f"Starting analysis orchestration for task {task_id}")
            
            # 更新任务状态
            await self._update_task_status(task_id, TaskStatus.PROCESSING, "开始分析")
            
            # 步骤1: YouTube数据提取
            await self._run_extraction_step(task_id, youtube_url, options)
            
            # 步骤2: 音频转录（如果需要）
            if self._should_transcribe(options):
                await self._run_transcription_step(task_id, options)
            
            # 步骤3和4: 并行执行内容分析和评论分析
            await self._run_parallel_analysis_steps(task_id, options)
            
            # 步骤5: 最终化和报告生成
            await self._run_finalization_step(task_id, options)
            
            # 完成分析
            await self._complete_analysis(task_id)
            
            logging.info(f"Analysis orchestration completed for task {task_id}")
            
        except Exception as e:
            logging.error(f"Analysis orchestration failed for task {task_id}: {e}")
            await self._handle_analysis_failure(task_id, str(e))
            raise
    
    async def _run_extraction_step(self, task_id: str, youtube_url: str, options: Dict[str, Any]):
        """执行数据提取步骤"""
        await self._update_progress(
            task_id, 
            AnalysisStep.EXTRACTION, 
            0, 
            "开始YouTube数据提取"
        )
        
        try:
            # 启动提取任务
            extraction_result = await asyncio.get_event_loop().run_in_executor(
                None,
                extract_youtube_data.apply,
                [task_id, youtube_url, options]
            )
            
            # 等待任务完成
            result = extraction_result.get()
            
            await self._update_progress(
                task_id,
                AnalysisStep.EXTRACTION,
                100,
                "YouTube数据提取完成"
            )
            
            logging.info(f"Extraction completed for task {task_id}")
            
        except Exception as e:
            logging.error(f"Extraction failed for task {task_id}: {e}")
            raise AnalysisError(f"数据提取失败: {str(e)}")
    
    async def _run_transcription_step(self, task_id: str, options: Dict[str, Any]):
        """执行音频转录步骤"""
        await self._update_progress(
            task_id,
            AnalysisStep.TRANSCRIPTION,
            0,
            "开始音频转录"
        )
        
        try:
            # 获取音频文件路径
            audio_file_path = await self._get_audio_file_path(task_id)
            
            # 启动转录任务
            transcription_result = await asyncio.get_event_loop().run_in_executor(
                None,
                transcribe_audio_task.apply,
                [task_id, audio_file_path, options]
            )
            
            # 等待任务完成
            result = transcription_result.get()
            
            await self._update_progress(
                task_id,
                AnalysisStep.TRANSCRIPTION,
                100,
                "音频转录完成"
            )
            
            logging.info(f"Transcription completed for task {task_id}")
            
        except Exception as e:
            logging.error(f"Transcription failed for task {task_id}: {e}")
            raise AnalysisError(f"音频转录失败: {str(e)}")
    
    async def _run_parallel_analysis_steps(self, task_id: str, options: Dict[str, Any]):
        """并行执行内容分析和评论分析"""
        await self._update_progress(
            task_id,
            AnalysisStep.CONTENT_ANALYSIS,
            0,
            "开始内容和评论分析"
        )
        
        try:
            # 创建并行任务
            tasks = []
            
            # 内容分析任务
            if self._should_analyze_content(options):
                content_task = asyncio.get_event_loop().run_in_executor(
                    None,
                    analyze_content_task.apply,
                    [task_id, options]
                )
                tasks.append(("content", content_task))
            
            # 评论分析任务
            if self._should_analyze_comments(options):
                comment_task = asyncio.get_event_loop().run_in_executor(
                    None,
                    analyze_comments_task.apply,
                    [task_id, options]
                )
                tasks.append(("comment", comment_task))
            
            # 等待所有任务完成
            if tasks:
                results = await asyncio.gather(*[task[1] for task in tasks], return_exceptions=True)
                
                # 检查结果
                for i, (task_type, _) in enumerate(tasks):
                    result = results[i]
                    if isinstance(result, Exception):
                        logging.error(f"{task_type} analysis failed: {result}")
                        raise AnalysisError(f"{task_type}分析失败: {str(result)}")
                    else:
                        logging.info(f"{task_type} analysis completed for task {task_id}")
            
            await self._update_progress(
                task_id,
                AnalysisStep.CONTENT_ANALYSIS,
                100,
                "内容和评论分析完成"
            )
            
        except Exception as e:
            logging.error(f"Parallel analysis failed for task {task_id}: {e}")
            raise AnalysisError(f"分析失败: {str(e)}")
    
    async def _run_finalization_step(self, task_id: str, options: Dict[str, Any]):
        """执行最终化步骤"""
        await self._update_progress(
            task_id,
            AnalysisStep.FINALIZATION,
            0,
            "生成最终报告"
        )
        
        try:
            # 聚合所有分析结果
            final_report = await self._generate_final_report(task_id)
            
            # 保存最终报告
            await self._save_final_report(task_id, final_report)
            
            await self._update_progress(
                task_id,
                AnalysisStep.FINALIZATION,
                100,
                "最终报告生成完成"
            )
            
            logging.info(f"Finalization completed for task {task_id}")
            
        except Exception as e:
            logging.error(f"Finalization failed for task {task_id}: {e}")
            raise AnalysisError(f"报告生成失败: {str(e)}")
    
    async def _generate_final_report(self, task_id: str) -> Dict[str, Any]:
        """生成最终综合报告"""
        async with get_db_session() as db:
            from sqlalchemy import select
            result = await db.execute(
                select(AnalysisTask.result_data).where(AnalysisTask.id == task_id)
            )
            task_data = result.scalar()
        
        if not task_data:
            raise AnalysisError("Task data not found")
        
        # 提取各部分数据
        video_info = task_data.get('video_info', {})
        transcription = task_data.get('transcription', {})
        content_analysis = task_data.get('content_analysis', {})
        comment_analysis = task_data.get('comment_analysis', {})
        
        # 生成综合洞察
        insights = await self._generate_comprehensive_insights(
            video_info, transcription, content_analysis, comment_analysis
        )
        
        # 构建最终报告
        final_report = {
            'summary': {
                'video_title': video_info.get('title', ''),
                'duration': video_info.get('duration', 0),
                'view_count': video_info.get('view_count', 0),
                'analysis_timestamp': datetime.utcnow().isoformat()
            },
            'content_insights': {
                'key_points': content_analysis.get('key_points', []),
                'topics': content_analysis.get('topics', []),
                'sentiment': content_analysis.get('sentiment', {}),
                'summary': content_analysis.get('summary', '')
            },
            'comment_insights': {
                'total_comments': comment_analysis.get('total_comments', 0),
                'sentiment_distribution': comment_analysis.get('sentiment_distribution', {}),
                'author_engagement': comment_analysis.get('author_reply_analysis', {}),
                'top_themes': comment_analysis.get('top_themes', [])
            },
            'comprehensive_insights': insights,
            'recommendations': await self._generate_recommendations(
                content_analysis, comment_analysis
            ),
            'metadata': {
                'analysis_version': '1.0.0',
                'processing_time': self._calculate_processing_time(task_id),
                'data_sources': ['youtube_api', 'whisper', 'openai_gpt']
            }
        }
        
        return final_report
    
    async def _generate_comprehensive_insights(
        self, 
        video_info: Dict[str, Any],
        transcription: Dict[str, Any],
        content_analysis: Dict[str, Any],
        comment_analysis: Dict[str, Any]
    ) -> List[str]:
        """生成综合洞察"""
        insights = []
        
        # 内容质量洞察
        if content_analysis.get('structure', {}).get('coherence_score', 0) > 0.8:
            insights.append("视频内容结构清晰，逻辑性强")
        
        # 观众反馈洞察
        comment_sentiment = comment_analysis.get('avg_sentiment', 0)
        if comment_sentiment > 0.3:
            insights.append("观众反馈整体积极正面")
        elif comment_sentiment < -0.3:
            insights.append("观众反馈存在较多负面意见")
        
        # 作者互动洞察
        author_engagement = comment_analysis.get('author_reply_analysis', {})
        if author_engagement.get('engagement_quality', 0) > 0.7:
            insights.append("作者与观众互动质量较高")
        
        # 内容与反馈一致性
        content_sentiment = content_analysis.get('sentiment', {}).get('overall', 0)
        if abs(content_sentiment - comment_sentiment) < 0.2:
            insights.append("视频内容与观众反馈情感倾向一致")
        
        return insights
    
    async def _generate_recommendations(
        self,
        content_analysis: Dict[str, Any],
        comment_analysis: Dict[str, Any]
    ) -> List[str]:
        """生成改进建议"""
        recommendations = []
        
        # 基于内容分析的建议
        structure = content_analysis.get('structure', {})
        if structure.get('flow_quality', 0) < 0.6:
            recommendations.append("建议优化视频内容结构，提高逻辑流畅性")
        
        # 基于评论分析的建议
        author_replies = comment_analysis.get('author_reply_analysis', {})
        if author_replies.get('reply_rate', 0) < 0.1:
            recommendations.append("建议增加与观众的互动，提高回复率")
        
        # 基于争议话题的建议
        controversial_topics = comment_analysis.get('controversial_topics', [])
        if controversial_topics:
            recommendations.append("注意到一些争议话题，建议在未来内容中澄清相关观点")
        
        return recommendations
    
    async def _update_progress(
        self, 
        task_id: str, 
        step: AnalysisStep, 
        step_progress: int, 
        message: str
    ):
        """更新分析进度"""
        # 计算总体进度
        completed_weight = sum(
            self.step_weights[s] for s in AnalysisStep 
            if s.value < step.value
        )
        current_step_weight = self.step_weights[step]
        overall_progress = completed_weight + (current_step_weight * step_progress // 100)
        
        # 发送进度更新
        await send_progress_update(task_id, overall_progress, message)
        
        # 更新数据库
        await self._update_task_status(task_id, TaskStatus.PROCESSING, message, overall_progress)
    
    async def _update_task_status(
        self, 
        task_id: str, 
        status: TaskStatus, 
        message: str, 
        progress: int = None
    ):
        """更新任务状态"""
        async with get_db_session() as db:
            from sqlalchemy import update
            update_data = {
                'status': status,
                'current_step': message,
                'updated_at': datetime.utcnow()
            }
            if progress is not None:
                update_data['progress'] = progress
            
            await db.execute(
                update(AnalysisTask)
                .where(AnalysisTask.id == task_id)
                .values(**update_data)
            )
            await db.commit()
    
    async def _complete_analysis(self, task_id: str):
        """完成分析"""
        await self._update_task_status(task_id, TaskStatus.COMPLETED, "分析完成", 100)
        
        # 获取最终结果
        async with get_db_session() as db:
            from sqlalchemy import select
            result = await db.execute(
                select(AnalysisTask.result_data).where(AnalysisTask.id == task_id)
            )
            final_result = result.scalar()
        
        # 发送完成通知
        await send_task_completed(task_id, final_result)
    
    async def _handle_analysis_failure(self, task_id: str, error_message: str):
        """处理分析失败"""
        await self._update_task_status(task_id, TaskStatus.FAILED, f"分析失败: {error_message}")
        await send_task_failed(task_id, {"message": error_message})
    
    def _should_transcribe(self, options: Dict[str, Any]) -> bool:
        """判断是否需要转录"""
        analysis_type = options.get('type', 'comprehensive')
        return analysis_type in ['content', 'comprehensive']
    
    def _should_analyze_content(self, options: Dict[str, Any]) -> bool:
        """判断是否需要内容分析"""
        analysis_type = options.get('type', 'comprehensive')
        return analysis_type in ['content', 'comprehensive']
    
    def _should_analyze_comments(self, options: Dict[str, Any]) -> bool:
        """判断是否需要评论分析"""
        analysis_type = options.get('type', 'comprehensive')
        include_comments = options.get('include_comments', True)
        return analysis_type in ['comments', 'comprehensive'] and include_comments
    
    async def estimate_duration(self, options: Dict[str, Any]) -> int:
        """估算分析时长（秒）"""
        base_time = 60  # 基础时间1分钟
        
        if self._should_transcribe(options):
            base_time += 120  # 转录增加2分钟
        
        if self._should_analyze_content(options):
            base_time += 90   # 内容分析增加1.5分钟
        
        if self._should_analyze_comments(options):
            base_time += 60   # 评论分析增加1分钟
        
        return base_time
```

## 依赖关系

### 前置条件
- Task 1: 项目配置管理（必须完成）
- Task 2: 后端API框架（必须完成）
- Task 4: YouTube数据提取（必须完成）
- Task 5: 音频转录服务（必须完成）
- Task 6: 内容分析模块（必须完成）
- Task 7: 评论分析模块（必须完成）

### 阻塞任务
- Task 9: 结果展示（需要编排器提供完整结果）

## 验收标准

### 功能验收
- [ ] 任务调度和依赖管理正确
- [ ] 实时进度跟踪准确
- [ ] 错误处理和恢复机制完善
- [ ] 最终报告生成完整
- [ ] 并行任务执行正常
- [ ] WebSocket通信稳定

### 技术验收
- [ ] 整体分析时间 < 5分钟（标准视频）
- [ ] 内存使用合理（< 4GB）
- [ ] 任务失败率 < 5%
- [ ] 进度更新延迟 < 1秒
- [ ] 并发任务处理能力

### 质量验收
- [ ] 单元测试覆盖率 ≥ 80%
- [ ] 集成测试覆盖主要流程
- [ ] 错误场景测试通过
- [ ] 性能测试通过
- [ ] 代码遵循项目规范

## 测试要求

### 单元测试
```python
# tests/test_analysis_orchestrator.py
import pytest
from unittest.mock import Mock, patch, AsyncMock
from app.services.analysis_orchestrator import AnalysisOrchestrator

@pytest.fixture
def orchestrator():
    return AnalysisOrchestrator()

@pytest.mark.asyncio
async def test_run_analysis_complete_flow(orchestrator):
    """测试完整分析流程"""
    task_id = "test_task_id"
    youtube_url = "https://youtube.com/watch?v=test"
    options = {"type": "comprehensive", "include_comments": True}
    
    with patch.object(orchestrator, '_run_extraction_step') as mock_extraction:
        with patch.object(orchestrator, '_run_transcription_step') as mock_transcription:
            with patch.object(orchestrator, '_run_parallel_analysis_steps') as mock_parallel:
                with patch.object(orchestrator, '_run_finalization_step') as mock_finalization:
                    with patch.object(orchestrator, '_complete_analysis') as mock_complete:
                        
                        await orchestrator.run_analysis(task_id, youtube_url, options)
                        
                        mock_extraction.assert_called_once()
                        mock_transcription.assert_called_once()
                        mock_parallel.assert_called_once()
                        mock_finalization.assert_called_once()
                        mock_complete.assert_called_once()

@pytest.mark.asyncio
async def test_estimate_duration(orchestrator):
    """测试时长估算"""
    options_comprehensive = {"type": "comprehensive", "include_comments": True}
    options_content_only = {"type": "content", "include_comments": False}
    
    duration_comprehensive = await orchestrator.estimate_duration(options_comprehensive)
    duration_content = await orchestrator.estimate_duration(options_content_only)
    
    assert duration_comprehensive > duration_content
    assert duration_comprehensive > 200  # 至少3分钟多
```

## 预估工作量

- **开发时间**: 3-4天
- **测试时间**: 2天
- **集成调试**: 1天
- **文档时间**: 0.5天
- **总计**: 6.5-7.5天

## 关键路径

此任务在关键路径上，是整个系统的核心协调组件，完成后将为Task 9提供完整的分析结果。

## 交付检查清单

- [ ] 分析编排器核心功能已实现
- [ ] 任务调度机制已完成
- [ ] 进度跟踪系统已实现
- [ ] 错误处理机制已完善
- [ ] 最终报告生成已实现
- [ ] 并行任务执行已实现
- [ ] 单元测试和集成测试通过
- [ ] 性能测试通过
- [ ] 代码已提交并通过CI检查

## 后续任务接口

完成此任务后，为后续任务提供：
- 完整的分析流程协调
- 实时进度跟踪能力
- 综合分析报告
- 错误处理和恢复机制
- 任务状态管理

这些将被Task 9（结果展示）直接使用，为用户提供完整的分析体验。
