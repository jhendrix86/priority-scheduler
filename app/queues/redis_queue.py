import json
import structlog
from typing import Optional, Dict, Any, List
from datetime import datetime
import redis.asyncio as aioredis
from ..utils.config import settings


logger = structlog.get_logger()


class RedisQueue:
    """Redis-based queue implementation with backpressure and rate limiting."""
    
    def __init__(
        self,
        queue_name: str,
        host: str = None,
        port: int = None,
        db: int = None,
        password: str = None
    ):
        self.queue_name = queue_name
        self.host = host or settings.redis_host
        self.port = port or settings.redis_port
        self.db = db or settings.redis_db
        self.password = password or settings.redis_password
        self._client: Optional[aioredis.Redis] = None
        self._max_size = 1000  # Maximum queue size for backpressure
    
    async def connect(self):
        """Connect to Redis."""
        self._client = aioredis.Redis(
            host=self.host,
            port=self.port,
            db=self.db,
            password=self.password,
            decode_responses=True
        )
        
        await self._client.ping()
        logger.info("redis_queue_connected", queue_name=self.queue_name)
    
    async def disconnect(self):
        """Disconnect from Redis."""
        if self._client:
            await self._client.close()
        logger.info("redis_queue_disconnected", queue_name=self.queue_name)
    
    async def enqueue(self, task: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """Enqueue a task."""
        ttl = ttl or settings.queue_ttl
        
        # Check backpressure
        queue_size = await self._client.llen(self.queue_name)
        if queue_size >= self._max_size:
            logger.warning("queue_full", queue_name=self.queue_name, size=queue_size)
            return False
        
        # Add to queue
        await self._client.rpush(self.queue_name, json.dumps(task))
        
        # Set TTL for the task
        task_id = task.get("task_id")
        if task_id:
            await self._client.setex(f"task:{task_id}", ttl, json.dumps(task))
        
        logger.info("task_enqueued", queue_name=self.queue_name, task_id=task_id)
        return True
    
    async def dequeue(self) -> Optional[Dict[str, Any]]:
        """Dequeue a task (blocking with timeout)."""
        result = await self._client.blpop(self.queue_name, timeout=5)
        
        if result:
            _, task_json = result
            task = json.loads(task_json)
            logger.info("task_dequeued", queue_name=self.queue_name, task_id=task.get("task_id"))
            return task
        
        return None
    
    async def peek(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Peek at tasks without removing them."""
        tasks = await self._client.lrange(self.queue_name, 0, limit - 1)
        return [json.loads(task) for task in tasks]
    
    async def size(self) -> int:
        """Get queue size."""
        return await self._client.llen(self.queue_name)
    
    async def requeue(self, task: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """Requeue a task (add to front of queue)."""
        ttl = ttl or settings.queue_ttl
        
        # Check backpressure
        queue_size = await self._client.llen(self.queue_name)
        if queue_size >= self._max_size:
            return False
        
        await self._client.lpush(self.queue_name, json.dumps(task))
        
        task_id = task.get("task_id")
        if task_id:
            await self._client.setex(f"task:{task_id}", ttl, json.dumps(task))
        
        logger.info("task_requeued", queue_name=self.queue_name, task_id=task_id)
        return True
    
    async def remove(self, task_id: str) -> bool:
        """Remove a specific task from the queue."""
        # This is expensive in Redis lists, but necessary for cancel operations
        tasks = await self._client.lrange(self.queue_name, 0, -1)
        
        for i, task_json in enumerate(tasks):
            task = json.loads(task_json)
            if task.get("task_id") == task_id:
                await self._client.lrem(self.queue_name, 1, task_json)
                logger.info("task_removed", queue_name=self.queue_name, task_id=task_id)
                return True
        
        return False
    
    async def clear(self):
        """Clear all tasks from the queue."""
        await self._client.delete(self.queue_name)
        logger.info("queue_cleared", queue_name=self.queue_name)
    
    async def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific task by ID."""
        task_json = await self._client.get(f"task:{task_id}")
        if task_json:
            return json.loads(task_json)
        return None
    
    async def __aenter__(self):
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.disconnect()
