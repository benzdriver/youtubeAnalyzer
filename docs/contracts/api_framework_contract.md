# API框架接口契约

**提供方**: TASK_02 (后端API框架)  
**使用方**: TASK_04 (YouTube数据提取), TASK_08 (分析编排器), TASK_10 (部署配置)  
**版本**: v1.0.0

## 概述

定义后端API框架的接口规范，包括RESTful API端点、WebSocket通信、数据库操作和Celery任务调度。

## RESTful API接口

### 基础响应格式

```typescript
interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: {
    code: string;
    message: string;
    details?: any;
  };
  timestamp: string;
  request_id: string;
}
```

### 分析任务API

#### 创建分析任务

```http
POST /api/v1/analyze
Content-Type: application/json

{
  "youtube_url": "https://youtube.com/watch?v=example",
  "options": {
    "max_comments": 1000,
    "enable_transcription": true,
    "analysis_depth": "detailed"
  }
}
```

**响应**:
```json
{
  "success": true,
  "data": {
    "task_id": "uuid-string",
    "status": "pending",
    "created_at": "2025-06-06T01:00:00Z",
    "estimated_completion": "2025-06-06T01:10:00Z"
  },
  "timestamp": "2025-06-06T01:00:00Z",
  "request_id": "req-uuid"
}
```

#### 获取任务状态

```http
GET /api/v1/tasks/{task_id}
```

**响应**:
```json
{
  "success": true,
  "data": {
    "task_id": "uuid-string",
    "status": "processing",
    "progress": 45,
    "current_step": "音频转录中",
    "created_at": "2025-06-06T01:00:00Z",
    "updated_at": "2025-06-06T01:05:00Z",
    "youtube_url": "https://youtube.com/watch?v=example"
  }
}
```

#### 获取分析结果

```http
GET /api/v1/tasks/{task_id}/result
```

**响应**:
```json
{
  "success": true,
  "data": {
    "task_id": "uuid-string",
    "status": "completed",
    "result": {
      "summary": { /* VideoInfo */ },
      "content_insights": { /* ContentInsights */ },
      "comment_insights": { /* CommentInsights */ },
      "comprehensive_insights": ["洞察1", "洞察2"],
      "recommendations": ["建议1", "建议2"]
    },
    "completed_at": "2025-06-06T01:10:00Z"
  }
}
```

### 健康检查API

```http
GET /health
```

**响应**:
```json
{
  "status": "healthy",
  "timestamp": "2025-06-06T01:00:00Z",
  "services": {
    "database": "healthy",
    "redis": "healthy",
    "celery": "healthy"
  }
}
```

## 数据库模型接口

### AnalysisTask模型

```python
from sqlalchemy import Column, String, Integer, DateTime, Text, JSON
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class AnalysisTask(Base):
    __tablename__ = "analysis_tasks"
    
    id = Column(String, primary_key=True)
    youtube_url = Column(String, nullable=False)
    status = Column(String, default="pending")  # pending, processing, completed, failed
    progress = Column(Integer, default=0)
    current_step = Column(String)
    
    # 时间戳
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    completed_at = Column(DateTime)
    
    # 配置和结果
    options = Column(JSON)
    result = Column(JSON)
    error_message = Column(Text)
    
    def to_dict(self):
        return {
            "task_id": self.id,
            "youtube_url": self.youtube_url,
            "status": self.status,
            "progress": self.progress,
            "current_step": self.current_step,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "options": self.options,
            "result": self.result,
            "error_message": self.error_message
        }
```

### 数据库操作接口

```python
from abc import ABC, abstractmethod
from typing import Optional, List

class TaskRepository(ABC):
    
    @abstractmethod
    async def create_task(self, task_data: dict) -> AnalysisTask:
        """创建新任务"""
        pass
    
    @abstractmethod
    async def get_task(self, task_id: str) -> Optional[AnalysisTask]:
        """获取任务"""
        pass
    
    @abstractmethod
    async def update_task(self, task_id: str, updates: dict) -> AnalysisTask:
        """更新任务"""
        pass
    
    @abstractmethod
    async def list_tasks(self, limit: int = 10, offset: int = 0) -> List[AnalysisTask]:
        """列出任务"""
        pass
    
    @abstractmethod
    async def delete_task(self, task_id: str) -> bool:
        """删除任务"""
        pass
```

