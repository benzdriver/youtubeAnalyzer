# Task 2: 后端API框架

## 任务概述

构建YouTube分析工具的后端API框架，包括FastAPI应用结构、任务队列系统、WebSocket实时通信、API端点定义和数据库模型设计。

## 目标

- 建立FastAPI应用的完整架构
- 实现Celery + Redis任务队列系统
- 配置WebSocket实时通信
- 定义核心API端点
- 设计数据库模型和迁移

## 可交付成果

### 1. FastAPI应用结构

#### 主应用文件
```python
# backend/app/main.py
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
import time
import logging

from app.core.config import settings
from app.core.database import engine, create_tables
from app.api.v1 import analyze, tasks, websocket
from app.utils.exceptions import YouTubeAnalyzerError

# 创建FastAPI应用
app = FastAPI(
    title=settings.app_name,
    description="YouTube视频内容分析API",
    version=settings.version,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None
)

# 中间件配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)

# 请求日志中间件
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    
    logging.info("Request processed", extra={
        "method": request.method,
        "url": str(request.url),
        "status_code": response.status_code,
        "process_time": process_time
    })
    
    response.headers["X-Process-Time"] = str(process_time)
    return response

# 全局异常处理
@app.exception_handler(YouTubeAnalyzerError)
async def youtube_analyzer_exception_handler(request: Request, exc: YouTubeAnalyzerError):
    return JSONResponse(
        status_code=400,
        content={
            "error": {
                "code": exc.__class__.__name__,
                "message": str(exc),
                "timestamp": time.time()
            }
        }
    )

# 路由注册
app.include_router(analyze.router, prefix="/api/v1", tags=["analysis"])
app.include_router(tasks.router, prefix="/api/v1", tags=["tasks"])
app.include_router(websocket.router, prefix="/ws", tags=["websocket"])

# 健康检查端点
@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": time.time()}

# 应用启动事件
@app.on_event("startup")
async def startup_event():
    await create_tables()
    logging.info("Application started")

# 应用关闭事件
@app.on_event("shutdown")
async def shutdown_event():
    logging.info("Application shutting down")
```

### 2. 数据库模型设计

#### 核心模型
```python
# backend/app/models/task.py
from sqlalchemy import Column, String, Integer, DateTime, Text, JSON, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
import enum
from datetime import datetime
from typing import Optional

Base = declarative_base()

class TaskStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class AnalysisType(str, enum.Enum):
    CONTENT = "content"
    COMMENTS = "comments"
    COMPREHENSIVE = "comprehensive"
    CUSTOM = "custom"

class AnalysisTask(Base):
    __tablename__ = "analysis_tasks"
    
    id = Column(String, primary_key=True)
    type = Column(Enum(AnalysisType), nullable=False)
    status = Column(Enum(TaskStatus), default=TaskStatus.PENDING, index=True)
    progress = Column(Integer, default=0)
    created_at = Column(DateTime, default=func.now(), index=True)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # 输入数据
    youtube_url = Column(String, nullable=False)
    input_options = Column(JSON)
    
    # 处理信息
    current_step = Column(String)
    estimated_time_remaining = Column(Integer)
    error_message = Column(Text)
    
    # 结果数据
    result_data = Column(JSON)
    
    # 元数据
    processing_time = Column(Integer)  # 秒
    cost_breakdown = Column(JSON)
    
    def __repr__(self):
        return f"<AnalysisTask(id={self.id}, type={self.type}, status={self.status})>"

class VideoInfo(Base):
    __tablename__ = "video_info"
    
    id = Column(String, primary_key=True)  # YouTube video ID
    task_id = Column(String, nullable=False, index=True)
    
    title = Column(String, nullable=False)
    description = Column(Text)
    duration = Column(Integer)  # 秒
    view_count = Column(Integer)
    like_count = Column(Integer)
    comment_count = Column(Integer)
    
    channel_id = Column(String)
    channel_name = Column(String)
    channel_subscriber_count = Column(Integer)
    
    published_at = Column(DateTime)
    tags = Column(JSON)  # List[str]
    category = Column(String)
    language = Column(String)
    thumbnail_url = Column(String)
    
    created_at = Column(DateTime, default=func.now())

class TranscriptData(Base):
    __tablename__ = "transcript_data"
    
    id = Column(String, primary_key=True)
    task_id = Column(String, nullable=False, index=True)
    
    full_text = Column(Text, nullable=False)
    segments = Column(JSON)  # List[TranscriptSegment]
    language = Column(String)
    confidence = Column(Integer)  # 0-100
    
    created_at = Column(DateTime, default=func.now())
```

