from typing import Dict, Any
import structlog
from autonomy_events import EventEnvelope, ConsumeResult, TraceParent
from .base import BaseConsumer


logger = structlog.get_logger()


class ResourceConsumer(BaseConsumer):
    """Consumer for resource-related events."""
    
    async def handle_event(
        self,
        envelope: EventEnvelope,
        trace_parent: TraceParent
    ) -> ConsumeResult:
        """Handle resource events."""
        event_type = envelope.event_type
        payload = envelope.payload
        trace_id = trace_parent.trace_context.trace_id if trace_parent else None
        
        try:
            if event_type == "resource.available":
                await self._handle_resource_available(payload, trace_id)
            elif event_type == "resource.exhausted":
                await self._handle_resource_exhausted(payload, trace_id)
            else:
                logger.warning("unknown_resource_event", event_type=event_type)
                return ConsumeResult(
                    success=False,
                    event_id=envelope.event_id,
                    event_type=event_type,
                    error=f"Unknown resource event type: {event_type}"
                )
            
            return ConsumeResult(
                success=True,
                event_id=envelope.event_id,
                event_type=event_type
            )
        
        except Exception as e:
            logger.error("resource_consumer_error", error=str(e))
            return ConsumeResult(
                success=False,
                event_id=envelope.event_id,
                event_type=event_type,
                error=str(e)
            )
    
    async def _handle_resource_available(self, payload: Dict[str, Any], trace_id: str):
        """Handle resource.available event."""
        # Resources are now available, can reschedule blocked tasks
        resource_type = payload.get("resource_type")
        available = payload.get("available", 0)
        
        logger.info("resource_available", resource_type=resource_type, available=available)
    
    async def _handle_resource_exhausted(self, payload: Dict[str, Any], trace_id: str):
        """Handle resource.exhausted event."""
        # Resources exhausted, pause scheduling for resource-intensive tasks
        resource_type = payload.get("resource_type")
        
        logger.info("resource_exhausted", resource_type=resource_type)
