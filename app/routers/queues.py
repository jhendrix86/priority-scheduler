"""
Queue router
"""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.database import get_db
from app.models.queue import Queue, QueueStatus
from app.models.task import Task, TaskStatus
from app.utils.serializers import model_to_dict

router = APIRouter()

_ACTIVE_TASK_STATUSES = (TaskStatus.PENDING, TaskStatus.RUNNING, TaskStatus.RETRYING)


@router.get("/status")
async def get_queue_status(
    db: AsyncSession = Depends(get_db)
):
    """Get queue status"""
    try:
        logger.info("Getting queue status")

        result = await db.execute(select(Queue))
        queues = result.scalars().all()

        queue_list = []
        for queue in queues:
            size_result = await db.execute(
                select(func.count(Task.id)).where(
                    Task.queue_name == queue.name,
                    Task.status.in_(_ACTIVE_TASK_STATUSES),
                )
            )
            current_size = size_result.scalar_one()

            entry = model_to_dict(queue)
            entry["current_size"] = current_size
            queue_list.append(entry)

        return {
            "total": len(queue_list),
            "queues": queue_list
        }

    except Exception as e:
        logger.error(f"Failed to get queue status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{queue_name}/pause")
async def pause_queue(
    queue_name: str,
    db: AsyncSession = Depends(get_db)
):
    """Pause a queue"""
    try:
        logger.info(f"Pausing queue {queue_name}")

        result = await db.execute(select(Queue).where(Queue.name == queue_name))
        queue = result.scalar_one_or_none()
        if queue is None:
            raise HTTPException(status_code=404, detail=f"Queue not found: {queue_name}")

        queue.status = QueueStatus.PAUSED
        await db.commit()
        await db.refresh(queue)

        logger.info(f"Queue paused: {queue_name}")
        return model_to_dict(queue)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to pause queue: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{queue_name}/resume")
async def resume_queue(
    queue_name: str,
    db: AsyncSession = Depends(get_db)
):
    """Resume a queue"""
    try:
        logger.info(f"Resuming queue {queue_name}")

        result = await db.execute(select(Queue).where(Queue.name == queue_name))
        queue = result.scalar_one_or_none()
        if queue is None:
            raise HTTPException(status_code=404, detail=f"Queue not found: {queue_name}")

        queue.status = QueueStatus.ACTIVE
        await db.commit()
        await db.refresh(queue)

        logger.info(f"Queue resumed: {queue_name}")
        return model_to_dict(queue)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to resume queue: {e}")
        raise HTTPException(status_code=500, detail=str(e))