### 3. API路由实现

#### 分析任务API
```python
# backend/app/api/v1/analyze.py
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel, Field, validator
from typing import Optional, List
import uuid
import re

from app.models.schemas import AnalysisInput, TaskResponse
from app.services.orchestrator import AnalysisOrchestrator
from app.core.database import get_db_session

router = APIRouter()

class AnalysisRequest(BaseModel):
    youtubeUrl: str = Field(..., description="YouTube视频链接")
    type: str = Field("comprehensive", description="分析类型")
    options: dict = Field(default_factory=dict, description="分析选项")
    
    @validator('youtubeUrl')
    def validate_youtube_url(cls, v):
        youtube_pattern = r'^https?://(www\.)?(youtube\.com/watch\?v=|youtu\.be/)[\w-]+$'
        if not re.match(youtube_pattern, v):
            raise ValueError('Invalid YouTube URL format')
        return v

@router.post("/analyze", response_model=TaskResponse)
async def create_analysis(
    request: AnalysisRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db_session)
):
    """创建新的视频分析任务"""
    
    # 生成任务ID
    task_id = str(uuid.uuid4())
    
    # 创建任务记录
    task = AnalysisTask(
        id=task_id,
        type=request.type,
        youtube_url=request.youtubeUrl,
        input_options=request.options
    )
    
    db.add(task)
    await db.commit()
    
    # 启动后台分析任务
    orchestrator = AnalysisOrchestrator()
    background_tasks.add_task(
        orchestrator.run_analysis,
        task_id,
        request.youtubeUrl,
        request.options
    )
    
    # 估算处理时间
    estimated_duration = await orchestrator.estimate_duration(request.options)
    
    return TaskResponse(
        taskId=task_id,
        status="pending",
        estimatedDuration=estimated_duration,
        message="任务已创建，正在队列中等待处理"
    )

@router.get("/analysis-types")
async def get_analysis_types():
    """获取支持的分析类型"""
    return {
        "types": [
            {
                "id": "content",
                "name": "内容分析",
                "description": "分析视频内容、结构和关键信息",
                "estimatedTime": 180,
                "features": ["transcript", "key_points", "topics", "sentiment"]
            },
            {
                "id": "comments",
                "name": "评论分析", 
                "description": "分析用户评论和作者回复",
                "estimatedTime": 120,
                "features": ["sentiment_analysis", "author_replies", "themes"]
            },
            {
                "id": "comprehensive",
                "name": "综合分析",
                "description": "包含内容和评论的完整分析",
                "estimatedTime": 300,
                "features": ["all"]
            }
        ]
    }
```

