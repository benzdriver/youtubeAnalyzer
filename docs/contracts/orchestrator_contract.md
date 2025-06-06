# 分析编排器接口契约

**提供方**: TASK_08 (分析编排器)  
**使用方**: TASK_09 (结果展示界面)  
**版本**: v1.0.0

## 概述

定义分析编排器的接口规范，包括任务编排逻辑、进度跟踪、错误处理和性能监控。

## 核心接口定义

### 编排器主接口

```python
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, AsyncGenerator
from enum import Enum

class AnalysisOrchestrator(ABC):
    """分析编排器抽象基类"""
    
    @abstractmethod
    async def start_analysis(
        self, 
        task_id: str, 
        youtube_url: str, 
        options: AnalysisOptions
    ) -> AnalysisTask:
        """启动分析任务"""
        pass
    
    @abstractmethod
    async def get_task_status(self, task_id: str) -> TaskStatus:
        """获取任务状态"""
        pass
    
    @abstractmethod
    async def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        pass
    
    @abstractmethod
    async def get_progress_stream(
        self, 
        task_id: str
    ) -> AsyncGenerator[ProgressUpdate, None]:
        """获取进度更新流"""
        pass
    
    @abstractmethod
    async def get_result(self, task_id: str) -> Optional[AnalysisResult]:
        """获取分析结果"""
        pass
```

### 任务编排流程

```python
class AnalysisStep(Enum):
    """分析步骤枚举"""
    INITIALIZATION = "initialization"
    VIDEO_EXTRACTION = "video_extraction"
    AUDIO_TRANSCRIPTION = "audio_transcription"
    CONTENT_ANALYSIS = "content_analysis"
    COMMENT_ANALYSIS = "comment_analysis"
    RESULT_SYNTHESIS = "result_synthesis"
    FINALIZATION = "finalization"

class StepStatus(Enum):
    """步骤状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"

class AnalysisWorkflow:
    """分析工作流定义"""
    
    def __init__(self):
        self.steps = [
            AnalysisStep.INITIALIZATION,
            AnalysisStep.VIDEO_EXTRACTION,
            AnalysisStep.AUDIO_TRANSCRIPTION,
            AnalysisStep.CONTENT_ANALYSIS,
            AnalysisStep.COMMENT_ANALYSIS,
            AnalysisStep.RESULT_SYNTHESIS,
            AnalysisStep.FINALIZATION
        ]
        
        self.step_dependencies = {
            AnalysisStep.AUDIO_TRANSCRIPTION: [AnalysisStep.VIDEO_EXTRACTION],
            AnalysisStep.CONTENT_ANALYSIS: [AnalysisStep.AUDIO_TRANSCRIPTION],
            AnalysisStep.COMMENT_ANALYSIS: [AnalysisStep.VIDEO_EXTRACTION],
            AnalysisStep.RESULT_SYNTHESIS: [
                AnalysisStep.CONTENT_ANALYSIS,
                AnalysisStep.COMMENT_ANALYSIS
            ],
            AnalysisStep.FINALIZATION: [AnalysisStep.RESULT_SYNTHESIS]
        }
    
    def get_next_steps(self, completed_steps: List[AnalysisStep]) -> List[AnalysisStep]:
        """获取下一步可执行的步骤"""
        next_steps = []
        for step in self.steps:
            if step in completed_steps:
                continue
            
            dependencies = self.step_dependencies.get(step, [])
            if all(dep in completed_steps for dep in dependencies):
                next_steps.append(step)
        
        return next_steps
```

### 进度跟踪接口

