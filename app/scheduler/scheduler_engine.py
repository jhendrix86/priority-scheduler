from typing import Dict, Any, Optional
import structlog
from ..schemas.task_schemas import Task
from ..schemas.scheduling_schemas import SchedulingDecision, SchedulingAlgorithm
from .priority_scheduler import PriorityScheduler
from .weighted_scheduler import WeightedScheduler
from .dependency_scheduler import DependencyScheduler
from .fairness_scheduler import FairnessScheduler
from .resource_scheduler import ResourceScheduler
from .risk_scheduler import RiskScheduler
from .strategy_scheduler import StrategyScheduler
from .temporal_scheduler import TemporalScheduler
from .causal_scheduler import CausalScheduler


logger = structlog.get_logger()


class SchedulerEngine:
    """Main scheduler engine coordinating all scheduling algorithms."""
    
    def __init__(self, default_algorithm: SchedulingAlgorithm = SchedulingAlgorithm.WEIGHTED):
        self.default_algorithm = default_algorithm
        self._schedulers = {
            SchedulingAlgorithm.PRIORITY: PriorityScheduler(),
            SchedulingAlgorithm.WEIGHTED: WeightedScheduler(),
            SchedulingAlgorithm.DEPENDENCY: DependencyScheduler(),
            SchedulingAlgorithm.FAIRNESS: FairnessScheduler(),
            SchedulingAlgorithm.RESOURCE_AWARE: ResourceScheduler(),
            SchedulingAlgorithm.RISK_AWARE: RiskScheduler(),
            SchedulingAlgorithm.STRATEGY_AWARE: StrategyScheduler(),
            SchedulingAlgorithm.TEMPORAL: TemporalScheduler(),
            SchedulingAlgorithm.CAUSAL: CausalScheduler(),
        }
    
    async def schedule(
        self,
        task: Task,
        algorithm: Optional[SchedulingAlgorithm] = None,
        available_resources: Optional[Dict[str, Any]] = None,
        trace_id: str = None,
        correlation_id: str = None
    ) -> SchedulingDecision:
        """Schedule a task using the specified or default algorithm."""
        algorithm = algorithm or self.default_algorithm
        scheduler = self._schedulers.get(algorithm)
        
        if not scheduler:
            logger.error("unknown_algorithm", algorithm=algorithm)
            algorithm = SchedulingAlgorithm.WEIGHTED
            scheduler = self._schedulers[algorithm]
        
        if available_resources is None:
            available_resources = {
                "compute": 100,
                "api": 1000,
                "budget": 10000.0
            }
        
        decision = await scheduler.schedule(
            task=task,
            available_resources=available_resources,
            trace_id=trace_id or "",
            correlation_id=correlation_id or ""
        )
        
        logger.info(
            "task_scheduled",
            task_id=task.task_id,
            algorithm=algorithm.value,
            scheduled=decision.scheduled,
            queue=decision.queue
        )
        
        return decision
    
    def get_scheduler(self, algorithm: SchedulingAlgorithm):
        """Get a specific scheduler instance."""
        return self._schedulers.get(algorithm)
    
    def mark_task_completed(self, task_id: str):
        """Mark a task as completed for dependency tracking."""
        dependency_scheduler = self._schedulers[SchedulingAlgorithm.DEPENDENCY]
        dependency_scheduler.mark_task_completed(task_id)
    
    def add_causal_chain(self, task_id: str, predecessors: list):
        """Add a causal chain for a task."""
        causal_scheduler = self._schedulers[SchedulingAlgorithm.CAUSAL]
        causal_scheduler.add_causal_chain(task_id, predecessors)
    
    def mark_negative_chain(self, task_id: str):
        """Mark a task as triggering a negative causal chain."""
        causal_scheduler = self._schedulers[SchedulingAlgorithm.CAUSAL]
        causal_scheduler.mark_negative_chain(task_id)
