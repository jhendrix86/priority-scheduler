"""
Job router
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import datetime
from pydantic import BaseModel
from loguru import logger

from app.database import get_db

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
        
        # In production, this would save to database and schedule with cron
        # For now, return a mock response
        job = {
            "id": "job_123",
            "name": request.name,
            "job_type": request.job_type,
            "cron_expression": request.cron_expression,
            "timezone": request.timezone,
            "payload": request.payload,
            "status": "active",
            "next_run_at": datetime.utcnow().isoformat(),
            "created_at": datetime.utcnow().isoformat()
        }
        
        logger.info(f"Job scheduled: {job['id']}")
        return job
        
    except Exception as e:
        logger.error(f"Failed to schedule job: {e}")
        raise HTTPException(status_code=500, detail(str(e))


@router.post("/{job_id}/unschedule")
async def unschedule_job(
    job_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Unschedule a job"""
    try:
        logger.info(f"Unscheduling job {job_id}")
        
        # In production, this would update database and remove from cron
        # For now, return a mock response
        job = {
            "id": job_id,
            "status": "cancelled",
            "unscheduled_at": datetime.utcnow().isoformat()
        }
        
        logger.info(f"Job unscheduled: {job_id}")
        return job
        
    except Exception as e:
        logger.error(f"Failed to unschedule job: {e}")
        raise HTTPException(status_code=500, detail(str(e))


@router.get("/{job_id}")
async def get_job(
    job_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get job details"""
    try:
        logger.info(f"Getting job details for {job_id}")
        
        # In production, this would query from database
        # For now, return a mock response
        job = {
            "id": job_id,
            "name": "Daily Report",
            "job_type": "report_generation",
            "cron_expression": "0 9 * * *",
            "status": "active",
            "last_run_at": (datetime.utcnow() - timedelta(days=1)).isoformat(),
            "next_run_at": (datetime.utcnow() + timedelta(days=1)).isoformat(),
            "run_count": 30
        }
        
        return job
        
    except Exception as e:
        logger.error(f"Failed to get job: {e}")
        raise HTTPException(status_code=500, detail(str(e))


@router.get("/")
async def list_jobs(
    status: Optional[str] = None,
    job_type: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    """List jobs"""
    try:
        logger.info("Listing jobs")
        
        # In production, this would query from database with filters
        # For now, return a mock response
        jobs = [
            {
                "id": "job_001",
                "name": "Daily Report",
                "job_type": "report_generation",
                "status": "active",
                "cron_expression": "0 9 * * *"
            },
            {
                "id": "job_002",
                "name": "Weekly Cleanup",
                "job_type": "maintenance",
                "status": "active",
                "cron_expression": "0 2 * * 0"
            }
        ]
        
        return {
            "total": len(jobs),
            "jobs": jobs,
            "filters": {
                "status": status,
                "job_type": job_type
            },
            "pagination": {
                "limit": limit,
                "offset": offset
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to list jobs: {e}")
        raise HTTPException(status_code=500, detail(str(e))