## WebSocket通信接口

### WebSocket管理器

```python
from fastapi import WebSocket
from typing import Dict, List
import json

class WebSocketManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, task_id: str):
        """建立连接"""
        await websocket.accept()
        if task_id not in self.active_connections:
            self.active_connections[task_id] = []
        self.active_connections[task_id].append(websocket)
    
    def disconnect(self, websocket: WebSocket, task_id: str):
        """断开连接"""
        if task_id in self.active_connections:
            self.active_connections[task_id].remove(websocket)
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        """发送个人消息"""
        await websocket.send_text(message)
    
    async def broadcast_to_task(self, task_id: str, message: dict):
        """广播到任务"""
        if task_id in self.active_connections:
            for connection in self.active_connections[task_id]:
                await connection.send_text(json.dumps(message))
```

### WebSocket端点

```python
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()

@router.websocket("/ws/{task_id}")
async def websocket_endpoint(websocket: WebSocket, task_id: str):
    await websocket_manager.connect(websocket, task_id)
    try:
        while True:
            data = await websocket.receive_text()
            # 处理客户端消息
            await handle_websocket_message(task_id, data)
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket, task_id)
```

## Celery任务接口

### 任务定义

```python
from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "youtube_analyzer",
    broker=settings.redis_url,
    backend=settings.redis_url
)

@celery_app.task(bind=True)
def analyze_youtube_video(self, task_id: str, youtube_url: str, options: dict):
    """YouTube视频分析任务"""
    try:
        # 更新任务状态
        update_task_progress(task_id, 0, "开始分析")
        
        # 执行分析步骤
        result = perform_analysis(task_id, youtube_url, options)
        
        # 完成任务
        update_task_status(task_id, "completed", result)
        
        return result
        
    except Exception as e:
        # 任务失败
        update_task_status(task_id, "failed", error=str(e))
        raise
```

### 任务状态更新接口

```python
async def update_task_progress(task_id: str, progress: int, message: str):
    """更新任务进度"""
    # 更新数据库
    await task_repository.update_task(task_id, {
        "progress": progress,
        "current_step": message,
        "updated_at": datetime.utcnow()
    })
    
    # 发送WebSocket消息
    await websocket_manager.broadcast_to_task(task_id, {
        "type": "progress_update",
        "data": {
            "progress": progress,
            "message": message
        }
    })

async def update_task_status(task_id: str, status: str, result: dict = None, error: str = None):
    """更新任务状态"""
    updates = {
        "status": status,
        "updated_at": datetime.utcnow()
    }
    
    if status == "completed":
        updates["completed_at"] = datetime.utcnow()
        updates["result"] = result
        updates["progress"] = 100
    elif status == "failed":
        updates["error_message"] = error
    
    await task_repository.update_task(task_id, updates)
    
    # 发送WebSocket消息
    await websocket_manager.broadcast_to_task(task_id, {
        "type": f"task_{status}",
        "data": updates
    })
```

## 错误处理接口

### 异常类型

```python
class APIError(Exception):
    """API错误基类"""
    def __init__(self, message: str, code: str = "API_ERROR", status_code: int = 500):
        self.message = message
        self.code = code
        self.status_code = status_code
        super().__init__(message)

class ValidationError(APIError):
    """验证错误"""
    def __init__(self, message: str, field: str = None):
        super().__init__(message, "VALIDATION_ERROR", 400)
        self.field = field

class NotFoundError(APIError):
    """资源不存在错误"""
    def __init__(self, resource: str, id: str):
        super().__init__(f"{resource} not found: {id}", "NOT_FOUND", 404)

class TaskError(APIError):
    """任务执行错误"""
    def __init__(self, message: str, task_id: str):
        super().__init__(message, "TASK_ERROR", 500)
        self.task_id = task_id
```

### 错误处理中间件

```python
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse

async def error_handler(request: Request, exc: Exception):
    """全局错误处理"""
    if isinstance(exc, APIError):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "error": {
                    "code": exc.code,
                    "message": exc.message
                },
                "timestamp": datetime.utcnow().isoformat(),
                "request_id": str(uuid.uuid4())
            }
        )
    
    # 未知错误
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "Internal server error"
            },
            "timestamp": datetime.utcnow().isoformat(),
            "request_id": str(uuid.uuid4())
        }
    )
```

