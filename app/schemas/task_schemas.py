from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class TaskStatus(str, Enum):
    """Task status."""
    PENDING = "pending"
    QUEUED = "queued"
    SCHEDULED = "scheduled"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"
    BLOCKED = "blocked"


class TaskPriority(str, Enum):
    """Task priority levels."""
    CRITICAL = "critical"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"


class Task(BaseModel):
    """Task model."""
    task_id: str = Field(..., description="Unique task identifier")
    task_type: str = Field(..., description="Type of task")
    priority: int = Field(default=5, ge=1, le=10, description="Priority level (1-10)")
    dependencies: List[str] = Field(default_factory=list, description="Task dependencies")
    constraints: Dict[str, Any] = Field(default_factory=dict, description="Task constraints")
    resource_requirements: Dict[str, Any] = Field(default_factory=dict, description="Resource requirements")
    risk_level: float = Field(default=0.0, ge=0.0, le=1.0, description="Risk level (0-1)")
    strategy_alignment: float = Field(default=1.0, ge=0.0, le=1.0, description="Strategy alignment score (0-1)")
    lifecycle_stage: TaskStatus = Field(default=TaskStatus.PENDING, description="Task lifecycle stage")
    version: str = Field(default="1.0.0", description="Task version")
    owner_engine: str = Field(..., description="Engine that owns this task")
    retry_policy: Dict[str, Any] = Field(default_factory=dict, description="Retry policy")
    timeout_policy: Dict[str, Any] = Field(default_factory=dict, description="Timeout policy")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Task creation time")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update time")
    scheduled_at: Optional[datetime] = Field(None, description="Scheduled time")
    started_at: Optional[datetime] = Field(None, description="Start time")
    completed_at: Optional[datetime] = Field(None, description="Completion time")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    retry_count: int = Field(default=0, description="Number of retries")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class TaskSubmitRequest(BaseModel):
    """Request to submit a task."""
    task_type: str = Field(..., description="Type of task")
    priority: int = Field(default=5, ge=1, le=10, description="Priority level (1-10)")
    dependencies: List[str] = Field(default_factory=list, description="Task dependencies")
    constraints: Dict[str, Any] = Field(default_factory=dict, description="Task constraints")
    resource_requirements: Dict[str, Any] = Field(default_factory=dict, description="Resource requirements")
    risk_level: float = Field(default=0.0, ge=0.0, le=1.0, description="Risk level (0-1)")
    strategy_alignment: float = Field(default=1.0, ge=0.0, le=1.0, description="Strategy alignment score (0-1)")
    owner_engine: str = Field(..., description="Engine that owns this task")
    retry_policy: Dict[str, Any] = Field(default_factory=dict, description="Retry policy")
    timeout_policy: Dict[str, Any] = Field(default_factory=dict, description="Timeout policy")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    trace_id: Optional[str] = Field(None, description="Trace ID for distributed tracing")
    correlation_id: Optional[str] = Field(None, description="Correlation ID")
