from typing import List, Dict, Any
from datetime import datetime
import structlog
from ..schemas.task_schemas import Task
from ..schemas.scheduling_schemas import SchedulingDecision, SchedulingAlgorithm
from ..utils.config import settings


logger = structlog.get_logger()


class StrategyScheduler:
    """Strategy-aware scheduling algorithm."""
    
    def __init__(self):
        self.algorithm = SchedulingAlgorithm.STRATEGY_AWARE
        self.min_alignment = settings.min_strategy_alignment
    
    async def schedule(
        self,
        task: Task,
        available_resources: Dict[str, Any],
        trace_id: str,
        correlation_id: str
    ) -> SchedulingDecision:
        """Schedule task based on strategy alignment."""
        # Check strategy alignment
        if task.strategy_alignment < self.min_alignment:
            return SchedulingDecision(
                task_id=task.task_id,
                algorithm=self.algorithm,
                scheduled=False,
                priority_score=task.strategy_alignment,
                reason=f"Strategy alignment {task.strategy_alignment} below minimum {self.min_alignment}",
                blocked=True,
                blocked_reason="Insufficient strategy alignment",
                governance_check={"approved": False, "reason": "Strategy alignment too low"},
                trace_id=trace_id,
                correlation_id=correlation_id
            )
        
        # Calculate strategy score
        strategy_score = self._calculate_strategy_score(task)
        
        # Check other blockers
        blocked, blocked_reason = self._check_blockers(task, available_resources)
        
        if blocked:
            return SchedulingDecision(
                task_id=task.task_id,
                algorithm=self.algorithm,
                scheduled=False,
                priority_score=strategy_score,
                reason=blocked_reason,
                blocked=True,
                blocked_reason=blocked_reason,
                governance_check={"approved": False, "reason": blocked_reason},
                trace_id=trace_id,
                correlation_id=correlation_id
            )
        
        queue = self._determine_queue(strategy_score, task.priority)
        
        return SchedulingDecision(
            task_id=task.task_id,
            algorithm=self.algorithm,
            scheduled=True,
            scheduled_at=datetime.utcnow(),
            queue=queue,
            priority_score=strategy_score,
            reason=f"Task scheduled with strategy score {strategy_score:.2f}",
            blocked=False,
            governance_check={"approved": True, "strategy_alignment": task.strategy_alignment},
            trace_id=trace_id,
            correlation_id=correlation_id
        )
    
    def _calculate_strategy_score(self, task: Task) -> float:
        """Calculate strategy alignment score."""
        # Base strategy alignment
        score = task.strategy_alignment
        
        # Boost for high priority tasks
        if task.priority >= 8:
            score += 0.1
        
        # Penalty for low priority tasks
        if task.priority <= 3:
            score -= 0.1
        
        return max(0.0, min(1.0, score))
    
    def _check_blockers(self, task: Task, resources: Dict[str, Any]) -> tuple[bool, str]:
        """Check if task is blocked."""
        if task.dependencies:
            return True, "Waiting for dependencies"
        
        required_compute = task.resource_requirements.get("compute", 0)
        available_compute = resources.get("compute", 0)
        
        if required_compute > available_compute:
            return True, f"Insufficient compute resources"
        
        return False, ""
    
    def _determine_queue(self, strategy_score: float, priority: int) -> str:
        """Determine queue based on strategy score and priority."""
        combined = (strategy_score + priority / 10.0) / 2.0
        
        if combined >= 0.8:
            return "high_priority"
        elif combined >= 0.5:
            return "normal"
        return "low_priority"