```python
@dataclass
class ProgressUpdate:
    """进度更新数据"""
    task_id: str
    current_step: AnalysisStep
    step_progress: float  # 当前步骤进度 0-100
    overall_progress: float  # 整体进度 0-100
    message: str
    timestamp: datetime
    estimated_remaining: Optional[int] = None  # 预计剩余秒数
    
class ProgressTracker:
    """进度跟踪器"""
    
    def __init__(self, task_id: str):
        self.task_id = task_id
        self.step_weights = {
            AnalysisStep.INITIALIZATION: 5,
            AnalysisStep.VIDEO_EXTRACTION: 15,
            AnalysisStep.AUDIO_TRANSCRIPTION: 25,
            AnalysisStep.CONTENT_ANALYSIS: 20,
            AnalysisStep.COMMENT_ANALYSIS: 20,
            AnalysisStep.RESULT_SYNTHESIS: 10,
            AnalysisStep.FINALIZATION: 5
        }
        self.step_progress = {step: 0.0 for step in AnalysisStep}
        self.current_step = AnalysisStep.INITIALIZATION
    
    def update_step_progress(
        self, 
        step: AnalysisStep, 
        progress: float, 
        message: str = ""
    ) -> ProgressUpdate:
        """更新步骤进度"""
        self.step_progress[step] = min(100.0, max(0.0, progress))
        self.current_step = step
        
        overall_progress = self._calculate_overall_progress()
        
        return ProgressUpdate(
            task_id=self.task_id,
            current_step=step,
            step_progress=progress,
            overall_progress=overall_progress,
            message=message,
            timestamp=datetime.utcnow()
        )
    
    def _calculate_overall_progress(self) -> float:
        """计算整体进度"""
        total_weight = sum(self.step_weights.values())
        weighted_progress = sum(
            self.step_progress[step] * weight / 100
            for step, weight in self.step_weights.items()
        )
        return (weighted_progress / total_weight) * 100
```

### 错误处理接口

```python
class AnalysisError(Exception):
    """分析错误基类"""
    
    def __init__(
        self, 
        message: str, 
        error_code: str, 
        step: Optional[AnalysisStep] = None,
        recoverable: bool = False,
        retry_after: Optional[int] = None
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.step = step
        self.recoverable = recoverable
        self.retry_after = retry_after
        self.timestamp = datetime.utcnow()

class ErrorHandler:
    """错误处理器"""
    
    def __init__(self):
        self.retry_strategies = {
            "NETWORK_ERROR": {"max_retries": 3, "backoff": 2},
            "API_RATE_LIMIT": {"max_retries": 5, "backoff": 60},
            "TEMPORARY_FAILURE": {"max_retries": 2, "backoff": 5}
        }
    
    async def handle_error(
        self, 
        error: AnalysisError, 
        task_id: str
    ) -> bool:
        """处理错误，返回是否应该重试"""
        strategy = self.retry_strategies.get(error.error_code)
        
        if not strategy or not error.recoverable:
            await self._log_fatal_error(error, task_id)
            return False
        
        retry_count = await self._get_retry_count(task_id, error.error_code)
        
        if retry_count >= strategy["max_retries"]:
            await self._log_max_retries_exceeded(error, task_id)
            return False
        
        await self._schedule_retry(task_id, error, strategy["backoff"])
        return True
    
    async def _log_fatal_error(self, error: AnalysisError, task_id: str):
        """记录致命错误"""
        pass
    
    async def _get_retry_count(self, task_id: str, error_code: str) -> int:
        """获取重试次数"""
        pass
    
    async def _schedule_retry(
        self, 
        task_id: str, 
        error: AnalysisError, 
        delay: int
    ):
        """安排重试"""
        pass
```

### 性能监控接口

