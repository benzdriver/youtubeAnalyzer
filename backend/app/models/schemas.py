from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field, HttpUrl

from .task import TaskStatus


class AnalysisTaskCreate(BaseModel):
    video_url: HttpUrl
    analysis_type: str = "basic"
    options: Optional[Dict[str, Any]] = Field(default_factory=dict)


class AnalysisTaskResponse(BaseModel):
    id: str
    video_url: str
    analysis_type: str
    status: TaskStatus
    current_step: Optional[str] = None
    progress: int = 0
    options: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    estimated_completion: Optional[datetime] = None


class AnalysisResult(BaseModel):
    task_id: str
    result: Dict[str, Any]
    metadata: Dict[str, Any]


class TaskStatusUpdate(BaseModel):
    status: TaskStatus
    current_step: Optional[str] = None
    progress: Optional[int] = None
    error_message: Optional[str] = None


class WebSocketMessage(BaseModel):
    type: str
    task_id: str
    data: Dict[str, Any]


class ProgressUpdate(BaseModel):
    type: str = "progress_update"
    progress: int
    message: str
    current_step: Optional[str] = None


class TaskCompleted(BaseModel):
    type: str = "task_completed"
    result: Dict[str, Any]


class TaskFailed(BaseModel):
    type: str = "task_failed"
    error: Dict[str, Any]


class HealthResponse(BaseModel):
    status: str
    version: str
    timestamp: float
    checks: Optional[Dict[str, bool]] = None


class ErrorResponse(BaseModel):
    success: bool = False
    error: Dict[str, str]
    timestamp: float
    request_id: str
