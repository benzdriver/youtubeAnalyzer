import enum
import uuid
from datetime import datetime

from sqlalchemy import JSON, Column, DateTime, Enum, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class TaskStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AnalysisType(str, enum.Enum):
    BASIC = "basic"
    DETAILED = "detailed"
    COMPREHENSIVE = "comprehensive"


class AnalysisTask(Base):
    __tablename__ = "tasks"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    video_url = Column(String, nullable=False)
    analysis_type = Column(Enum(AnalysisType), default=AnalysisType.BASIC, nullable=False)
    status = Column(Enum(TaskStatus), default=TaskStatus.PENDING, nullable=False)
    current_step = Column(String)
    progress = Column(Integer, default=0)
    options = Column(JSON)
    result_data = Column(JSON)
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
    completed_at = Column(DateTime)

    def to_dict(self):
        return {
            "id": self.id,
            "video_url": self.video_url,
            "analysis_type": self.analysis_type.value,
            "status": self.status.value,
            "current_step": self.current_step,
            "progress": self.progress,
            "options": self.options,
            "result_data": self.result_data,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "completed_at": (
                self.completed_at.isoformat() if self.completed_at else None
            ),
        }