```python
@dataclass
class PerformanceMetrics:
    """性能指标"""
    task_id: str
    step: AnalysisStep
    start_time: datetime
    end_time: Optional[datetime] = None
    duration: Optional[float] = None  # 秒
    memory_usage: Optional[float] = None  # MB
    cpu_usage: Optional[float] = None  # 百分比
    api_calls: int = 0
    api_cost: Optional[float] = None  # 美元

class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self):
        self.metrics: Dict[str, List[PerformanceMetrics]] = {}
    
    def start_step_monitoring(
        self, 
        task_id: str, 
        step: AnalysisStep
    ) -> PerformanceMetrics:
        """开始步骤监控"""
        metric = PerformanceMetrics(
            task_id=task_id,
            step=step,
            start_time=datetime.utcnow()
        )
        
        if task_id not in self.metrics:
            self.metrics[task_id] = []
        
        self.metrics[task_id].append(metric)
        return metric
    
    def end_step_monitoring(
        self, 
        task_id: str, 
        step: AnalysisStep,
        **kwargs
    ):
        """结束步骤监控"""
        for metric in reversed(self.metrics.get(task_id, [])):
            if metric.step == step and metric.end_time is None:
                metric.end_time = datetime.utcnow()
                metric.duration = (
                    metric.end_time - metric.start_time
                ).total_seconds()
                
                for key, value in kwargs.items():
                    if hasattr(metric, key):
                        setattr(metric, key, value)
                break
    
    def get_task_metrics(self, task_id: str) -> List[PerformanceMetrics]:
        """获取任务性能指标"""
        return self.metrics.get(task_id, [])
```

## 实现示例

### 主编排器实现

