from typing import List, Dict, Any
from datetime import datetime
import structlog
from ..schemas.task_schemas import Task
from ..schemas.scheduling_schemas import SchedulingDecision, SchedulingAlgorithm
from ..utils.config import settings


logger = structlog.get_logger()


class RiskScheduler:
    """Risk-aware scheduling algorithm."""
    
    def __init__(self):
        self.algorithm = SchedulingAlgorithm.RISK_AWARE
        self.max_risk = settings.max_risk_level
    
    async def schedule(
        self,
        task: Task,
        available_resources: Dict[str, Any],
        trace_id: str,
        correlation_id: str
    ) -> SchedulingDecision:
        """Schedule task based on risk assessment."""
        # Calculate risk score
        risk_score = self._calculate_risk_score(task)
        
        # Check if risk is acceptable
        if task.risk_level > self.max_risk:
            return SchedulingDecision(
                task_id=task.task_id,
                algorithm=self.algorithm,
                scheduled=False,
                priority_score=risk_score,
                reason=f"Task risk level {task.risk_level} exceeds maximum {self.max_risk}",
                blocked=True,
                blocked_reason="Risk level too high",
                trace_id=trace_id,
                correlation_id=correlation_id
            )
        
        # Check other blockers
        blocked, blocked_reason = self._check_blockers(task, available_resources)
        
        if blocked:
            return SchedulingDecision(
                task_id=task.task_id,
                algorithm=self.algorithm,
                scheduled=False,
                priority_score=risk_score,
                reason=blocked_reason,
                blocked=True,
                blocked_reason=blocked_reason,
                trace_id=trace_id,
                correlation_id=correlation_id
            )
        
        queue = self._determine_queue(task.risk_level, task.priority)
        
        return SchedulingDecision(
            task_id=task.task_id,
            algorithm=self.algorithm,
            scheduled=True,
            scheduled_at=datetime.utcnow(),
            queue=queue,
            priority_score=risk_score,
            reason=f"Task scheduled with risk score {risk_score:.2f}",
            blocked=False,
            trace_id=trace_id,
            correlation_id=correlation_id
        )
    
    def _calculate_risk_score(self, task: Task) -> float:
        """Calculate risk score (lower risk = higher score)."""
        # Base risk score (inverse of risk level)
        risk_score = 1.0 - task.risk_level
        
        # Adjust for priority (high priority tasks can tolerate more risk)
        priority_adjustment = (task.priority / 10.0) * 0.2
        
        # Adjust for retry count (more retries = lower risk tolerance)
        retry_penalty = task.retry_count * 0.1
        
        final_score = risk_score + priority_adjustment - retry_penalty
        return max(0.0, min(1.0, final_score))
    
    def _check_blockers(self, task: Task, resources: Dict[str, Any]) -> tuple[bool, str]:
        """Check if task is blocked."""
        if task.dependencies:
            return True, "Waiting for dependencies"
        
        required_compute = task.resource_requirements.get("compute", 0)
        available_compute = resources.get("compute", 0)
        
        if required_compute > available_compute:
            return True, f"Insufficient compute resources"
        
        return False, ""
    
    def _determine_queue(self, risk_level: float, priority: int) -> str:
        """Determine queue based on risk and priority."""
        # High priority tasks can go to higher queue even with moderate risk
        if priority >= 8:
            return "high_priority"
        elif risk_level < 0.3 and priority >= 5:
            return "high_priority"
        elif priority >= 5:
            return "normal"
        return "low_priority"
