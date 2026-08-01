"""
Priority Scheduler - Main Application
Task scheduling and priority management system for the Autonomous Company OS
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from loguru import logger
from datetime import datetime
import os

from app.config import settings
from app.database import init_db
from app.scheduler.scheduler_engine import SchedulerEngine
from app.routers import tasks, jobs, queues, workers


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info("Starting Priority Scheduler...")

    # Initialize database
    await init_db()

    # Single shared scheduler engine instance for the app's lifetime
    app.state.scheduler_engine = SchedulerEngine()

    logger.info("Priority Scheduler started successfully")
    yield

    logger.info("Shutting down Priority Scheduler...")


# Create FastAPI application
app = FastAPI(
    title="Priority Scheduler",
    description="Task scheduling and priority management system for the Autonomous Company OS",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
app.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
app.include_router(queues.router, prefix="/queues", tags=["queues"])
app.include_router(workers.router, prefix="/workers", tags=["workers"])


@app.get("/")
async def root():
    """Root endpoint with service information"""
    return {
        "service": "Priority Scheduler",
        "version": "1.0.0",
        "status": "operational",
        "description": "Task scheduling and priority management system",
        "features": [
            "Task queuing",
            "Priority-based execution",
            "Resource allocation",
            "Job scheduling",
            "Dependency management",
            "Retry logic",
            "Dead letter queue",
            "Monitoring"
        ],
        "endpoints": {
            "tasks": "/tasks",
            "jobs": "/jobs",
            "queues": "/queues",
            "workers": "/workers"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    logger.info("Health check performed")
    return {
        "status": "healthy",
        "service": "priority-scheduler",
        "timestamp": datetime.utcnow().isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8034,
        reload=True
    )
