# Task 8: 分析编排器 - Sub-Session Prompt

## 必读文档

**重要提示**: 开始此任务前，你必须阅读并理解以下文档：

### 核心协调文档
- `docs/TASK_COORDINATION.md` - 整体任务依赖关系和项目结构
- `docs/ARCHITECTURE_OVERVIEW.md` - 系统架构和技术栈
- `docs/CODING_STANDARDS.md` - 代码格式、命名规范和最佳实践
- `docs/API_SPECIFICATIONS.md` - 完整API接口定义

### 任务专用文档
- `docs/tasks/TASK_08_ANALYSIS_ORCHESTRATOR.md` - 详细任务要求和验收标准
- `docs/contracts/orchestrator_contract.md` - 分析编排器接口规范

### 参考文档
- `docs/DEVELOPMENT_SETUP.md` - 开发环境配置
- `docs/PROGRESS_TRACKER.md` - 进度跟踪和任务状态更新

### 依赖关系
- Task 1 (项目配置) 必须先完成
- Task 2 (后端API) 必须先完成
- Task 4 (YouTube数据提取) 必须先完成
- Task 5 (音频转录) 必须先完成
- Task 6 (内容分析) 必须先完成
- Task 7 (评论分析) 必须先完成
- 查看所有相关的contract文档了解各模块接口

## 项目背景

你正在为YouTube视频分析工具构建分析编排器。这个模块是整个分析流程的核心协调器，需要：
- 协调所有分析步骤的执行顺序
- 管理任务状态和进度跟踪
- 处理错误和异常情况
- 提供实时进度更新
- 生成最终的综合分析报告

## 任务目标

实现完整的分析编排服务，包括任务调度、进度管理、错误处理、结果聚合和实时通信。

## 具体要求

### 1. 分析编排器核心实现
参考 <ref_file file="/home/ubuntu/repos/generic-ai-agent/src/agent_core/response_router.py" /> 的任务路由模式：

