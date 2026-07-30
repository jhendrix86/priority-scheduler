"""
Task router
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import datetime
from pydantic import BaseModel
from loguru import logger

from app.database import get_db
from app.models.task import Task, TaskStatus, TaskPriority

router = APIRouter()


class CreateTaskRequest(BaseModel):
    """Request to create task"""
    task_type: str
    priority: str = "medium"
    payload: dict
    queue_name: str = "default"
    depends_on: Optional[list] = None


@router.post("/create")
async def create_task(
    request: CreateTaskRequest,
    db: AsyncSession = Depends(get_db)
):
    """Create a new task"""
    try:
        logger.info(f"Creating task: {request.task_type}")
        
        # In production, this would save to database and enqueue
        # For now, return a mock response
        task = {
            "id": "task_123",
            "task_type": request.task_type,
            "priority": request.priority,
            "payload": request.payload,
            "queue_name": request.queue_name,
            "status": "pending",
            "created_at": datetime.utcnow().isoformat()
        }
        
        logger.info(f"Task created: {task['id']}")
        return task
        
    except Exception as e:
        logger.error(f"Failed to create task: {e}")
        raise HTTPException(status_code=500, detail(str(e))


@router.post("/{task_id}/cancel")
async def cancel_task(
    task_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Cancel a task"""
    try:
        logger.info(f"Cancelling task {task_id}")
        
        # In production, this would update database and cancel execution
        # For now, return a mock response
        task = {
            "id": task_id,
            "status": "cancelled",
            "cancelled_at": datetime.utcnow().isoformat()
        }
        
        logger.info(f"Task cancelled: {task_id}")
        return task
        
    except Exception as e:
        logger.error(f"Failed to cancel task: {e}")
        raise HTTPException(status_code=500, detail(str(e))


@router.post("/{task_id}/retry")
async def retry_task(
    task_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Retry a failed task"""
    try:
        logger.info(f"Retrying task {task_id}")
        
        # In production, this would update database and re-enqueue
        # For now, return a mock response
        task = {
            "id": task_id,
            "status": "retrying",
            "retry_count": 1,
            "retried_at": datetime.utcnow().isoformat()
        }
        
        logger.info(f"Task retry initiated: {task_id}")
        return task
        
    except Exception as e:
        logger.error(f"Failed to retry task: {e}")
        raise HTTPException(status_code=500, detail(str(e))


@router.get("/{task_id}")
async def get_task(
    task_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get task details"""
    try:
        logger.info(f"Getting task details for {task_id}")
        
        # In production, this would query from database
        # For now, return a mock response
        task = {
            "id": task_id,
            "task_type": "email_campaign",
            "priority": "high",
            "status": "completed",
            "queue_name": "default",
            "result": {"success": True, "emails_sent": 1000},
            "created_at": datetime.utcnow().isoformat()
        }
        
        return task
        
    except Exception as e:
        logger.error(f"Failed to get task: {e}")
        raise HTTPException(status_code=500, detail(str(e))


@router.get("/")
async def list_tasks(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    queue_name: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    """List tasks"""
    try:
        logger.info("Listing tasks")
        
        # In production, this would query from database with filters
        # For now, return a mock response
        tasks = [
            {
                "id": "task_001",
                "task_type": "email_campaign",
                "priority": "high",
                "status": "completed",
                "created_at": datetime.utcnow().isoformat()
            },
            {
                "id": "task_002",
                "task_type": "report_generation",
                "priority": "medium",
                "status": "running",
                "created_at": (datetime.utcnow() - timedelta(minutes=5)).isoformat()
            }
        ]
        
        return {
            "total": len(tasks),
            "tasks": tasks,
            "filters": {
                "status": status,
                "priority": priority,
                "queue_name": queue_name
            },
            "pagination": {
                "limit": limit,
                "offset": offset
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to list tasks: {e}")
        raise HTTPException(status_code=500, detail(str(e))
