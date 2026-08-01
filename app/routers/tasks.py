"""
Task router
"""

import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
from loguru import logger

from app.database import get_db
from app.models.task import Task, TaskStatus, TaskPriority
from app.models.queue import Queue, QueueStatus as DbQueueStatus
from app.scheduler.scheduler_engine import SchedulerEngine
from app.schemas.task_schemas import Task as SchedulerTaskSchema
from app.utils.serializers import model_to_dict

router = APIRouter()

# Maps the API's human priority levels onto the 1-10 scale the scheduling
# algorithms actually operate on (higher = more urgent).
_PRIORITY_TO_SCORE = {
    TaskPriority.CRITICAL: 10,
    TaskPriority.HIGH: 8,
    TaskPriority.MEDIUM: 5,
    TaskPriority.LOW: 3,
    TaskPriority.BACKGROUND: 1,
}


def get_scheduler_engine(request: Request) -> SchedulerEngine:
    return request.app.state.scheduler_engine


class CreateTaskRequest(BaseModel):
    """Request to create task"""
    task_type: str
    priority: TaskPriority = TaskPriority.MEDIUM
    payload: dict
    queue_name: str = "default"
    depends_on: Optional[List[str]] = None
    owner_engine: str = "priority-scheduler"
    constraints: Dict[str, Any] = Field(default_factory=dict)
    resource_requirements: Dict[str, Any] = Field(default_factory=dict)
    risk_level: float = Field(default=0.0, ge=0.0, le=1.0)
    strategy_alignment: float = Field(default=1.0, ge=0.0, le=1.0)
    trace_id: Optional[str] = None
    correlation_id: Optional[str] = None


async def _get_or_create_queue(db: AsyncSession, name: str) -> Queue:
    result = await db.execute(select(Queue).where(Queue.name == name))
    queue = result.scalar_one_or_none()
    if queue is None:
        queue = Queue(name=name, status=DbQueueStatus.ACTIVE)
        db.add(queue)
        await db.flush()
    return queue


@router.post("/create")
async def create_task(
    request: CreateTaskRequest,
    db: AsyncSession = Depends(get_db),
    scheduler: SchedulerEngine = Depends(get_scheduler_engine)
):
    """Create a new task, run it through the scheduler, and persist it"""
    try:
        logger.info(f"Creating task: {request.task_type}")

        task_id = str(uuid.uuid4())

        scheduler_task = SchedulerTaskSchema(
            task_id=task_id,
            task_type=request.task_type,
            priority=_PRIORITY_TO_SCORE[request.priority],
            dependencies=request.depends_on or [],
            constraints=request.constraints,
            resource_requirements=request.resource_requirements,
            risk_level=request.risk_level,
            strategy_alignment=request.strategy_alignment,
            owner_engine=request.owner_engine,
            metadata=request.payload,
        )

        decision = await scheduler.schedule(
            task=scheduler_task,
            trace_id=request.trace_id,
            correlation_id=request.correlation_id,
        )

        queue_name = decision.queue or request.queue_name
        await _get_or_create_queue(db, queue_name)

        task = Task(
            id=uuid.UUID(task_id),
            task_type=request.task_type,
            priority=request.priority,
            payload=request.payload,
            status=TaskStatus.PENDING,
            queue_name=queue_name,
            depends_on=request.depends_on,
            extra_metadata={
                "scheduling_decision": decision.model_dump(mode="json"),
                "constraints": request.constraints,
                "resource_requirements": request.resource_requirements,
                "risk_level": request.risk_level,
                "strategy_alignment": request.strategy_alignment,
                "owner_engine": request.owner_engine,
            },
        )

        db.add(task)
        await db.commit()
        await db.refresh(task)

        logger.info(f"Task created: {task.id}")

        result = model_to_dict(task)
        result["scheduling_decision"] = decision.model_dump(mode="json")
        return result

    except Exception as e:
        logger.error(f"Failed to create task: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{task_id}/cancel")
async def cancel_task(
    task_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Cancel a task"""
    try:
        logger.info(f"Cancelling task {task_id}")

        task = await db.get(Task, uuid.UUID(task_id))
        if task is None:
            raise HTTPException(status_code=404, detail=f"Task not found: {task_id}")

        task.status = TaskStatus.CANCELLED
        task.completed_at = datetime.utcnow()
        await db.commit()
        await db.refresh(task)

        logger.info(f"Task cancelled: {task_id}")
        return model_to_dict(task)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel task: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{task_id}/retry")
async def retry_task(
    task_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Retry a failed task"""
    try:
        logger.info(f"Retrying task {task_id}")

        task = await db.get(Task, uuid.UUID(task_id))
        if task is None:
            raise HTTPException(status_code=404, detail=f"Task not found: {task_id}")

        if task.retry_count >= task.max_retries:
            raise HTTPException(
                status_code=400,
                detail=f"Task {task_id} has exceeded its max retries ({task.max_retries})"
            )

        task.retry_count += 1
        task.status = TaskStatus.RETRYING
        task.error_message = None
        await db.commit()
        await db.refresh(task)

        logger.info(f"Task retry initiated: {task_id}")
        return model_to_dict(task)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retry task: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{task_id}")
async def get_task(
    task_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get task details"""
    try:
        logger.info(f"Getting task details for {task_id}")

        task = await db.get(Task, uuid.UUID(task_id))
        if task is None:
            raise HTTPException(status_code=404, detail=f"Task not found: {task_id}")

        return model_to_dict(task)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get task: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/")
async def list_tasks(
    status: Optional[TaskStatus] = None,
    priority: Optional[TaskPriority] = None,
    queue_name: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    """List tasks"""
    try:
        logger.info("Listing tasks")

        query = select(Task)
        if status is not None:
            query = query.where(Task.status == status)
        if priority is not None:
            query = query.where(Task.priority == priority)
        if queue_name is not None:
            query = query.where(Task.queue_name == queue_name)

        count_result = await db.execute(query)
        total = len(count_result.scalars().all())

        query = query.order_by(Task.created_at.desc()).limit(limit).offset(offset)
        result = await db.execute(query)
        tasks = [model_to_dict(t) for t in result.scalars().all()]

        return {
            "total": total,
            "tasks": tasks,
            "filters": {
                "status": status.value if status else None,
                "priority": priority.value if priority else None,
                "queue_name": queue_name
            },
            "pagination": {
                "limit": limit,
                "offset": offset
            }
        }

    except Exception as e:
        logger.error(f"Failed to list tasks: {e}")
        raise HTTPException(status_code=500, detail=str(e))
