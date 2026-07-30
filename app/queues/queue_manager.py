from typing import Dict, Any, Optional, List
import structlog
from .redis_queue import RedisQueue
from ..schemas.queue_schemas import QueueType, QueueStatus, QueueStats


logger = structlog.get_logger()


class QueueManager:
    """Manages all task queues."""
    
    def __init__(self):
        self._queues: Dict[str, RedisQueue] = {}
        self._initialize_queues()
    
    def _initialize_queues(self):
        """Initialize all queue instances."""
        queue_configs = {
            QueueType.HIGH_PRIORITY: {"max_size": 500},
            QueueType.NORMAL: {"max_size": 1000},
            QueueType.LOW_PRIORITY: {"max_size": 2000},
            QueueType.SCHEDULED: {"max_size": 100},
            QueueType.DEPENDENCY: {"max_size": 500},
            QueueType.RETRY: {"max_size": 200},
            QueueType.DLQ: {"max_size": 1000},
        }
        
        for queue_type, config in queue_configs.items():
            queue_name = f"queue:{queue_type.value}"
            queue = RedisQueue(queue_name)
            queue._max_size = config["max_size"]
            self._queues[queue_type.value] = queue
        
        logger.info("queues_initialized", count=len(self._queues))
    
    async def connect_all(self):
        """Connect all queues to Redis."""
        for queue in self._queues.values():
            await queue.connect()
        logger.info("all_queues_connected")
    
    async def disconnect_all(self):
        """Disconnect all queues from Redis."""
        for queue in self._queues.values():
            await queue.disconnect()
        logger.info("all_queues_disconnected")
    
    def get_queue(self, queue_type: QueueType) -> RedisQueue:
        """Get a specific queue."""
        return self._queues.get(queue_type.value)
    
    async def enqueue(self, queue_type: QueueType, task: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """Enqueue a task to a specific queue."""
        queue = self.get_queue(queue_type)
        if not queue:
            logger.error("queue_not_found", queue_type=queue_type.value)
            return False
        
        return await queue.enqueue(task, ttl)
    
    async def dequeue(self, queue_type: QueueType) -> Optional[Dict[str, Any]]:
        """Dequeue a task from a specific queue."""
        queue = self.get_queue(queue_type)
        if not queue:
            return None
        
        return await queue.dequeue()
    
    async def get_queue_status(self, queue_type: QueueType) -> QueueStatus:
        """Get status of a specific queue."""
        queue = self.get_queue(queue_type)
        if not queue:
            raise ValueError(f"Queue {queue_type.value} not found")
        
        size = await queue.size()
        
        return QueueStatus(
            queue_name=queue.queue_name,
            queue_type=queue_type,
            size=size,
            max_size=queue._max_size
        )
    
    async def get_all_queue_stats(self) -> QueueStats:
        """Get statistics for all queues."""
        total_tasks = 0
        queue_breakdown = {}
        
        for queue_type, queue in self._queues.items():
            size = await queue.size()
            total_tasks += size
            queue_breakdown[queue_type] = size
        
        return QueueStats(
            total_queues=len(self._queues),
            total_tasks=total_tasks,
            queue_breakdown=queue_breakdown,
            throughput={},  # Would need historical tracking
            average_wait_time=0.0,  # Would need historical tracking
            average_processing_time=0.0,  # Would need historical tracking
            error_rate=0.0  # Would need historical tracking
        )
    
    async def requeue(self, queue_type: QueueType, task: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """Requeue a task to a specific queue."""
        queue = self.get_queue(queue_type)
        if not queue:
            return False
        
        return await queue.requeue(task, ttl)
    
    async def remove_task(self, queue_type: QueueType, task_id: str) -> bool:
        """Remove a task from a specific queue."""
        queue = self.get_queue(queue_type)
        if not queue:
            return False
        
        return await queue.remove(task_id)
    
    async def peek_queue(self, queue_type: QueueType, limit: int = 10) -> List[Dict[str, Any]]:
        """Peek at tasks in a specific queue."""
        queue = self.get_queue(queue_type)
        if not queue:
            return []
        
        return await queue.peek(limit)
    
    async def clear_queue(self, queue_type: QueueType):
        """Clear all tasks from a specific queue."""
        queue = self.get_queue(queue_type)
        if queue:
            await queue.clear()
