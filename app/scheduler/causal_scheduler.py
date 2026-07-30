from typing import List, Dict, Any
from datetime import datetime
import structlog
from ..schemas.task_schemas import Task
from ..schemas.scheduling_schemas import SchedulingDecision, SchedulingAlgorithm


logger = structlog.get_logger()


class CausalScheduler:
    """Causal scheduling algorithm considering causal relationships."""
    
    def __init__(self):
        self.algorithm = SchedulingAlgorithm.CAUSAL
        self._causal_chains: Dict[str, List[str]] = {}  # task_id -> [causal_predecessors]
        self._negative_chains: set = set()  # Tasks that trigger negative causal chains
    
    async def schedule(
        self,
        task: Task,
        available_resources: Dict[str, Any],
        trace_id: str,
        correlation_id: str
    ) -> SchedulingDecision:
        """Schedule task based on causal relationships."""
        # Check for negative causal chains
        if task.task_id in self._negative_chains:
            return SchedulingDecision(
                task_id=task.task_id,
                algorithm=self.algorithm,
                scheduled=False,
                priority_score=0.0,
                reason="Task triggers negative causal chain",
                blocked=True,
                blocked_reason="Negative causal chain detected",
                trace_id=trace_id,
                correlation_id=correlation_id
            )
        
        # Check causal dependencies
        blocked, blocked_reason = self._check_causal_dependencies(task)
        
        if blocked:
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
        
        # Calculate causal score
        causal_score = self._calculate_causal_score(task)
        
        # Check other blockers
        resource_blocked, resource_reason = self._check_resources(task, available_resources)
        
        if resource_blocked:
            return SchedulingDecision(
                task_id=task.task_id,
                algorithm=self.algorithm,
                scheduled=False,
                priority_score=causal_score,
                reason=resource_reason,
                blocked=True,
                blocked_reason=resource_reason,
                trace_id=trace_id,
                correlation_id=correlation_id
            )
        
        queue = self._determine_queue(causal_score, task.priority)
        
        return SchedulingDecision(
            task_id=task.task_id,
            algorithm=self.algorithm,
            scheduled=True,
            scheduled_at=datetime.utcnow(),
            queue=queue,
            priority_score=causal_score,
            reason=f"Task scheduled with causal score {causal_score:.2f}",
            blocked=False,
            trace_id=trace_id,
            correlation_id=correlation_id
        )
    
    def add_causal_chain(self, task_id: str, predecessors: List[str]):
        """Add a causal chain for a task."""
        self._causal_chains[task_id] = predecessors
    
    def mark_negative_chain(self, task_id: str):
        """Mark a task as triggering a negative causal chain."""
        self._negative_chains.add(task_id)
    
    def _check_causal_dependencies(self, task: Task) -> tuple[bool, str]:
        """Check if causal dependencies are satisfied."""
        # Check explicit dependencies
        if task.dependencies:
            unsatisfied = [dep for dep in task.dependencies if dep in self._causal_chains]
            if unsatisfied:
                return True, f"Waiting for causal dependencies: {', '.join(unsatisfied)}"
        
        # Check if task is in a causal chain
        if task.task_id in self._causal_chains:
            predecessors = self._causal_chains[task.task_id]
            # In a real implementation, we'd check if predecessors completed
            # For now, assume they're not blocking
            pass
        
        return False, ""
    
    def _calculate_causal_score(self, task: Task) -> float:
        """Calculate causal score."""
        # Base priority
        score = task.priority / 10.0
        
        # Boost for tasks that are causal predecessors
        is_predecessor = any(task.task_id in chain for chain in self._causal_chains.values())
        if is_predecessor:
            score += 0.2
        
        # Penalty for tasks with many causal dependencies
        if len(task.dependencies) > 5:
            score -= 0.1
        
        return max(0.0, min(1.0, score))
    
    def _check_resources(self, task: Task, resources: Dict[str, Any]) -> tuple[bool, str]:
        """Check resource availability."""
        required_compute = task.resource_requirements.get("compute", 0)
        available_compute = resources.get("compute", 0)
        
        if required_compute > available_compute:
            return True, f"Insufficient compute resources"
        
        return False, ""
    
    def _determine_queue(self, causal_score: float, priority: int) -> str:
        """Determine queue based on causal score and priority."""
        combined = (causal_score + priority / 10.0) / 2.0
        
        if combined >= 0.7:
            return "high_priority"
        elif combined >= 0.4:
            return "normal"
        return "low_priority"
