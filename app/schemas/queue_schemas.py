from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class QueueType(str, Enum):
    """Queue types."""
    HIGH_PRIORITY = "high_priority"
    NORMAL = "normal"
    LOW_PRIORITY = "low_priority"
    SCHEDULED = "scheduled"
    DEPENDENCY = "dependency"
    RETRY = "retry"
    DLQ = "dlq"


class QueueStatus(BaseModel):
    """Queue status."""
    queue_name: str
    queue_type: QueueType
    size: int = Field(..., description="Number of tasks in queue")
    max_size: Optional[int] = Field(None, description="Maximum queue size")
    processing: int = Field(default=0, description="Number of tasks being processed")
    blocked: int = Field(default=0, description="Number of blocked tasks")
    last_updated: datetime = Field(default_factory=datetime.utcnow)


class QueueStats(BaseModel):
    """Queue statistics."""
    total_queues: int
    total_tasks: int
    queue_breakdown: Dict[str, int]
    throughput: Dict[str, float]  # tasks per second
    average_wait_time: float  # seconds
    average_processing_time: float  # seconds
    error_rate: float