```python
# backend/app/services/analysis_orchestrator.py
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import asyncio
import logging
from datetime import datetime, timedelta

from app.core.config import settings
from app.core.database import get_db_session
from app.models.task import AnalysisTask, TaskStatus
from app.api.v1.websocket import send_progress_update, send_task_completed, send_task_failed
from app.tasks.extraction import extract_youtube_data
from app.tasks.transcription import transcribe_audio_task
from app.tasks.content_analysis import analyze_content_task
from app.tasks.comment_analysis import analyze_comments_task
from app.utils.exceptions import ExternalServiceError
from sqlalchemy import update, select

class AnalysisStep(str, Enum):
    EXTRACTION = "extraction"
    TRANSCRIPTION = "transcription"
    CONTENT_ANALYSIS = "content_analysis"
    COMMENT_ANALYSIS = "comment_analysis"
    FINALIZATION = "finalization"

@dataclass
class StepResult:
    step: AnalysisStep
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    duration: Optional[float] = None

@dataclass
class AnalysisProgress:
    current_step: AnalysisStep
    progress_percentage: int
    estimated_time_remaining: Optional[int] = None
    steps_completed: List[AnalysisStep] = None
    steps_failed: List[AnalysisStep] = None

class AnalysisOrchestrator:
    """分析编排器"""
    
    def __init__(self):
        self.step_weights = {
            AnalysisStep.EXTRACTION: 25,
            AnalysisStep.TRANSCRIPTION: 30,
            AnalysisStep.CONTENT_ANALYSIS: 25,
            AnalysisStep.COMMENT_ANALYSIS: 15,
            AnalysisStep.FINALIZATION: 5
        }
    
    async def run_analysis(self, task_id: str, youtube_url: str, options: Dict[str, Any]):
        """运行完整的分析流程"""
        start_time = datetime.utcnow()
        step_results = {}
        
        try:
            logging.info(f"Starting analysis for task {task_id}")
            
            # 更新任务状态
            await self._update_task_status(task_id, TaskStatus.PROCESSING, "开始分析")
            
            # 步骤1: YouTube数据提取
            extraction_result = await self._run_extraction_step(task_id, youtube_url, options)
            step_results[AnalysisStep.EXTRACTION] = extraction_result
            
            if not extraction_result.success:
                raise ExternalServiceError(f"数据提取失败: {extraction_result.error}")
            
            # 步骤2: 音频转录
            transcription_result = await self._run_transcription_step(task_id, extraction_result.data, options)
            step_results[AnalysisStep.TRANSCRIPTION] = transcription_result
            
            if not transcription_result.success:
                raise ExternalServiceError(f"音频转录失败: {transcription_result.error}")
            
            # 步骤3&4: 并行执行内容分析和评论分析
            content_result, comment_result = await self._run_parallel_analysis_steps(
                task_id, extraction_result.data, transcription_result.data, options
            )
            
            step_results[AnalysisStep.CONTENT_ANALYSIS] = content_result
            step_results[AnalysisStep.COMMENT_ANALYSIS] = comment_result
            
            # 步骤5: 生成最终报告
            final_result = await self._run_finalization_step(
                task_id, step_results, options
            )
            step_results[AnalysisStep.FINALIZATION] = final_result
            
            if not final_result.success:
                raise ExternalServiceError(f"报告生成失败: {final_result.error}")
            
            # 计算总耗时
            total_duration = (datetime.utcnow() - start_time).total_seconds()
            
            # 更新任务为完成状态
            await self._update_task_status(
                task_id, 
                TaskStatus.COMPLETED, 
                "分析完成",
                completed_at=datetime.utcnow()
            )
            
            # 发送完成通知
            await send_task_completed(task_id, final_result.data)
            
            logging.info(f"Analysis completed for task {task_id} in {total_duration:.2f}s")
            
        except Exception as e:
            logging.error(f"Analysis failed for task {task_id}: {e}")
            
            # 更新任务为失败状态
            await self._update_task_status(
                task_id,
                TaskStatus.FAILED,
                f"分析失败: {str(e)}"
            )
            
            # 发送失败通知
            await send_task_failed(task_id, {"message": str(e), "step_results": step_results})
            
            raise
    
    async def _run_extraction_step(self, task_id: str, youtube_url: str, options: Dict) -> StepResult:
        """执行数据提取步骤"""
        step_start = datetime.utcnow()
        
        try:
            await send_progress_update(task_id, 5, "开始YouTube数据提取")
            
            # 调用提取任务
            result = extract_youtube_data.delay(task_id, youtube_url, options)
            extraction_data = result.get(timeout=300)  # 5分钟超时
            
            duration = (datetime.utcnow() - step_start).total_seconds()
            
            await send_progress_update(task_id, 25, "数据提取完成")
            
            return StepResult(
                step=AnalysisStep.EXTRACTION,
                success=True,
                data=extraction_data,
                duration=duration
            )
            
        except Exception as e:
            duration = (datetime.utcnow() - step_start).total_seconds()
            logging.error(f"Extraction step failed: {e}")
            
            return StepResult(
                step=AnalysisStep.EXTRACTION,
                success=False,
                error=str(e),
                duration=duration
            )
    
    async def _run_transcription_step(self, task_id: str, extraction_data: Dict, options: Dict) -> StepResult:
        """执行音频转录步骤"""
        step_start = datetime.utcnow()
        
        try:
            await send_progress_update(task_id, 30, "开始音频转录")
            
            audio_file_path = extraction_data.get('audio_file_path')
            if not audio_file_path:
                raise ValueError("音频文件路径不存在")
            
            # 调用转录任务
            result = transcribe_audio_task.delay(task_id, audio_file_path, options)
            transcription_data = result.get(timeout=600)  # 10分钟超时
            
            duration = (datetime.utcnow() - step_start).total_seconds()
            
            await send_progress_update(task_id, 55, "音频转录完成")
            
            return StepResult(
                step=AnalysisStep.TRANSCRIPTION,
                success=True,
                data=transcription_data,
                duration=duration
            )
            
        except Exception as e:
            duration = (datetime.utcnow() - step_start).total_seconds()
            logging.error(f"Transcription step failed: {e}")
            
            return StepResult(
                step=AnalysisStep.TRANSCRIPTION,
                success=False,
                error=str(e),
                duration=duration
            )
    
    async def _run_parallel_analysis_steps(self, task_id: str, extraction_data: Dict, 
                                         transcription_data: Dict, options: Dict) -> tuple:
        """并行执行内容分析和评论分析"""
        await send_progress_update(task_id, 60, "开始内容和评论分析")
        
        # 准备任务
        content_task = asyncio.create_task(
            self._run_content_analysis(task_id, extraction_data, transcription_data, options)
        )
        
        comment_task = asyncio.create_task(
            self._run_comment_analysis(task_id, extraction_data, options)
        )
        
        # 等待两个任务完成
        content_result, comment_result = await asyncio.gather(
            content_task, comment_task, return_exceptions=True
        )
        
        # 处理异常结果
        if isinstance(content_result, Exception):
            content_result = StepResult(
                step=AnalysisStep.CONTENT_ANALYSIS,
                success=False,
                error=str(content_result)
            )
        
        if isinstance(comment_result, Exception):
            comment_result = StepResult(
                step=AnalysisStep.COMMENT_ANALYSIS,
                success=False,
                error=str(comment_result)
            )
        
        await send_progress_update(task_id, 85, "内容和评论分析完成")
        
        return content_result, comment_result
    
    async def _run_content_analysis(self, task_id: str, extraction_data: Dict, 
                                  transcription_data: Dict, options: Dict) -> StepResult:
        """执行内容分析"""
        step_start = datetime.utcnow()
        
        try:
            video_info = extraction_data.get('video_info', {})
            
            # 调用内容分析任务
            result = analyze_content_task.delay(
                task_id, transcription_data, video_info, options
            )
            content_data = result.get(timeout=300)  # 5分钟超时
            
            duration = (datetime.utcnow() - step_start).total_seconds()
            
            return StepResult(
                step=AnalysisStep.CONTENT_ANALYSIS,
                success=True,
                data=content_data,
                duration=duration
            )
            
        except Exception as e:
            duration = (datetime.utcnow() - step_start).total_seconds()
            logging.error(f"Content analysis step failed: {e}")
            
            return StepResult(
                step=AnalysisStep.CONTENT_ANALYSIS,
                success=False,
                error=str(e),
                duration=duration
            )
    
    async def _run_comment_analysis(self, task_id: str, extraction_data: Dict, options: Dict) -> StepResult:
        """执行评论分析"""
        step_start = datetime.utcnow()
        
        try:
            comments_data = extraction_data.get('comments', [])
            video_info = extraction_data.get('video_info', {})
            
            # 调用评论分析任务
            result = analyze_comments_task.delay(
                task_id, comments_data, video_info, options
            )
            comment_data = result.get(timeout=300)  # 5分钟超时
            
            duration = (datetime.utcnow() - step_start).total_seconds()
            
            return StepResult(
                step=AnalysisStep.COMMENT_ANALYSIS,
                success=True,
                data=comment_data,
                duration=duration
            )
            
        except Exception as e:
            duration = (datetime.utcnow() - step_start).total_seconds()
            logging.error(f"Comment analysis step failed: {e}")
            
            return StepResult(
                step=AnalysisStep.COMMENT_ANALYSIS,
                success=False,
                error=str(e),
                duration=duration
            )
    
    async def _run_finalization_step(self, task_id: str, step_results: Dict[AnalysisStep, StepResult], 
                                   options: Dict) -> StepResult:
        """生成最终分析报告"""
        step_start = datetime.utcnow()
        
        try:
            await send_progress_update(task_id, 90, "生成综合分析报告")
            
            # 聚合所有分析结果
            final_report = await self._generate_comprehensive_report(step_results, options)
            
            # 保存最终结果到数据库
            await self._save_final_result(task_id, final_report)
            
            duration = (datetime.utcnow() - step_start).total_seconds()
            
            await send_progress_update(task_id, 100, "分析报告生成完成")
            
            return StepResult(
                step=AnalysisStep.FINALIZATION,
                success=True,
                data=final_report,
                duration=duration
            )
            
        except Exception as e:
            duration = (datetime.utcnow() - step_start).total_seconds()
            logging.error(f"Finalization step failed: {e}")
            
            return StepResult(
                step=AnalysisStep.FINALIZATION,
                success=False,
                error=str(e),
                duration=duration
            )
    
    async def _generate_comprehensive_report(self, step_results: Dict[AnalysisStep, StepResult], 
                                           options: Dict) -> Dict[str, Any]:
        """生成综合分析报告"""
        report = {
            "summary": {},
            "content_insights": {},
            "comment_insights": {},
            "comprehensive_insights": [],
            "recommendations": [],
            "metadata": {
                "analysis_timestamp": datetime.utcnow().isoformat(),
                "analysis_duration": sum(
                    result.duration for result in step_results.values() 
                    if result.duration is not None
                ),
                "steps_completed": [
                    step.value for step, result in step_results.items() 
                    if result.success
                ],
                "steps_failed": [
                    step.value for step, result in step_results.items() 
                    if not result.success
                ]
            }
        }
        
        # 提取各步骤的结果
        extraction_result = step_results.get(AnalysisStep.EXTRACTION)
        transcription_result = step_results.get(AnalysisStep.TRANSCRIPTION)
        content_result = step_results.get(AnalysisStep.CONTENT_ANALYSIS)
        comment_result = step_results.get(AnalysisStep.COMMENT_ANALYSIS)
        
        # 构建摘要信息
        if extraction_result and extraction_result.success:
            video_info = extraction_result.data.get('video_info', {})
            report["summary"] = {
                "video_title": video_info.get('title'),
                "channel_title": video_info.get('channel_title'),
                "duration": video_info.get('duration'),
                "view_count": video_info.get('view_count'),
                "like_count": video_info.get('like_count'),
                "upload_date": video_info.get('upload_date'),
                "analysis_timestamp": report["metadata"]["analysis_timestamp"]
            }
        
        # 添加内容分析结果
        if content_result and content_result.success:
            report["content_insights"] = content_result.data
        
        # 添加评论分析结果
        if comment_result and comment_result.success:
            report["comment_insights"] = comment_result.data
        
        # 生成综合洞察
        report["comprehensive_insights"] = await self._generate_comprehensive_insights(
            content_result.data if content_result and content_result.success else {},
            comment_result.data if comment_result and comment_result.success else {}
        )
        
        # 生成综合建议
        report["recommendations"] = await self._generate_comprehensive_recommendations(
            content_result.data if content_result and content_result.success else {},
            comment_result.data if comment_result and comment_result.success else {}
        )
        
        return report
    
    async def _generate_comprehensive_insights(self, content_data: Dict, comment_data: Dict) -> List[str]:
        """生成综合洞察"""
        insights = []
        
        # 基于内容和评论的综合分析
        if content_data and comment_data:
            content_sentiment = content_data.get('sentiment_analysis', {}).get('overall_sentiment')
            comment_sentiment_dist = comment_data.get('sentiment_distribution', {})
            
            # 内容与评论情感对比
            if content_sentiment and comment_sentiment_dist:
                positive_comments = comment_sentiment_dist.get('positive', 0)
                total_comments = sum(comment_sentiment_dist.values())
                
                if total_comments > 0:
                    positive_ratio = positive_comments / total_comments
                    
                    if content_sentiment == 'positive' and positive_ratio > 0.7:
                        insights.append("视频内容积极正面，观众反馈也非常积极，内容与观众期望高度一致")
                    elif content_sentiment == 'positive' and positive_ratio < 0.3:
                        insights.append("视频内容积极，但观众反馈偏负面，可能存在内容与标题不符或观众期望落差")
        
        # 作者互动质量分析
        author_engagement = comment_data.get('author_engagement', {})
        if author_engagement:
            reply_rate = author_engagement.get('reply_rate', 0)
            engagement_quality = author_engagement.get('engagement_quality', 0)
            
            if reply_rate > 0.1 and engagement_quality > 0.7:
                insights.append("作者积极回复评论且互动质量高，有助于建立良好的观众关系")
            elif reply_rate < 0.05:
                insights.append("作者回复评论较少，建议增加与观众的互动以提升参与度")
        
        return insights
    
    async def _generate_comprehensive_recommendations(self, content_data: Dict, comment_data: Dict) -> List[str]:
        """生成综合建议"""
        recommendations = []
        
        # 基于内容分析的建议
        if content_data:
            content_recommendations = content_data.get('recommendations', [])
            recommendations.extend(content_recommendations)
        
        # 基于评论分析的建议
        if comment_data:
            comment_recommendations = comment_data.get('recommendations', [])
            recommendations.extend(comment_recommendations)
        
        # 去重并限制数量
        unique_recommendations = list(dict.fromkeys(recommendations))
        return unique_recommendations[:10]
    
    async def _save_final_result(self, task_id: str, final_report: Dict[str, Any]):
        """保存最终结果到数据库"""
        async with get_db_session() as db:
            await db.execute(
                update(AnalysisTask)
                .where(AnalysisTask.id == task_id)
                .values(result_data=final_report)
            )
            await db.commit()
    
    async def _update_task_status(self, task_id: str, status: TaskStatus, 
                                current_step: str, completed_at: Optional[datetime] = None):
        """更新任务状态"""
        update_data = {
            "status": status,
            "current_step": current_step,
            "updated_at": datetime.utcnow()
        }
        
        if completed_at:
            update_data["completed_at"] = completed_at
        
        async with get_db_session() as db:
            await db.execute(
                update(AnalysisTask)
                .where(AnalysisTask.id == task_id)
                .values(**update_data)
            )
            await db.commit()

# 全局实例
analysis_orchestrator = AnalysisOrchestrator()
```

