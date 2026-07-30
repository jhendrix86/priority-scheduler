from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class SchedulingAlgorithm(str, Enum):
    """Scheduling algorithms."""
    PRIORITY = "priority"
    WEIGHTED = "weighted"
    DEPENDENCY = "dependency"
    FAIRNESS = "fairness"
    RESOURCE_AWARE = "resource_aware"
    RISK_AWARE = "risk_aware"
    STRATEGY_AWARE = "strategy_aware"
    TEMPORAL = "temporal"
    CAUSAL = "causal"


class SchedulingDecision(BaseModel):
    """Scheduling decision."""
    task_id: str
    algorithm: SchedulingAlgorithm
    scheduled: bool = Field(..., description="Whether the task was scheduled")
    scheduled_at: Optional[datetime] = Field(None, description="When the task was scheduled")
    queue: Optional[str] = Field(None, description="Queue the task was placed in")
    priority_score: float = Field(..., description="Computed priority score")
    reason: str = Field(..., description="Reason for scheduling decision")
    blocked: bool = Field(default=False, description="Whether the task is blocked")
    blocked_reason: Optional[str] = Field(None, description="Reason for blocking")
    estimated_start: Optional[datetime] = Field(None, description="Estimated start time")
    resource_allocation: Dict[str, Any] = Field(default_factory=dict, description="Allocated resources")
    governance_check: Dict[str, Any] = Field(default_factory=dict, description="Governance check results")
    trace_id: str = Field(..., description="Trace ID")
    correlation_id: str = Field(..., description="Correlation ID")
