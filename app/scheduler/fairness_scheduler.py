from typing import List, Dict, Any
from datetime import datetime
import structlog
from ..schemas.task_schemas import Task
from ..schemas.scheduling_schemas import SchedulingDecision, SchedulingAlgorithm


logger = structlog.get_logger()


class FairnessScheduler:
    """Fairness-based scheduling algorithm to prevent starvation."""
    
    def __init__(self):
        self.algorithm = SchedulingAlgorithm.FAIRNESS
        self._engine_task_counts: Dict[str, int] = {}
        self._last_scheduled: Dict[str, datetime] = {}
    
    async def schedule(
        self,
        task: Task,
        available_resources: Dict[str, Any],
        trace_id: str,
        correlation_id: str
    ) -> SchedulingDecision:
        """Schedule task based on fairness across engines."""
        # Calculate fairness score
        fairness_score = self._calculate_fairness_score(task)
        
        # Check blockers
        blocked, blocked_reason = self._check_blockers(task, available_resources)
        
        if blocked:
            return SchedulingDecision(
                task_id=task.task_id,
                algorithm=self.algorithm,
                scheduled=False,
                priority_score=fairness_score,
                reason=blocked_reason,
                blocked=True,
                blocked_reason=blocked_reason,
                trace_id=trace_id,
                correlation_id=correlation_id
            )
        
        queue = self._determine_queue(task.priority, fairness_score)
        
        # Update tracking
        self._engine_task_counts[task.owner_engine] = self._engine_task_counts.get(task.owner_engine, 0) + 1
        self._last_scheduled[task.owner_engine] = datetime.utcnow()
        
        return SchedulingDecision(
            task_id=task.task_id,
            algorithm=self.algorithm,
            scheduled=True,
            scheduled_at=datetime.utcnow(),
            queue=queue,
            priority_score=fairness_score,
            reason=f"Task scheduled with fairness score {fairness_score:.2f}",
            blocked=False,
            trace_id=trace_id,
            correlation_id=correlation_id
        )
    
    def _calculate_fairness_score(self, task: Task) -> float:
        """Calculate fairness score based on engine task distribution."""
        # Base priority score
        priority_score = task.priority / 10.0
        
        # Fairness penalty for engines with many tasks
        engine_count = self._engine_task_counts.get(task.owner_engine, 0)
        fairness_penalty = min(engine_count / 20.0, 0.5)  # Max 50% penalty
        
        # Time since last scheduled for this engine
        last_scheduled = self._last_scheduled.get(task.owner_engine)
        if last_scheduled:
            hours_since = (datetime.utcnow() - last_scheduled).total_seconds() / 3600
            time_bonus = min(hours_since / 12.0, 0.3)  # Max 30% bonus after 12 hours
        else:
            time_bonus = 0.3  # First time scheduling this engine
        
        fairness_score = priority_score - fairness_penalty + time_bonus
        return max(0.0, min(1.0, fairness_score))
    
    def _check_blockers(self, task: Task, resources: Dict[str, Any]) -> tuple[bool, str]:
        """Check if task is blocked."""
        if task.dependencies:
            return True, "Waiting for dependencies"
        
        required_compute = task.resource_requirements.get("compute", 0)
        available_compute = resources.get("compute", 0)
        
        if required_compute > available_compute:
            return True, f"Insufficient compute resources"
        
        return False, ""
    
    def _determine_queue(self, priority: int, fairness_score: float) -> str:
        """Determine queue based on priority and fairness."""
        combined_score = (priority / 10.0 + fairness_score) / 2.0
        
        if combined_score >= 0.7:
            return "high_priority"
        elif combined_score >= 0.4:
            return "normal"
        return "low_priority"
