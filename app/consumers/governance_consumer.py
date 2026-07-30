from typing import Dict, Any
import structlog
from autonomy_events import EventEnvelope, ConsumeResult, TraceParent
from .base import BaseConsumer


logger = structlog.get_logger()


class GovernanceConsumer(BaseConsumer):
    """Consumer for governance-related events."""
    
    async def handle_event(
        self,
        envelope: EventEnvelope,
        trace_parent: TraceParent
    ) -> ConsumeResult:
        """Handle governance events."""
        event_type = envelope.event_type
        payload = envelope.payload
        trace_id = trace_parent.trace_context.trace_id if trace_parent else None
        
        try:
            if event_type == "governance.approved":
                await self._handle_governance_approved(payload, trace_id)
            elif event_type == "governance.rejected":
                await self._handle_governance_rejected(payload, trace_id)
            elif event_type == "governance.emergency_stop":
                await self._handle_emergency_stop(payload, trace_id)
            else:
                logger.warning("unknown_governance_event", event_type=event_type)
                return ConsumeResult(
                    success=False,
                    event_id=envelope.event_id,
                    event_type=event_type,
                    error=f"Unknown governance event type: {event_type}"
                )
            
            return ConsumeResult(
                success=True,
                event_id=envelope.event_id,
                event_type=event_type
            )
        
        except Exception as e:
            logger.error("governance_consumer_error", error=str(e))
            return ConsumeResult(
                success=False,
                event_id=envelope.event_id,
                event_type=event_type,
                error=str(e)
            )
    
    async def _handle_governance_approved(self, payload: Dict[str, Any], trace_id: str):
        """Handle governance.approved event."""
        task_id = payload.get("task_id")
        if task_id:
            # Task can proceed with scheduling
            logger.info("governance_approved", task_id=task_id)
    
    async def _handle_governance_rejected(self, payload: Dict[str, Any], trace_id: str):
        """Handle governance.rejected event."""
        task_id = payload.get("task_id")
        if task_id:
            # Remove task from queues
            from ..schemas.queue_schemas import QueueType
            for queue_type in QueueType:
                await self.queue_manager.remove_task(queue_type, task_id)
            logger.info("task_removed_governance_rejected", task_id=task_id)
    
    async def _handle_emergency_stop(self, payload: Dict[str, Any], trace_id: str):
        """Handle governance.emergency_stop event."""
        # Pause all scheduling
        logger.info("emergency_stop_received", reason=payload.get("reason"))
