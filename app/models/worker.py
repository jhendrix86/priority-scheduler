"""
Worker models
"""

from sqlalchemy import Column, String, Integer, DateTime, Boolean, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from app.database import Base


class WorkerStatus(str, enum.Enum):
    """Worker status enumeration"""
    IDLE = "idle"
    BUSY = "busy"
    OFFLINE = "offline"
    ERROR = "error"


class Worker(Base):
    """Worker model"""
    __tablename__ = "workers"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Worker details
    name = Column(String(255), nullable=False)
    worker_type = Column(String(50), nullable=False)
    
    # Status
    status = Column(Enum(WorkerStatus), default=WorkerStatus.IDLE)
    
    # Performance
    tasks_completed = Column(Integer, default=0)
    tasks_failed = Column(Integer, default=0)
    
    # Current task
    current_task_id = Column(UUID(as_uuid=True), ForeignKey("tasks.id"), nullable=True)
    
    # Metadata
    extra_metadata = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_heartbeat = Column(DateTime, nullable=True)
    
    # Relationships
    tasks = relationship("Task")
    
    def __repr__(self):
        return f"<Worker {self.name} - {self.status}>"