#### 任务管理API
```python
# backend/app/api/v1/tasks.py
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from typing import Optional, List

from app.models.task import AnalysisTask, TaskStatus
from app.models.schemas import TaskDetail, TaskList
from app.core.database import get_db_session

router = APIRouter()

@router.get("/tasks/{task_id}", response_model=TaskDetail)
async def get_task(
    task_id: str,
    db: AsyncSession = Depends(get_db_session)
):
    """获取任务详情"""
    
    result = await db.execute(
        select(AnalysisTask).where(AnalysisTask.id == task_id)
    )
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return TaskDetail.from_orm(task)

@router.get("/tasks/{task_id}/result")
async def get_task_result(
    task_id: str,
    db: AsyncSession = Depends(get_db_session)
):
    """获取任务结果"""
    
    result = await db.execute(
        select(AnalysisTask).where(AnalysisTask.id == task_id)
    )
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if task.status != TaskStatus.COMPLETED:
        raise HTTPException(
            status_code=202,
            detail={
                "message": "任务仍在处理中",
                "status": task.status,
                "progress": task.progress
            }
        )
    
    return {
        "taskId": task_id,
        "result": task.result_data
    }

@router.get("/tasks", response_model=TaskList)
async def list_tasks(
    status: Optional[TaskStatus] = Query(None),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db_session)
):
    """获取任务列表"""
    
    query = select(AnalysisTask)
    
    if status:
        query = query.where(AnalysisTask.status == status)
    
    query = query.order_by(AnalysisTask.created_at.desc())
    query = query.offset(offset).limit(limit)
    
    result = await db.execute(query)
    tasks = result.scalars().all()
    
    # 获取总数
    count_query = select(func.count(AnalysisTask.id))
    if status:
        count_query = count_query.where(AnalysisTask.status == status)
    
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    return TaskList(
        tasks=[TaskDetail.from_orm(task) for task in tasks],
        total=total,
        limit=limit,
        offset=offset
    )

@router.delete("/tasks/{task_id}")
async def cancel_task(
    task_id: str,
    db: AsyncSession = Depends(get_db_session)
):
    """取消任务"""
    
    result = await db.execute(
        select(AnalysisTask).where(AnalysisTask.id == task_id)
    )
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
        raise HTTPException(
            status_code=409,
            detail="Cannot cancel completed or failed task"
        )
    
    await db.execute(
        update(AnalysisTask)
        .where(AnalysisTask.id == task_id)
        .values(status=TaskStatus.CANCELLED)
    )
    await db.commit()
    
    return {"message": "Task cancelled", "taskId": task_id}
```

### 4. WebSocket实时通信

```python
# backend/app/api/v1/websocket.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, Set
import json
import logging

router = APIRouter()

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, task_id: str):
        await websocket.accept()
        if task_id not in self.active_connections:
            self.active_connections[task_id] = set()
        self.active_connections[task_id].add(websocket)
        logging.info(f"WebSocket connected for task {task_id}")
    
    def disconnect(self, websocket: WebSocket, task_id: str):
        if task_id in self.active_connections:
            self.active_connections[task_id].discard(websocket)
            if not self.active_connections[task_id]:
                del self.active_connections[task_id]
        logging.info(f"WebSocket disconnected for task {task_id}")
    
    async def send_message(self, task_id: str, message: dict):
        if task_id in self.active_connections:
            disconnected = set()
            for connection in self.active_connections[task_id]:
                try:
                    await connection.send_text(json.dumps(message))
                except:
                    disconnected.add(connection)
            
            # 清理断开的连接
            for connection in disconnected:
                self.active_connections[task_id].discard(connection)

manager = ConnectionManager()

@router.websocket("/tasks/{task_id}")
async def websocket_endpoint(websocket: WebSocket, task_id: str):
    await manager.connect(websocket, task_id)
    try:
        while True:
            # 保持连接活跃
            data = await websocket.receive_text()
            # 可以处理客户端发送的消息（如认证）
    except WebSocketDisconnect:
        manager.disconnect(websocket, task_id)

# 进度更新函数（供其他模块调用）
async def send_progress_update(task_id: str, progress: int, step: str, message: str = ""):
    await manager.send_message(task_id, {
        "type": "progress_update",
        "taskId": task_id,
        "progress": progress,
        "currentStep": step,
        "message": message,
        "timestamp": time.time()
    })

async def send_task_completed(task_id: str, result: dict):
    await manager.send_message(task_id, {
        "type": "task_completed",
        "taskId": task_id,
        "result": result,
        "timestamp": time.time()
    })

async def send_task_failed(task_id: str, error: dict):
    await manager.send_message(task_id, {
        "type": "task_failed",
        "taskId": task_id,
        "error": error,
        "timestamp": time.time()
    })
```

