from typing import List, Dict, Any
from datetime import datetime
import structlog
from ..schemas.task_schemas import Task
from ..schemas.scheduling_schemas import SchedulingDecision, SchedulingAlgorithm


logger = structlog.get_logger()


class PriorityScheduler:
    """Priority-based scheduling algorithm."""
    
    def __init__(self):
        self.algorithm = SchedulingAlgorithm.PRIORITY
    
    async def schedule(
        self,
        task: Task,
        available_resources: Dict[str, Any],
        trace_id: str,
        correlation_id: str
    ) -> SchedulingDecision:
        """Schedule task based on priority."""
        # Calculate priority score
        priority_score = self._calculate_priority_score(task)
        
        # Check if task can be scheduled
        blocked, blocked_reason = self._check_blockers(task, available_resources)
        
        if blocked:
            return SchedulingDecision(
                task_id=task.task_id,
                algorithm=self.algorithm,
                scheduled=False,
                priority_score=priority_score,
                reason=blocked_reason,
                blocked=True,
                blocked_reason=blocked_reason,
                trace_id=trace_id,
                correlation_id=correlation_id
            )
        
        # Determine queue based on priority
        queue = self._determine_queue(task.priority)
        
        return SchedulingDecision(
            task_id=task.task_id,
            algorithm=self.algorithm,
            scheduled=True,
            scheduled_at=datetime.utcnow(),
            queue=queue,
            priority_score=priority_score,
            reason=f"Task scheduled based on priority {task.priority}",
            blocked=False,
            trace_id=trace_id,
            correlation_id=correlation_id
        )
    
    def _calculate_priority_score(self, task: Task) -> float:
        """Calculate priority score from task priority."""
        # Normalize priority (1-10) to score (0-1)
        return task.priority / 10.0
    
    def _check_blockers(self, task: Task, resources: Dict[str, Any]) -> tuple[bool, str]:
        """Check if task is blocked."""
        # Check dependencies
        if task.dependencies:
            return True, "Waiting for dependencies to complete"
        
        # Check resource availability
        required_compute = task.resource_requirements.get("compute", 0)
        available_compute = resources.get("compute", 0)
        
        if required_compute > available_compute:
            return True, f"Insufficient compute resources (need {required_compute}, have {available_compute})"
        
        return False, ""
    
    def _determine_queue(self, priority: int) -> str:
        """Determine queue based on priority level."""
        if priority >= 8:
            return "high_priority"
        elif priority >= 5:
            return "normal"
        else:
            return "low_priority"
