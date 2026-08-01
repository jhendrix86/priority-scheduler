"""
Job router
"""

import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from loguru import logger

from app.database import get_db
from app.models.job import Job, JobStatus
from app.utils.serializers import model_to_dict

router = APIRouter()


class ScheduleJobRequest(BaseModel):
    """Request to schedule job"""
    name: str
    job_type: str
    cron_expression: str
    payload: dict
    timezone: str = "UTC"


@router.post("/schedule")
async def schedule_job(
    request: ScheduleJobRequest,
    db: AsyncSession = Depends(get_db)
):
    """Schedule a recurring job"""
    try:
        logger.info(f"Scheduling job: {request.name}")

        job = Job(
            name=request.name,
            job_type=request.job_type,
            cron_expression=request.cron_expression,
            timezone=request.timezone,
            payload=request.payload,
            status=JobStatus.ACTIVE,
        )

        db.add(job)
        await db.commit()
        await db.refresh(job)

        logger.info(f"Job scheduled: {job.id}")
        return model_to_dict(job)

    except Exception as e:
        logger.error(f"Failed to schedule job: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{job_id}/unschedule")
async def unschedule_job(
    job_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Unschedule a job"""
    try:
        logger.info(f"Unscheduling job {job_id}")

        job = await db.get(Job, uuid.UUID(job_id))
        if job is None:
            raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")

        job.status = JobStatus.CANCELLED
        await db.commit()
        await db.refresh(job)

        logger.info(f"Job unscheduled: {job_id}")
        return model_to_dict(job)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to unschedule job: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{job_id}")
async def get_job(
    job_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get job details"""
    try:
        logger.info(f"Getting job details for {job_id}")

        job = await db.get(Job, uuid.UUID(job_id))
        if job is None:
            raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")

        return model_to_dict(job)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get job: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/")
async def list_jobs(
    status: Optional[JobStatus] = None,
    job_type: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    """List jobs"""
    try:
        logger.info("Listing jobs")

        query = select(Job)
        if status is not None:
            query = query.where(Job.status == status)
        if job_type is not None:
            query = query.where(Job.job_type == job_type)

        count_result = await db.execute(query)
        total = len(count_result.scalars().all())

        query = query.order_by(Job.created_at.desc()).limit(limit).offset(offset)
        result = await db.execute(query)
        jobs = [model_to_dict(j) for j in result.scalars().all()]

        return {
            "total": total,
            "jobs": jobs,
            "filters": {
                "status": status.value if status else None,
                "job_type": job_type
            },
            "pagination": {
                "limit": limit,
                "offset": offset
            }
        }

    except Exception as e:
        logger.error(f"Failed to list jobs: {e}")
        raise HTTPException(status_code=500, detail=str(e))