```python
class YouTubeAnalysisOrchestrator(AnalysisOrchestrator):
    """YouTube分析编排器实现"""
    
    def __init__(
        self,
        youtube_extractor: YouTubeExtractor,
        transcription_service: TranscriptionService,
        content_analyzer: ContentAnalyzer,
        comment_analyzer: CommentAnalyzer,
        task_repository: TaskRepository,
        websocket_manager: WebSocketManager
    ):
        self.youtube_extractor = youtube_extractor
        self.transcription_service = transcription_service
        self.content_analyzer = content_analyzer
        self.comment_analyzer = comment_analyzer
        self.task_repository = task_repository
        self.websocket_manager = websocket_manager
        
        self.workflow = AnalysisWorkflow()
        self.error_handler = ErrorHandler()
        self.performance_monitor = PerformanceMonitor()
        
        self.active_tasks: Dict[str, AnalysisTask] = {}
    
    async def start_analysis(
        self, 
        task_id: str, 
        youtube_url: str, 
        options: AnalysisOptions
    ) -> AnalysisTask:
        """启动分析任务"""
        
        # 创建任务
        task = AnalysisTask(
            id=task_id,
            youtube_url=youtube_url,
            options=options,
            status=TaskStatus.PENDING,
            created_at=datetime.utcnow()
        )
        
        # 保存任务
        await self.task_repository.create_task(task)
        self.active_tasks[task_id] = task
        
        # 启动异步处理
        asyncio.create_task(self._process_analysis(task))
        
        return task
    
    async def _process_analysis(self, task: AnalysisTask):
        """处理分析任务"""
        task_id = task.id
        progress_tracker = ProgressTracker(task_id)
        
        try:
            # 更新任务状态
            task.status = TaskStatus.PROCESSING
            await self.task_repository.update_task(task)
            
            # 执行分析流程
            completed_steps = []
            
            for step in self.workflow.steps:
                # 检查依赖
                dependencies = self.workflow.step_dependencies.get(step, [])
                if not all(dep in completed_steps for dep in dependencies):
                    continue
                
                # 开始步骤监控
                metric = self.performance_monitor.start_step_monitoring(
                    task_id, step
                )
                
                try:
                    # 执行步骤
                    await self._execute_step(task, step, progress_tracker)
                    completed_steps.append(step)
                    
                    # 结束步骤监控
                    self.performance_monitor.end_step_monitoring(task_id, step)
                    
                except AnalysisError as e:
                    # 处理错误
                    should_retry = await self.error_handler.handle_error(e, task_id)
                    
                    if not should_retry:
                        task.status = TaskStatus.FAILED
                        task.error = str(e)
                        await self.task_repository.update_task(task)
                        return
            
            # 完成任务
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.utcnow()
            await self.task_repository.update_task(task)
            
            # 发送完成通知
            await self._send_completion_notification(task)
            
        except Exception as e:
            # 处理未预期的错误
            task.status = TaskStatus.FAILED
            task.error = str(e)
            await self.task_repository.update_task(task)
            
        finally:
            # 清理资源
            if task_id in self.active_tasks:
                del self.active_tasks[task_id]
    
    async def _execute_step(
        self, 
        task: AnalysisTask, 
        step: AnalysisStep, 
        progress_tracker: ProgressTracker
    ):
        """执行分析步骤"""
        
        if step == AnalysisStep.INITIALIZATION:
            await self._step_initialization(task, progress_tracker)
        elif step == AnalysisStep.VIDEO_EXTRACTION:
            await self._step_video_extraction(task, progress_tracker)
        elif step == AnalysisStep.AUDIO_TRANSCRIPTION:
            await self._step_audio_transcription(task, progress_tracker)
        elif step == AnalysisStep.CONTENT_ANALYSIS:
            await self._step_content_analysis(task, progress_tracker)
        elif step == AnalysisStep.COMMENT_ANALYSIS:
            await self._step_comment_analysis(task, progress_tracker)
        elif step == AnalysisStep.RESULT_SYNTHESIS:
            await self._step_result_synthesis(task, progress_tracker)
        elif step == AnalysisStep.FINALIZATION:
            await self._step_finalization(task, progress_tracker)
    
    async def _step_video_extraction(
        self, 
        task: AnalysisTask, 
        progress_tracker: ProgressTracker
    ):
        """视频提取步骤"""
        
        # 更新进度
        update = progress_tracker.update_step_progress(
            AnalysisStep.VIDEO_EXTRACTION, 
            0, 
            "开始提取视频信息..."
        )
        await self._send_progress_update(update)
        
        # 提取视频信息
        video_info = await self.youtube_extractor.extract_video_info(
            task.youtube_url
        )
        
        # 更新进度
        update = progress_tracker.update_step_progress(
            AnalysisStep.VIDEO_EXTRACTION, 
            50, 
            "正在下载音频文件..."
        )
        await self._send_progress_update(update)
        
        # 下载音频
        audio_file = await self.youtube_extractor.download_audio(
            task.youtube_url
        )
        
        # 提取评论
        if task.options.include_comments:
            update = progress_tracker.update_step_progress(
                AnalysisStep.VIDEO_EXTRACTION, 
                75, 
                "正在提取评论数据..."
            )
            await self._send_progress_update(update)
            
            comments = await self.youtube_extractor.extract_comments(
                video_info.id,
                max_comments=task.options.max_comments
            )
        else:
            comments = []
        
        # 保存提取结果
        task.video_info = video_info
        task.audio_file = audio_file
        task.comments = comments
        
        # 完成步骤
        update = progress_tracker.update_step_progress(
            AnalysisStep.VIDEO_EXTRACTION, 
            100, 
            "视频信息提取完成"
        )
        await self._send_progress_update(update)
    
    async def _send_progress_update(self, update: ProgressUpdate):
        """发送进度更新"""
        await self.websocket_manager.send_to_task(
            update.task_id,
            {
                "type": "progress_update",
                "data": {
                    "current_step": update.current_step.value,
                    "step_progress": update.step_progress,
                    "overall_progress": update.overall_progress,
                    "message": update.message,
                    "timestamp": update.timestamp.isoformat()
                }
            }
        )
    
    async def _send_completion_notification(self, task: AnalysisTask):
        """发送完成通知"""
        await self.websocket_manager.send_to_task(
            task.id,
            {
                "type": "task_completed",
                "data": {
                    "task_id": task.id,
                    "result": task.result.dict() if task.result else None
                }
            }
        )
```

## WebSocket事件规范

### 进度更新事件

```typescript
interface ProgressUpdateEvent {
  type: 'progress_update';
  task_id: string;
  data: {
    current_step: string;
    step_progress: number;
    overall_progress: number;
    message: string;
    timestamp: string;
    estimated_remaining?: number;
  };
}
```

### 任务完成事件

```typescript
interface TaskCompletedEvent {
  type: 'task_completed';
  task_id: string;
  data: {
    task_id: string;
    result: AnalysisResult;
    performance_metrics: PerformanceMetrics[];
  };
}
```

### 错误事件

