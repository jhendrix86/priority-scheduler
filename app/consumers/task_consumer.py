from typing import Dict, Any
from datetime import datetime
import structlog
import uuid
from autonomy_events import EventEnvelope, ConsumeResult, TraceParent
from .base import BaseConsumer
from ..schemas.task_schemas import Task, TaskStatus
from ..schemas.queue_schemas import QueueType


logger = structlog.get_logger()


class TaskConsumer(BaseConsumer):
    """Consumer for task-related events."""
    
    async def handle_event(
        self,
        envelope: EventEnvelope,
        trace_parent: TraceParent
    ) -> ConsumeResult:
        """Handle task events."""
        event_type = envelope.event_type
        payload = envelope.payload
        trace_id = trace_parent.trace_context.trace_id if trace_parent else None
        
        try:
            if event_type == "task.submitted":
                await self._handle_task_submitted(payload, trace_id)
            elif event_type == "task.completed":
                await self._handle_task_completed(payload, trace_id)
            elif event_type == "task.failed":
                await self._handle_task_failed(payload, trace_id)
            elif event_type == "task.cancelled":
                await self._handle_task_cancelled(payload, trace_id)
            else:
                logger.warning("unknown_task_event", event_type=event_type)
                return ConsumeResult(
                    success=False,
                    event_id=envelope.event_id,
                    event_type=event_type,
                    error=f"Unknown task event type: {event_type}"
                )
            
            return ConsumeResult(
                success=True,
                event_id=envelope.event_id,
                event_type=event_type
            )
        
        except Exception as e:
            logger.error("task_consumer_error", error=str(e))
            return ConsumeResult(
                success=False,
                event_id=envelope.event_id,
                event_type=event_type,
                error=str(e)
            )
    
    async def _handle_task_submitted(self, payload: Dict[str, Any], trace_id: str):
        """Handle task.submitted event."""
        task_id = payload.get("task_id") or str(uuid.uuid4())
        
        # Create task object
        task = Task(
            task_id=task_id,
            task_type=payload["task_type"],
            priority=payload.get("priority", 5),
            dependencies=payload.get("dependencies", []),
            constraints=payload.get("constraints", {}),
            resource_requirements=payload.get("resource_requirements", {}),
            risk_level=payload.get("risk_level", 0.0),
            strategy_alignment=payload.get("strategy_alignment", 1.0),
            owner_engine=payload["owner_engine"],
            retry_policy=payload.get("retry_policy", {}),
            timeout_policy=payload.get("timeout_policy", {}),
            metadata=payload.get("metadata", {})
        )
        
        # Schedule the task
        decision = await self.scheduler.schedule(
            task=task,
            trace_id=trace_id,
            correlation_id=envelope.correlation_id or trace_id
        )
        
        # Enqueue to appropriate queue
        if decision.scheduled and decision.queue:
            from ..schemas.queue_schemas import QueueType
            queue_type = QueueType(decision.queue)
            # mode="json": redis_queue.enqueue json.dumps()es this dict; a
            # bare .dict() keeps datetime objects and the dump raises.
            await self.queue_manager.enqueue(queue_type, task.model_dump(mode="json"))
        
        logger.info("task_submitted_handled", task_id=task_id, scheduled=decision.scheduled)
    
    async def _handle_task_completed(self, payload: Dict[str, Any], trace_id: str):
        """Handle task.completed event."""
        task_id = payload["task_id"]
        
        # Mark task as completed in scheduler
        self.scheduler.mark_task_completed(task_id)
        
        logger.info("task_completed_handled", task_id=task_id)
    
    async def _handle_task_failed(self, payload: Dict[str, Any], trace_id: str):
        """Handle task.failed event."""
        task_id = payload["task_id"]
        retry_count = payload.get("retry_count", 0)
        max_retries = payload.get("max_retries", 3)
        
        if retry_count < max_retries:
            # Requeue to retry queue
            task = Task(
                task_id=task_id,
                task_type=payload.get("task_type", "unknown"),
                priority=payload.get("priority", 5),
                retry_count=retry_count + 1,
                lifecycle_stage=TaskStatus.RETRYING,
                error_message=payload.get("error_message")
            )
            
            await self.queue_manager.enqueue(QueueType.RETRY, task.model_dump(mode="json"))
            logger.info("task_requeued", task_id=task_id, retry_count=retry_count + 1)
        else:
            # Send to DLQ
            await self.queue_manager.enqueue(QueueType.DLQ, payload)
            logger.info("task_sent_to_dlq", task_id=task_id)
    
    async def _handle_task_cancelled(self, payload: Dict[str, Any], trace_id: str):
        """Handle task.cancelled event."""
        task_id = payload["task_id"]
        
        # Remove task from all queues
        for queue_type in QueueType:
            await self.queue_manager.remove_task(queue_type, task_id)
        
        logger.info("task_cancelled_handled", task_id=task_id)
