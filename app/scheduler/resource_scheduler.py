from typing import List, Dict, Any
from datetime import datetime
import structlog
from ..schemas.task_schemas import Task
from ..schemas.scheduling_schemas import SchedulingDecision, SchedulingAlgorithm
from ..utils.config import settings


logger = structlog.get_logger()


class ResourceScheduler:
    """Resource-aware scheduling algorithm."""
    
    def __init__(self):
        self.algorithm = SchedulingAlgorithm.RESOURCE_AWARE
        self.max_compute = settings.max_compute_per_task
        self.max_api = settings.max_api_rate_per_task
        self.max_budget = settings.max_budget_per_task
    
    async def schedule(
        self,
        task: Task,
        available_resources: Dict[str, Any],
        trace_id: str,
        correlation_id: str
    ) -> SchedulingDecision:
        """Schedule task based on resource availability and efficiency."""
        # Calculate resource score
        resource_score = self._calculate_resource_score(task, available_resources)
        
        # Check resource constraints
        blocked, blocked_reason = self._check_resource_constraints(task, available_resources)
        
        if blocked:
            return SchedulingDecision(
                task_id=task.task_id,
                algorithm=self.algorithm,
                scheduled=False,
                priority_score=resource_score,
                reason=blocked_reason,
                blocked=True,
                blocked_reason=blocked_reason,
                trace_id=trace_id,
                correlation_id=correlation_id
            )
        
        queue = self._determine_queue(resource_score)
        
        # Allocate resources
        resource_allocation = self._allocate_resources(task)
        
        return SchedulingDecision(
            task_id=task.task_id,
            algorithm=self.algorithm,
            scheduled=True,
            scheduled_at=datetime.utcnow(),
            queue=queue,
            priority_score=resource_score,
            reason=f"Task scheduled with resource score {resource_score:.2f}",
            blocked=False,
            resource_allocation=resource_allocation,
            trace_id=trace_id,
            correlation_id=correlation_id
        )
    
    def _calculate_resource_score(self, task: Task, available: Dict[str, Any]) -> float:
        """Calculate resource efficiency score."""
        req_compute = task.resource_requirements.get("compute", 0)
        req_api = task.resource_requirements.get("api", 0)
        req_budget = task.resource_requirements.get("budget", 0)
        
        avail_compute = available.get("compute", 0)
        avail_api = available.get("api", 0)
        avail_budget = available.get("budget", 0)
        
        # Availability score (how much of request can be satisfied)
        compute_avail = min(req_compute / avail_compute, 1.0) if avail_compute > 0 else 0
        api_avail = min(req_api / avail_api, 1.0) if avail_api > 0 else 0
        budget_avail = min(req_budget / avail_budget, 1.0) if avail_budget > 0 else 0
        
        # Efficiency score (lower requirements = higher efficiency)
        compute_eff = 1.0 - min(req_compute / self.max_compute, 1.0)
        api_eff = 1.0 - min(req_api / self.max_api, 1.0)
        budget_eff = 1.0 - min(req_budget / self.max_budget, 1.0)
        
        # Combined score
        resource_score = (
            (compute_avail + api_avail + budget_avail) / 3.0 * 0.5 +
            (compute_eff + api_eff + budget_eff) / 3.0 * 0.5
        )
        
        return resource_score
    
    def _check_resource_constraints(self, task: Task, available: Dict[str, Any]) -> tuple[bool, str]:
        """Check if resource constraints are satisfied."""
        req_compute = task.resource_requirements.get("compute", 0)
        req_api = task.resource_requirements.get("api", 0)
        req_budget = task.resource_requirements.get("budget", 0)
        
        avail_compute = available.get("compute", 0)
        avail_api = available.get("api", 0)
        avail_budget = available.get("budget", 0)
        
        if req_compute > self.max_compute:
            return True, f"Compute requirement {req_compute} exceeds maximum {self.max_compute}"
        
        if req_api > self.max_api:
            return True, f"API requirement {req_api} exceeds maximum {self.max_api}"
        
        if req_budget > self.max_budget:
            return True, f"Budget requirement {req_budget} exceeds maximum {self.max_budget}"
        
        if req_compute > avail_compute:
            return True, f"Insufficient compute: need {req_compute}, have {avail_compute}"
        
        if req_api > avail_api:
            return True, f"Insufficient API quota: need {req_api}, have {avail_api}"
        
        if req_budget > avail_budget:
            return True, f"Insufficient budget: need {req_budget}, have {avail_budget}"
        
        return False, ""
    
    def _allocate_resources(self, task: Task) -> Dict[str, Any]:
        """Allocate resources for the task."""
        return {
            "compute": task.resource_requirements.get("compute", 0),
            "api": task.resource_requirements.get("api", 0),
            "budget": task.resource_requirements.get("budget", 0)
        }
    
    def _determine_queue(self, score: float) -> str:
        """Determine queue based on resource score."""
        if score >= 0.8:
            return "high_priority"
        elif score >= 0.5:
            return "normal"
        return "low_priority"