```typescript
interface TaskErrorEvent {
  type: 'task_error';
  task_id: string;
  data: {
    error_code: string;
    message: string;
    step: string;
    recoverable: boolean;
    retry_after?: number;
  };
}
```

## 测试接口

### 单元测试

```python
import pytest
from unittest.mock import AsyncMock, Mock

@pytest.fixture
async def orchestrator():
    """创建测试用编排器"""
    youtube_extractor = AsyncMock()
    transcription_service = AsyncMock()
    content_analyzer = AsyncMock()
    comment_analyzer = AsyncMock()
    task_repository = AsyncMock()
    websocket_manager = AsyncMock()
    
    return YouTubeAnalysisOrchestrator(
        youtube_extractor=youtube_extractor,
        transcription_service=transcription_service,
        content_analyzer=content_analyzer,
        comment_analyzer=comment_analyzer,
        task_repository=task_repository,
        websocket_manager=websocket_manager
    )

@pytest.mark.asyncio
async def test_start_analysis(orchestrator):
    """测试启动分析"""
    task = await orchestrator.start_analysis(
        task_id="test-task",
        youtube_url="https://youtube.com/watch?v=test",
        options=AnalysisOptions(
            include_comments=True,
            analysis_depth="detailed"
        )
    )
    
    assert task.id == "test-task"
    assert task.status == TaskStatus.PENDING
    orchestrator.task_repository.create_task.assert_called_once()

@pytest.mark.asyncio
async def test_error_handling(orchestrator):
    """测试错误处理"""
    # 模拟网络错误
    orchestrator.youtube_extractor.extract_video_info.side_effect = \
        AnalysisError("Network error", "NETWORK_ERROR", recoverable=True)
    
    task = await orchestrator.start_analysis(
        task_id="test-task",
        youtube_url="https://youtube.com/watch?v=test",
        options=AnalysisOptions()
    )
    
    # 等待处理完成
    await asyncio.sleep(0.1)
    
    # 验证重试逻辑
    assert orchestrator.youtube_extractor.extract_video_info.call_count > 1
```

### 集成测试

```python
@pytest.mark.integration
async def test_full_analysis_workflow():
    """测试完整分析流程"""
    # 设置真实的服务实例
    orchestrator = create_real_orchestrator()
    
    # 启动分析
    task = await orchestrator.start_analysis(
        task_id="integration-test",
        youtube_url="https://youtube.com/watch?v=dQw4w9WgXcQ",
        options=AnalysisOptions(
            include_comments=True,
            analysis_depth="basic"
        )
    )
    
    # 等待完成
    while task.status not in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
        await asyncio.sleep(1)
        task = await orchestrator.get_task_status(task.id)
    
    # 验证结果
    assert task.status == TaskStatus.COMPLETED
    assert task.result is not None
    assert task.result.video_info is not None
    assert task.result.content_insights is not None
```

## 性能要求

- **任务启动时间**: < 1秒
- **进度更新频率**: 每5秒至少一次
- **内存使用**: 单任务 < 1GB
- **并发任务数**: 支持至少10个并发任务
- **错误恢复时间**: < 30秒

## 扩展性设计

### 插件系统

```python
class AnalysisPlugin(ABC):
    """分析插件基类"""
    
    @abstractmethod
    def get_name(self) -> str:
        """获取插件名称"""
        pass
    
    @abstractmethod
    async def execute(
        self, 
        context: AnalysisContext
    ) -> AnalysisStepResult:
        """执行插件逻辑"""
        pass

class PluginManager:
    """插件管理器"""
    
    def __init__(self):
        self.plugins: Dict[str, AnalysisPlugin] = {}
    
    def register_plugin(self, plugin: AnalysisPlugin):
        """注册插件"""
        self.plugins[plugin.get_name()] = plugin
    
    async def execute_plugin(
        self, 
        name: str, 
        context: AnalysisContext
    ) -> AnalysisStepResult:
        """执行插件"""
        if name not in self.plugins:
            raise ValueError(f"Plugin {name} not found")
        
        return await self.plugins[name].execute(context)
```
