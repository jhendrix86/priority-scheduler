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
    lifespan=lifespan,
    # SECURITY_REVIEW.md finding: /docs, /redoc, /openapi.json were reachable
    # unauthenticated on every engine (dynamic-pentest-confirmed) - a full
    # interactive API browser plus every unauth write path. Disabled unless
    # DEBUG=true.
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    openapi_url="/openapi.json" if settings.debug else None,
)

# Configure CORS
def _cors_allowed_origins() -> list:
    # SECURITY_REVIEW.md #1 - no wildcard with credentials. Set
    # ALLOWED_ORIGINS (comma-separated) when a browser client exists.
    import os
    return [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "").split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_allowed_origins(),
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
        port=8046,
        reload=True
    )
