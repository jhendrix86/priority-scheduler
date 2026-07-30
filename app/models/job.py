"""
Job models
"""

from sqlalchemy import Column, String, Integer, DateTime, Boolean, Enum, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid
import enum

from app.database import Base


class JobStatus(str, enum.Enum):
    """Job status enumeration"""
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Job(Base):
    """Job model"""
    __tablename__ = "jobs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Job details
    name = Column(String(255), nullable=False)
    job_type = Column(String(100), nullable=False)
    
    # Schedule
    cron_expression = Column(String(100), nullable=False)
    timezone = Column(String(50), default="UTC")
    
    # Status
    status = Column(Enum(JobStatus), default=JobStatus.ACTIVE)
    
    # Payload
    payload = Column(JSON, nullable=False)
    
    # Execution
    last_run_at = Column(DateTime, nullable=True)
    next_run_at = Column(DateTime, nullable=True)
    run_count = Column(Integer, default=0)
    
    # Metadata
    metadata = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<Job {self.name} - {self.status}>"
