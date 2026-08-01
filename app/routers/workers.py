"""
Worker router
"""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.database import get_db
from app.models.worker import Worker, WorkerStatus
from app.utils.serializers import model_to_dict

router = APIRouter()


@router.get("/status")
async def get_worker_status(
    db: AsyncSession = Depends(get_db)
):
    """Get worker status"""
    try:
        logger.info("Getting worker status")

        result = await db.execute(select(Worker))
        workers = result.scalars().all()

        return {
            "total": len(workers),
            "workers": [model_to_dict(w) for w in workers]
        }

    except Exception as e:
        logger.error(f"Failed to get worker status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/scale")
async def scale_workers(
    target_count: int,
    db: AsyncSession = Depends(get_db)
):
    """Scale the worker pool up or down to target_count active workers"""
    try:
        logger.info(f"Scaling workers to {target_count}")

        if target_count < 0:
            raise HTTPException(status_code=400, detail="target_count cannot be negative")

        active_result = await db.execute(
            select(Worker).where(Worker.status != WorkerStatus.OFFLINE)
        )
        active_workers = active_result.scalars().all()
        current_count = len(active_workers)

        if target_count > current_count:
            next_index_result = await db.execute(select(func.count(Worker.id)))
            next_index = next_index_result.scalar_one() + 1
            for i in range(target_count - current_count):
                worker = Worker(
                    name=f"Worker-{next_index + i}",
                    worker_type="general",
                    status=WorkerStatus.IDLE,
                )
                db.add(worker)

        elif target_count < current_count:
            # Prefer retiring idle workers first, leave busy ones running
            to_retire = sorted(active_workers, key=lambda w: w.status != WorkerStatus.IDLE)
            for worker in to_retire[: current_count - target_count]:
                worker.status = WorkerStatus.OFFLINE

        await db.commit()

        logger.info(f"Workers scaled to {target_count}")
        return {
            "previous_count": current_count,
            "target_count": target_count,
            "scaling": target_count > current_count,
            "scaled_at": datetime.utcnow().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to scale workers: {e}")
        raise HTTPException(status_code=500, detail=str(e))
