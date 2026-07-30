from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Priority Scheduler Configuration."""
    
    # Service
    service_name: str = "priority-scheduler"
    service_version: str = "1.0.0"
    port: int = 8036
    
    # Redis
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: Optional[str] = None
    
    # PostgreSQL
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_user: str = "postgres"
    postgres_password: str = "password"
    postgres_database: str = "priority_scheduler"
    
    # RabbitMQ
    rabbitmq_url: str = "amqp://localhost:5672"
    rabbitmq_exchange: str = "autonomy.events"
    rabbitmq_exchange_type: str = "topic"
    
    # Scheduling
    max_concurrent_tasks: int = 10
    scheduling_interval: int = 1  # seconds
    default_priority: int = 5
    priority_levels: int = 10
    
    # Queue Settings
    queue_ttl: int = 3600  # seconds
    max_retry_attempts: int = 3
    retry_backoff_base: int = 2  # seconds
    
    # Resource Limits
    max_compute_per_task: int = 100
    max_api_rate_per_task: int = 1000
    max_budget_per_task: float = 1000.0
    
    # Governance
    enforce_governance: bool = True
    require_governance_approval: bool = False
    
    # Strategy
    enforce_strategy_alignment: bool = True
    min_strategy_alignment: float = 0.7
    
    # Risk
    max_risk_level: float = 0.8
    risk_aware_scheduling: bool = True
    
    # Event Consumers
    consumer_prefetch_count: int = 10
    consumer_auto_ack: bool = False
    dlq_enabled: bool = True
    
    # OpenTelemetry
    otel_enabled: bool = True
    otel_endpoint: str = "http://localhost:4318"
    otel_service_name: str = "priority-scheduler"
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "json"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


settings = Settings()
