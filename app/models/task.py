"""
Task models
"""

from sqlalchemy import Column, String, Integer, DateTime, Boolean, Enum, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from app.database import Base


class TaskStatus(str, enum.Enum):
    """Task status enumeration"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


class TaskPriority(str, enum.Enum):
    """Task priority enumeration"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    BACKGROUND = "background"


class Task(Base):
    """Task model"""
    __tablename__ = "tasks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Task details
    task_type = Column(String(100), nullable=False)
    priority = Column(Enum(TaskPriority), default=TaskPriority.MEDIUM)
    
    # Payload
    payload = Column(JSON, nullable=False)
    
    # Status
    status = Column(Enum(TaskStatus), default=TaskStatus.PENDING)
    
    # Queue
    queue_name = Column(String(100), nullable=False)
    
    # Dependencies
    depends_on = Column(JSON, nullable=True)  # List of task IDs
    
    # Execution
    worker_id = Column(UUID(as_uuid=True), ForeignKey("workers.id"), nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Retry
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    
    # Error handling
    error_message = Column(String(500), nullable=True)
    
    # Result
    result = Column(JSON, nullable=True)
    
    # Metadata
    metadata = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    worker = relationship("Worker")
    
    def __repr__(self):
        return f"<Task {self.id} - {self.task_type} - {self.status}>"
