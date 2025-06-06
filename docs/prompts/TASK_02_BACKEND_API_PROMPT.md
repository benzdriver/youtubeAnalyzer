# Task 2: 后端API框架 - Sub-Session Prompt

## 必读文档

**重要提示**: 开始此任务前，你必须阅读并理解以下文档：

### 核心协调文档
- `docs/TASK_COORDINATION.md` - 整体任务依赖关系和项目结构
- `docs/ARCHITECTURE_OVERVIEW.md` - 系统架构和技术栈
- `docs/CODING_STANDARDS.md` - 代码格式、命名规范和最佳实践
- `docs/API_SPECIFICATIONS.md` - 完整API接口定义

### 任务专用文档
- `docs/tasks/TASK_02_BACKEND_API.md` - 详细任务要求和验收标准
- `docs/contracts/api_framework_contract.md` - API框架接口规范

### 参考文档
- `docs/DEVELOPMENT_SETUP.md` - 开发环境配置
- `docs/PROGRESS_TRACKER.md` - 进度跟踪和任务状态更新

### 依赖关系
- Task 1 (项目配置) 必须先完成
- 查看 `docs/contracts/project_config_contract.md` 了解配置接口

## 项目背景

你正在为YouTube视频分析工具构建FastAPI后端框架。这个后端需要支持：
- RESTful API接口
- WebSocket实时通信
- Celery异步任务处理
- 数据库操作
- 用户认证和授权

## 任务目标

建立完整的FastAPI应用框架，包括API路由、数据库模型、WebSocket通信、Celery集成和中间件配置。

## 具体要求

### 1. FastAPI应用主体
参考 <ref_file file="/home/ubuntu/repos/generic-ai-agent/src/agent_core/response_router.py" /> 的路由设计模式：

```python
# backend/app/main.py
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.database import init_db
from app.api.v1 import api_router
from app.api.v1.websocket import websocket_manager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时初始化
    await init_db()
    yield
    # 关闭时清理

app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="YouTube视频分析API",
    lifespan=lifespan
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

# 路由注册
app.include_router(api_router, prefix="/api/v1")

@app.websocket("/ws/{task_id}")
async def websocket_endpoint(websocket: WebSocket, task_id: str):
    await websocket_manager.connect(websocket, task_id)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        websocket_manager.disconnect(task_id)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}
```

### 2. 数据库模型设计
基于 <ref_file file="/home/ubuntu/repos/youtubeAnalyzer/docs/API_SPECIFICATIONS.md" /> 的数据模型：

```python
# backend/app/models/task.py
from sqlalchemy import Column, String, DateTime, Integer, Text, JSON, Enum
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import enum
import uuid

Base = declarative_base()

class TaskStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class AnalysisTask(Base):
    __tablename__ = "analysis_tasks"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    youtube_url = Column(String, nullable=False)
    status = Column(Enum(TaskStatus), default=TaskStatus.PENDING)
    current_step = Column(String)
    progress = Column(Integer, default=0)
    result_data = Column(JSON)
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime)

# backend/app/models/schemas.py
from pydantic import BaseModel, HttpUrl
from typing import Optional, Dict, Any
from datetime import datetime
from .task import TaskStatus

class AnalysisTaskCreate(BaseModel):
    youtube_url: HttpUrl
    options: Optional[Dict[str, Any]] = {}

class AnalysisTaskResponse(BaseModel):
    id: str
    youtube_url: str
    status: TaskStatus
    current_step: Optional[str]
    progress: int
    created_at: datetime
    estimated_completion: Optional[datetime]

class AnalysisResult(BaseModel):
    task_id: str
    result: Dict[str, Any]
    metadata: Dict[str, Any]
```

### 3. API路由实现

```python
# backend/app/api/v1/__init__.py
from fastapi import APIRouter
from .analysis import router as analysis_router

api_router = APIRouter()
api_router.include_router(analysis_router, prefix="/analysis", tags=["analysis"])

# backend/app/api/v1/analysis.py
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.core.database import get_db_session
from app.models.schemas import AnalysisTaskCreate, AnalysisTaskResponse, AnalysisResult
from app.models.task import AnalysisTask, TaskStatus
from app.services.analysis_orchestrator import AnalysisOrchestrator

router = APIRouter()

@router.post("/", response_model=AnalysisTaskResponse)
async def create_analysis_task(
    task_data: AnalysisTaskCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db_session)
):
    """创建新的分析任务"""
    # 创建任务记录
    task = AnalysisTask(
        youtube_url=str(task_data.youtube_url),
        status=TaskStatus.PENDING
    )
    
    db.add(task)
    await db.commit()
    await db.refresh(task)
    
    # 启动后台分析
    orchestrator = AnalysisOrchestrator()
    background_tasks.add_task(
        orchestrator.run_analysis,
        task.id,
        str(task_data.youtube_url),
        task_data.options
    )
    
    return AnalysisTaskResponse(
        id=task.id,
        youtube_url=task.youtube_url,
        status=task.status,
        current_step=task.current_step,
        progress=task.progress,
        created_at=task.created_at,
        estimated_completion=None
    )

@router.get("/{task_id}", response_model=AnalysisTaskResponse)
async def get_task_status(
    task_id: str,
    db: AsyncSession = Depends(get_db_session)
):
    """获取任务状态"""
    task = await db.get(AnalysisTask, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return AnalysisTaskResponse(
        id=task.id,
        youtube_url=task.youtube_url,
        status=task.status,
        current_step=task.current_step,
        progress=task.progress,
        created_at=task.created_at,
        estimated_completion=None
    )

@router.get("/{task_id}/result", response_model=AnalysisResult)
async def get_task_result(
    task_id: str,
    db: AsyncSession = Depends(get_db_session)
):
    """获取任务结果"""
    task = await db.get(AnalysisTask, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if task.status == TaskStatus.COMPLETED:
        return AnalysisResult(
            task_id=task.id,
            result=task.result_data,
            metadata={"completed_at": task.completed_at}
        )
    elif task.status == TaskStatus.FAILED:
        raise HTTPException(status_code=400, detail=task.error_message)
    else:
        raise HTTPException(status_code=202, detail="Task still processing")
```