## 验收标准

### 功能验收
- [ ] 任务调度正确执行
- [ ] 进度跟踪准确更新
- [ ] 错误处理机制完善
- [ ] 实时通信正常工作
- [ ] 结果聚合正确
- [ ] 最终报告生成完整

### 技术验收
- [ ] 整体分析时间 < 10分钟
- [ ] 并发任务处理正常
- [ ] 内存使用合理
- [ ] 错误恢复机制有效
- [ ] WebSocket连接稳定

### 质量验收
- [ ] 单元测试覆盖率 ≥ 80%
- [ ] 集成测试通过
- [ ] 异常情况测试通过
- [ ] 性能测试通过
- [ ] 代码遵循项目规范

## 测试要求

### 单元测试
```python
# tests/test_analysis_orchestrator.py
import pytest
from unittest.mock import Mock, patch, AsyncMock
from app.services.analysis_orchestrator import AnalysisOrchestrator, StepResult, AnalysisStep

@pytest.fixture
def orchestrator():
    return AnalysisOrchestrator()

@pytest.mark.asyncio
async def test_run_analysis_success(orchestrator):
    """测试成功的分析流程"""
    task_id = "test-task-id"
    youtube_url = "https://youtube.com/watch?v=test"
    options = {}
    
    with patch.object(orchestrator, '_run_extraction_step') as mock_extraction:
        with patch.object(orchestrator, '_run_transcription_step') as mock_transcription:
            with patch.object(orchestrator, '_run_parallel_analysis_steps') as mock_parallel:
                with patch.object(orchestrator, '_run_finalization_step') as mock_finalization:
                    
                    # 模拟成功的步骤结果
                    mock_extraction.return_value = StepResult(
                        step=AnalysisStep.EXTRACTION,
                        success=True,
                        data={'video_info': {}, 'audio_file_path': '/test.wav'}
                    )
                    
                    mock_transcription.return_value = StepResult(
                        step=AnalysisStep.TRANSCRIPTION,
                        success=True,
                        data={'full_text': 'test transcript'}
                    )
                    
                    mock_parallel.return_value = (
                        StepResult(step=AnalysisStep.CONTENT_ANALYSIS, success=True, data={}),
                        StepResult(step=AnalysisStep.COMMENT_ANALYSIS, success=True, data={})
                    )
                    
                    mock_finalization.return_value = StepResult(
                        step=AnalysisStep.FINALIZATION,
                        success=True,
                        data={'summary': {}}
                    )
                    
                    # 执行分析
                    await orchestrator.run_analysis(task_id, youtube_url, options)
                    
                    # 验证所有步骤都被调用
                    mock_extraction.assert_called_once()
                    mock_transcription.assert_called_once()
                    mock_parallel.assert_called_once()
                    mock_finalization.assert_called_once()

@pytest.mark.asyncio
async def test_run_analysis_failure(orchestrator):
    """测试分析流程失败情况"""
    task_id = "test-task-id"
    youtube_url = "https://youtube.com/watch?v=test"
    options = {}
    
    with patch.object(orchestrator, '_run_extraction_step') as mock_extraction:
        # 模拟提取步骤失败
        mock_extraction.return_value = StepResult(
            step=AnalysisStep.EXTRACTION,
            success=False,
            error="提取失败"
        )
        
        with pytest.raises(Exception):
            await orchestrator.run_analysis(task_id, youtube_url, options)
```

## 交付物清单

- [ ] 分析编排器核心类 (app/services/analysis_orchestrator.py)
- [ ] 步骤结果数据模型 (StepResult, AnalysisProgress)
- [ ] 任务调度和协调逻辑
- [ ] 进度跟踪和状态管理
- [ ] 错误处理和恢复机制
- [ ] 结果聚合和报告生成
- [ ] 实时通信集成
- [ ] 单元测试和集成测试
- [ ] 性能监控和日志记录

## 关键接口

完成此任务后，需要为后续任务提供：
- 完整的分析结果数据
- 实时进度更新能力
- 错误处理和恢复机制
- 任务状态管理接口

## 预估时间

- 开发时间: 3-4天
- 测试时间: 1.5天
- 集成调试: 1天
- 文档时间: 0.5天
- 总计: 6-7天

## 注意事项

1. 确保任务调度的可靠性和容错性
2. 实现合理的超时和重试机制
3. 优化并行处理的性能
4. 处理各种异常和边界情况
5. 提供详细的进度反馈和错误信息

这是整个系统的核心协调器，请确保其稳定性和可靠性。
