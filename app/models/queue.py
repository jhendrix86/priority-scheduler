"""
Queue models
"""

from sqlalchemy import Column, String, Integer, DateTime, Boolean, Enum
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid
import enum

from app.database import Base


class QueueStatus(str, enum.Enum):
    """Queue status enumeration"""
    ACTIVE = "active"
    PAUSED = "paused"
    ERROR = "error"


class Queue(Base):
    """Queue model"""
    __tablename__ = "queues"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Queue details
    name = Column(String(100), nullable=False, unique=True)
    description = Column(String(500), nullable=True)
    
    # Status
    status = Column(Enum(QueueStatus), default=QueueStatus.ACTIVE)
    
    # Capacity
    max_size = Column(Integer, nullable=True)
    current_size = Column(Integer, default=0)
    
    # Priority
    priority = Column(Integer, default=5)  # Lower number = higher priority
    
    # Metadata
    extra_metadata = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<Queue {self.name} - {self.status}>"
