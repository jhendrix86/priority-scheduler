from typing import List, Dict, Any
from datetime import datetime
import structlog
from ..schemas.task_schemas import Task
from ..schemas.scheduling_schemas import SchedulingDecision, SchedulingAlgorithm


logger = structlog.get_logger()


class TemporalScheduler:
    """Temporal scheduling algorithm considering time-based constraints."""
    
    def __init__(self):
        self.algorithm = SchedulingAlgorithm.TEMPORAL
    
    async def schedule(
        self,
        task: Task,
        available_resources: Dict[str, Any],
        trace_id: str,
        correlation_id: str
    ) -> SchedulingDecision:
        """Schedule task based on temporal constraints."""
        # Check temporal constraints
        blocked, blocked_reason, estimated_start = self._check_temporal_constraints(task)
        
        if blocked:
            return SchedulingDecision(
                task_id=task.task_id,
                algorithm=self.algorithm,
                scheduled=False,
                priority_score=task.priority / 10.0,
                reason=blocked_reason,
                blocked=True,
                blocked_reason=blocked_reason,
                estimated_start=estimated_start,
                trace_id=trace_id,
                correlation_id=correlation_id
            )
        
        # Calculate temporal score
        temporal_score = self._calculate_temporal_score(task)
        
        # Check other blockers
        resource_blocked, resource_reason = self._check_resources(task, available_resources)
        
        if resource_blocked:
            return SchedulingDecision(
                task_id=task.task_id,
                algorithm=self.algorithm,
                scheduled=False,
                priority_score=temporal_score,
                reason=resource_reason,
                blocked=True,
                blocked_reason=resource_reason,
                trace_id=trace_id,
                correlation_id=correlation_id
            )
        
        queue = self._determine_queue(temporal_score, task.priority)
        
        return SchedulingDecision(
            task_id=task.task_id,
            algorithm=self.algorithm,
            scheduled=True,
            scheduled_at=datetime.utcnow(),
            queue=queue,
            priority_score=temporal_score,
            reason=f"Task scheduled with temporal score {temporal_score:.2f}",
            blocked=False,
            estimated_start=estimated_start,
            trace_id=trace_id,
            correlation_id=correlation_id
        )
    
    def _check_temporal_constraints(self, task: Task) -> tuple[bool, str, datetime]:
        """Check temporal constraints."""
        constraints = task.constraints
        
        # Check if task has a scheduled time
        scheduled_time = constraints.get("scheduled_at")
        if scheduled_time:
            scheduled_dt = datetime.fromisoformat(scheduled_time)
            if datetime.utcnow() < scheduled_dt:
                return True, f"Task scheduled for {scheduled_time}", scheduled_dt
        
        # Check if task has a time window
        window_start = constraints.get("window_start")
        window_end = constraints.get("window_end")
        
        if window_start:
            start_dt = datetime.fromisoformat(window_start)
            if datetime.utcnow() < start_dt:
                return True, f"Task window starts at {start_dt}", start_dt
        
        if window_end:
            end_dt = datetime.fromisoformat(window_end)
            if datetime.utcnow() > end_dt:
                return True, f"Task window ended at {end_dt}", None
        
        # Check if task has a deadline
        deadline = constraints.get("deadline")
        if deadline:
            deadline_dt = datetime.fromisoformat(deadline)
            if datetime.utcnow() > deadline_dt:
                return True, f"Task deadline {deadline_dt} has passed", None
        
        return False, "", None
    
    def _calculate_temporal_score(self, task: Task) -> float:
        """Calculate temporal score."""
        # Base priority
        score = task.priority / 10.0
        
        # Boost for urgent tasks (deadline approaching)
        constraints = task.constraints
        deadline = constraints.get("deadline")
        
        if deadline:
            deadline_dt = datetime.fromisoformat(deadline)
            hours_until = (deadline_dt - datetime.utcnow()).total_seconds() / 3600
            
            if hours_until < 1:
                score += 0.3  # Very urgent
            elif hours_until < 6:
                score += 0.2  # Urgent
            elif hours_until < 24:
                score += 0.1  # Somewhat urgent
        
        # Age bonus (older tasks get priority)
        age_hours = (datetime.utcnow() - task.created_at).total_seconds() / 3600
        if age_hours > 24:
            score += 0.1
        
        return max(0.0, min(1.0, score))
    
    def _check_resources(self, task: Task, resources: Dict[str, Any]) -> tuple[bool, str]:
        """Check resource availability."""
        required_compute = task.resource_requirements.get("compute", 0)
        available_compute = resources.get("compute", 0)
        
        if required_compute > available_compute:
            return True, f"Insufficient compute resources"
        
        return False, ""
    
    def _determine_queue(self, temporal_score: float, priority: int) -> str:
        """Determine queue based on temporal score and priority."""
        combined = (temporal_score + priority / 10.0) / 2.0
        
        if combined >= 0.7:
            return "high_priority"
        elif combined >= 0.4:
            return "normal"
        return "low_priority"
