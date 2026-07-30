from typing import List, Dict, Any
from datetime import datetime
import structlog
from ..schemas.task_schemas import Task
from ..schemas.scheduling_schemas import SchedulingDecision, SchedulingAlgorithm


logger = structlog.get_logger()


class WeightedScheduler:
    """Weighted scheduling algorithm considering multiple factors."""
    
    def __init__(self):
        self.algorithm = SchedulingAlgorithm.WEIGHTED
        self.weights = {
            "priority": 0.4,
            "strategy_alignment": 0.2,
            "risk": 0.2,
            "age": 0.1,
            "resource_efficiency": 0.1
        }
    
    async def schedule(
        self,
        task: Task,
        available_resources: Dict[str, Any],
        trace_id: str,
        correlation_id: str
    ) -> SchedulingDecision:
        """Schedule task based on weighted score."""
        # Calculate weighted score
        priority_score = self._calculate_weighted_score(task)
        
        # Check blockers
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
        
        queue = self._determine_queue(priority_score)
        
        return SchedulingDecision(
            task_id=task.task_id,
            algorithm=self.algorithm,
            scheduled=True,
            scheduled_at=datetime.utcnow(),
            queue=queue,
            priority_score=priority_score,
            reason=f"Task scheduled with weighted score {priority_score:.2f}",
            blocked=False,
            trace_id=trace_id,
            correlation_id=correlation_id
        )
    
    def _calculate_weighted_score(self, task: Task) -> float:
        """Calculate weighted score from multiple factors."""
        # Priority component (normalized 0-1)
        priority_score = task.priority / 10.0
        
        # Strategy alignment component
        strategy_score = task.strategy_alignment
        
        # Risk component (lower risk = higher score)
        risk_score = 1.0 - task.risk_level
        
        # Age component (older tasks get higher score)
        age_hours = (datetime.utcnow() - task.created_at).total_seconds() / 3600
        age_score = min(age_hours / 24.0, 1.0)  # Max score after 24 hours
        
        # Resource efficiency component
        resource_efficiency = self._calculate_resource_efficiency(task)
        
        # Weighted sum
        weighted_score = (
            self.weights["priority"] * priority_score +
            self.weights["strategy_alignment"] * strategy_score +
            self.weights["risk"] * risk_score +
            self.weights["age"] * age_score +
            self.weights["resource_efficiency"] * resource_efficiency
        )
        
        return weighted_score
    
    def _calculate_resource_efficiency(self, task: Task) -> float:
        """Calculate resource efficiency score."""
        req_compute = task.resource_requirements.get("compute", 0)
        req_api = task.resource_requirements.get("api", 0)
        
        # Lower resource requirements = higher efficiency
        if req_compute > 0:
            compute_eff = 1.0 - min(req_compute / 100.0, 1.0)
        else:
            compute_eff = 1.0
        
        if req_api > 0:
            api_eff = 1.0 - min(req_api / 1000.0, 1.0)
        else:
            api_eff = 1.0
        
        return (compute_eff + api_eff) / 2.0
    
    def _check_blockers(self, task: Task, resources: Dict[str, Any]) -> tuple[bool, str]:
        """Check if task is blocked."""
        if task.dependencies:
            return True, "Waiting for dependencies"
        
        required_compute = task.resource_requirements.get("compute", 0)
        available_compute = resources.get("compute", 0)
        
        if required_compute > available_compute:
            return True, f"Insufficient compute resources"
        
        return False, ""
    
    def _determine_queue(self, score: float) -> str:
        """Determine queue based on weighted score."""
        if score >= 0.8:
            return "high_priority"
        elif score >= 0.5:
            return "normal"
        else:
            return "low_priority"
