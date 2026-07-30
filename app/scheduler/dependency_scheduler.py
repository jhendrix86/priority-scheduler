from typing import List, Dict, Any
from datetime import datetime
import structlog
from ..schemas.task_schemas import Task
from ..schemas.scheduling_schemas import SchedulingDecision, SchedulingAlgorithm


logger = structlog.get_logger()


class DependencyScheduler:
    """Dependency-aware scheduling algorithm."""
    
    def __init__(self):
        self.algorithm = SchedulingAlgorithm.DEPENDENCY
        self._completed_tasks: set = set()
    
    async def schedule(
        self,
        task: Task,
        available_resources: Dict[str, Any],
        trace_id: str,
        correlation_id: str
    ) -> SchedulingDecision:
        """Schedule task based on dependency resolution."""
        # Check if dependencies are satisfied
        dependencies_satisfied, blocked_reason = self._check_dependencies(task)
        
        if not dependencies_satisfied:
            return SchedulingDecision(
                task_id=task.task_id,
                algorithm=self.algorithm,
                scheduled=False,
                priority_score=task.priority / 10.0,
                reason=blocked_reason,
                blocked=True,
                blocked_reason=blocked_reason,
                queue="dependency",
                trace_id=trace_id,
                correlation_id=correlation_id
            )
        
        # Check resource availability
        blocked, resource_reason = self._check_resources(task, available_resources)
        
        if blocked:
            return SchedulingDecision(
                task_id=task.task_id,
                algorithm=self.algorithm,
                scheduled=False,
                priority_score=task.priority / 10.0,
                reason=resource_reason,
                blocked=True,
                blocked_reason=resource_reason,
                trace_id=trace_id,
                correlation_id=correlation_id
            )
        
        queue = self._determine_queue(task.priority)
        
        return SchedulingDecision(
            task_id=task.task_id,
            algorithm=self.algorithm,
            scheduled=True,
            scheduled_at=datetime.utcnow(),
            queue=queue,
            priority_score=task.priority / 10.0,
            reason="Dependencies satisfied, task ready to execute",
            blocked=False,
            trace_id=trace_id,
            correlation_id=correlation_id
        )
    
    def mark_task_completed(self, task_id: str):
        """Mark a task as completed for dependency tracking."""
        self._completed_tasks.add(task_id)
    
    def _check_dependencies(self, task: Task) -> tuple[bool, str]:
        """Check if task dependencies are satisfied."""
        if not task.dependencies:
            return True, ""
        
        unsatisfied = [dep for dep in task.dependencies if dep not in self._completed_tasks]
        
        if unsatisfied:
            return False, f"Waiting for dependencies: {', '.join(unsatisfied)}"
        
        return True, ""
    
    def _check_resources(self, task: Task, resources: Dict[str, Any]) -> tuple[bool, str]:
        """Check resource availability."""
        required_compute = task.resource_requirements.get("compute", 0)
        available_compute = resources.get("compute", 0)
        
        if required_compute > available_compute:
            return True, f"Insufficient compute resources"
        
        return False, ""
    
    def _determine_queue(self, priority: int) -> str:
        """Determine queue based on priority."""
        if priority >= 8:
            return "high_priority"
        elif priority >= 5:
            return "normal"
        return "low_priority"