### 5. Celery任务队列配置

```python
# backend/app/core/celery_app.py
from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "youtube_analyzer",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["app.tasks.analysis"]
)

# Celery配置
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1小时超时
    task_soft_time_limit=3300,  # 55分钟软超时
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# 任务路由
celery_app.conf.task_routes = {
    "app.tasks.analysis.*": {"queue": "analysis"},
    "app.tasks.transcription.*": {"queue": "transcription"},
    "app.tasks.extraction.*": {"queue": "extraction"},
}
```

### 6. 数据库连接和会话管理

```python
# backend/app/core/database.py
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models.task import Base

# 创建异步引擎
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    future=True
)

# 创建会话工厂
AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

async def get_db_session() -> AsyncSession:
    """获取数据库会话"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

async def create_tables():
    """创建数据库表"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
```

## 依赖关系

### 前置条件
- Task 1: 项目配置管理（必须完成）

### 阻塞任务
- Task 4: YouTube数据提取
- Task 5: 音频转录服务
- Task 6: 内容分析模块
- Task 7: 评论分析模块
- Task 8: 分析编排器

## 验收标准

### 功能验收
- [ ] FastAPI应用能够正常启动
- [ ] 所有API端点响应正确
- [ ] WebSocket连接和消息推送正常
- [ ] 数据库模型和迁移正常工作
- [ ] Celery任务队列正常运行
- [ ] 健康检查端点返回正确状态

### 技术验收
- [ ] API响应时间 < 200ms（非分析任务）
- [ ] WebSocket连接延迟 < 100ms
- [ ] 数据库查询优化（使用索引）
- [ ] 错误处理完整且用户友好
- [ ] 日志记录详细且结构化

### 质量验收
- [ ] 代码覆盖率 ≥ 80%
- [ ] API文档完整且准确
- [ ] 所有端点有适当的验证
- [ ] 安全性检查通过
- [ ] 性能测试通过

## 测试要求

### 单元测试
```python
# tests/test_api.py
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_create_analysis():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post("/api/v1/analyze", json={
            "youtubeUrl": "https://www.youtube.com/watch?v=test",
            "type": "content",
            "options": {"includeComments": False}
        })
        assert response.status_code == 201
        data = response.json()
        assert "taskId" in data

@pytest.mark.asyncio
async def test_get_task():
    # 先创建任务
    async with AsyncClient(app=app, base_url="http://test") as ac:
        create_response = await ac.post("/api/v1/analyze", json={
            "youtubeUrl": "https://www.youtube.com/watch?v=test",
            "type": "content"
        })
        task_id = create_response.json()["taskId"]
        
        # 获取任务详情
        response = await ac.get(f"/api/v1/tasks/{task_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == task_id
```

### 集成测试
```python
# tests/test_websocket.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

def test_websocket_connection():
    client = TestClient(app)
    with client.websocket_connect("/ws/tasks/test-task-id") as websocket:
        # 测试连接建立
        assert websocket is not None
        
        # 可以发送测试消息
        websocket.send_text("test")
```

## 预估工作量

- **开发时间**: 3-4天
- **测试时间**: 1天
- **文档时间**: 0.5天
- **总计**: 4.5-5.5天

## 关键路径

此任务在关键路径上，完成后将为所有分析服务提供API基础设施。

## 交付检查清单

- [ ] FastAPI应用结构完整
- [ ] 所有API端点已实现
- [ ] WebSocket通信已配置
- [ ] 数据库模型已定义
- [ ] Celery任务队列已配置
- [ ] 单元测试和集成测试通过
- [ ] API文档已生成
- [ ] 代码已提交并通过CI检查

## 后续任务接口

完成此任务后，为后续任务提供：
- 标准化的API接口
- 数据库模型和会话管理
- 任务队列基础设施
- WebSocket通信机制
- 错误处理和日志系统

这些将被Task 4-8的所有分析服务直接使用。
