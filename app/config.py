"""
Configuration management for Priority Scheduler
"""

from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings"""
    
    # Database
    database_url: str = os.getenv("DATABASE_URL", "postgresql://localhost/scheduler")
    
    # Redis
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # RabbitMQ
    rabbitmq_url: str = os.getenv("RABBITMQ_URL", "amqp://localhost:5672")
    
    # Workers
    worker_count: int = int(os.getenv("WORKER_COUNT", "4"))
    max_retries: int = int(os.getenv("MAX_RETRIES", "3"))
    
    # Queues
    default_queue: str = os.getenv("DEFAULT_QUEUE", "default")
    critical_queue: str = os.getenv("CRITICAL_QUEUE", "critical")
    
    # Task Timeout
    task_timeout_seconds: int = int(os.getenv("TASK_TIMEOUT_SECONDS", "300"))
    
    # Application
    app_name: str = "Priority Scheduler"
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    # Integration
    global_state_manager_url: str = os.getenv("GLOBAL_STATE_MANAGER_URL", "http://localhost:8035")
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