## 验证规则

### 请求验证

```python
from pydantic import BaseModel, HttpUrl, validator

class AnalyzeRequest(BaseModel):
    youtube_url: HttpUrl
    options: dict = {}
    
    @validator('youtube_url')
    def validate_youtube_url(cls, v):
        url_str = str(v)
        if not any(domain in url_str for domain in ['youtube.com', 'youtu.be']):
            raise ValueError('必须是有效的YouTube URL')
        return v
    
    @validator('options')
    def validate_options(cls, v):
        allowed_keys = ['max_comments', 'enable_transcription', 'analysis_depth']
        for key in v.keys():
            if key not in allowed_keys:
                raise ValueError(f'不支持的选项: {key}')
        return v
```

### 响应验证

```python
class TaskResponse(BaseModel):
    task_id: str
    status: str
    progress: int = 0
    current_step: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    youtube_url: HttpUrl
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
```

## 性能要求

### API响应时间

- **创建任务**: < 200ms
- **获取状态**: < 100ms
- **获取结果**: < 500ms
- **健康检查**: < 50ms

### 并发处理

- **同时处理任务数**: 10个
- **WebSocket连接数**: 100个
- **API请求频率**: 100 req/min per IP

## 安全要求

### 认证和授权

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer

security = HTTPBearer()

async def verify_token(token: str = Depends(security)):
    """验证访问令牌"""
    try:
        # 验证JWT令牌
        payload = jwt.decode(token.credentials, settings.secret_key, algorithms=["HS256"])
        return payload
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )
```

### 速率限制

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.post("/analyze")
@limiter.limit("10/minute")
async def create_analysis_task(request: Request, data: AnalyzeRequest):
    """创建分析任务（限制频率）"""
    pass
```

## 测试接口

### 单元测试

```python
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_create_task():
    """测试创建任务"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post("/api/v1/analyze", json={
            "youtube_url": "https://youtube.com/watch?v=test",
            "options": {"max_comments": 100}
        })
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "task_id" in data["data"]

@pytest.mark.asyncio
async def test_get_task_status():
    """测试获取任务状态"""
    # 先创建任务
    task_id = "test-task-id"
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get(f"/api/v1/tasks/{task_id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
```

### 集成测试

```python
@pytest.mark.integration
async def test_full_analysis_workflow():
    """测试完整分析流程"""
    # 创建任务
    create_response = await client.post("/api/v1/analyze", json={
        "youtube_url": "https://youtube.com/watch?v=dQw4w9WgXcQ"
    })
    task_id = create_response.json()["data"]["task_id"]
    
    # 等待任务完成
    while True:
        status_response = await client.get(f"/api/v1/tasks/{task_id}")
        status = status_response.json()["data"]["status"]
        
        if status in ["completed", "failed"]:
            break
        
        await asyncio.sleep(1)
    
    # 获取结果
    result_response = await client.get(f"/api/v1/tasks/{task_id}/result")
    assert result_response.status_code == 200
```

## 使用示例

### 创建FastAPI应用

```python
from fastapi import FastAPI
from app.api.v1 import tasks, health
from app.core.websocket import websocket_router

app = FastAPI(title="YouTube Analyzer API", version="1.0.0")

# 注册路由
app.include_router(tasks.router, prefix="/api/v1", tags=["tasks"])
app.include_router(health.router, tags=["health"])
app.include_router(websocket_router, prefix="/ws")

# 注册中间件
app.add_exception_handler(APIError, error_handler)
```

### 使用数据库

```python
from app.database import get_db
from app.repositories.task_repository import TaskRepository

async def create_analysis_task(data: AnalyzeRequest, db = Depends(get_db)):
    """创建分析任务"""
    task_repo = TaskRepository(db)
    
    task_data = {
        "id": str(uuid.uuid4()),
        "youtube_url": str(data.youtube_url),
        "options": data.options,
        "status": "pending",
        "created_at": datetime.utcnow()
    }
    
    task = await task_repo.create_task(task_data)
    
    # 启动异步任务
    analyze_youtube_video.delay(task.id, task.youtube_url, task.options)
    
    return {"success": True, "data": task.to_dict()}
```