### 4. WebSocket管理器

```python
# backend/app/api/v1/websocket.py
from fastapi import WebSocket
from typing import Dict, List
import json
import logging

class WebSocketManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, task_id: str):
        await websocket.accept()
        if task_id not in self.active_connections:
            self.active_connections[task_id] = []
        self.active_connections[task_id].append(websocket)
        logging.info(f"WebSocket connected for task {task_id}")
    
    def disconnect(self, task_id: str, websocket: WebSocket = None):
        if task_id in self.active_connections:
            if websocket:
                self.active_connections[task_id].remove(websocket)
            else:
                self.active_connections[task_id] = []
        logging.info(f"WebSocket disconnected for task {task_id}")
    
    async def send_message(self, task_id: str, message: dict):
        if task_id in self.active_connections:
            for connection in self.active_connections[task_id]:
                try:
                    await connection.send_text(json.dumps(message))
                except Exception as e:
                    logging.error(f"Failed to send message: {e}")
                    self.active_connections[task_id].remove(connection)

websocket_manager = WebSocketManager()

async def send_progress_update(task_id: str, progress: int, message: str):
    """发送进度更新"""
    await websocket_manager.send_message(task_id, {
        "type": "progress_update",
        "progress": progress,
        "message": message
    })

async def send_task_completed(task_id: str, result: dict):
    """发送任务完成通知"""
    await websocket_manager.send_message(task_id, {
        "type": "task_completed",
        "result": result
    })

async def send_task_failed(task_id: str, error: dict):
    """发送任务失败通知"""
    await websocket_manager.send_message(task_id, {
        "type": "task_failed",
        "error": error
    })
```

### 5. Celery集成

```python
# backend/app/core/celery_app.py
from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "youtube_analyzer",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.tasks"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30分钟超时
    task_soft_time_limit=25 * 60,  # 25分钟软超时
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)
```

### 6. 数据库配置

```python
# backend/app/core/database.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models.task import Base

engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    pool_pre_ping=True,
    pool_recycle=300,
)

AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

async def init_db():
    """初始化数据库"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_db_session() -> AsyncSession:
    """获取数据库会话"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
```

## 验收标准

### 功能验收
- [ ] FastAPI应用正常启动
- [ ] API端点响应正确
- [ ] WebSocket连接和消息传递正常
- [ ] 数据库操作正确执行
- [ ] Celery任务队列正常工作
- [ ] 错误处理机制完善

### 技术验收
- [ ] API响应时间 < 200ms
- [ ] WebSocket连接稳定
- [ ] 数据库连接池正常工作
- [ ] 并发请求处理能力 > 100 req/s
- [ ] 内存使用合理

### 质量验收
- [ ] API文档自动生成
- [ ] 单元测试覆盖率 ≥ 80%
- [ ] 代码遵循项目规范
- [ ] 错误日志详细有用
- [ ] 性能监控指标完整

## 测试要求

### API测试
```python
# tests/test_api.py
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_create_analysis_task():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post("/api/v1/analysis/", json={
            "youtube_url": "https://youtube.com/watch?v=test",
            "options": {}
        })
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["status"] == "pending"

@pytest.mark.asyncio
async def test_health_check():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
```

### WebSocket测试
```python
# tests/test_websocket.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

def test_websocket_connection():
    client = TestClient(app)
    with client.websocket_connect("/ws/test-task-id") as websocket:
        # 测试连接建立
        assert websocket is not None
```

## 交付物清单

- [ ] FastAPI主应用 (app/main.py)
- [ ] 数据库模型 (app/models/)
- [ ] API路由 (app/api/v1/)
- [ ] WebSocket管理器 (app/api/v1/websocket.py)
- [ ] Celery配置 (app/core/celery_app.py)
- [ ] 数据库配置 (app/core/database.py)
- [ ] Pydantic模式 (app/models/schemas.py)
- [ ] API测试文件
- [ ] 数据库迁移文件

## 关键接口

完成此任务后，需要为后续任务提供：
- 标准化的API接口
- WebSocket实时通信能力
- 数据库操作接口
- Celery任务调度能力

## 预估时间

- 开发时间: 3-4天
- 测试时间: 1天
- 文档时间: 0.5天
- 总计: 4.5-5.5天

## 注意事项

1. 确保API设计符合RESTful规范
2. WebSocket连接要处理断线重连
3. 数据库操作要使用事务
4. 错误处理要统一和完善
5. 性能监控要覆盖关键指标

这是整个系统的API基础，请确保接口的稳定性和可扩展性。
