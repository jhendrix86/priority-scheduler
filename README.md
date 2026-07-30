# Priority Scheduler

Task scheduling and priority management system for the Autonomous Company OS. This engine handles task queuing, priority-based execution, resource allocation, and job scheduling.

## Features

- **Task Queuing** - Centralized task queue management
- **Priority-Based Execution** - Execute tasks based on priority
- **Resource Allocation** - Allocate resources based on task requirements
- **Job Scheduling** - Schedule recurring and one-time jobs
- **Dependency Management** - Handle task dependencies
- **Retry Logic** - Automatic retry for failed tasks
- **Dead Letter Queue** - Handle failed tasks
- **Monitoring** - Task execution monitoring

## Architecture

```
┌─────────────┐    Tasks     ┌──────────────┐
│   All       │ ────────────> │  Task        │
│  Engines    │               │  Ingestion   │
└─────────────┘               └──────┬───────┘
                                     │
                    ┌────────────────┼────────────────┐
                    │                │                │
            ┌───────▼──────┐ ┌────▼────┐ ┌────▼──────┐
            │   Priority   │ │ Resource│ │ Dependency│
            │   Engine     │ │ Manager │ │  Manager   │
            └──────────────┘ └─────────┘ └───────────┘
                    │                │                │
                    └────────────────┼────────────────┘
                                     │
                    ┌────────────────▼────────────────┐
                    │      Task Executor             │
                    │  (Worker pool, execution)       │
                    └─────────────────────────────────┘
                                     │
                    ┌────────────────┼────────────────┐
                    │                │                │
            ┌───────▼──────┐ ┌────▼────┐ ┌────▼──────┐
            │   Retry      │ │ Dead    │ │ Monitor   │
            │   Logic      │ │ Letter  │ │  Engine    │
            └──────────────┘ └─────────┘ └───────────┘
```

## Installation

### Prerequisites

- Python 3.9+
- PostgreSQL (for task data)
- Redis (for queuing and caching)
- RabbitMQ (for message queue)

### Local Development

```bash
# Clone repository
git clone https://github.com/autonomous-company/priority-scheduler.git
cd priority-scheduler

# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp .env.example .env
# Edit .env with your configuration

# Run the service
uvicorn app.main:app --reload --port 8034
```

### Docker Deployment

```bash
# Build and start all services
cd docker
docker-compose up -d

# View logs
docker-compose logs -f priority-scheduler

# Stop services
docker-compose down
```

## Configuration

Configuration is managed via environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql://localhost/scheduler` | PostgreSQL connection URL |
| `REDIS_URL` | `redis://localhost:6379` | Redis connection URL |
| `RABBITMQ_URL` | `amqp://localhost:5672` | RabbitMQ connection URL |
| `WORKER_COUNT` | `4` | Number of worker processes |
| `MAX_RETRIES` | `3` | Maximum retry attempts |

## API Endpoints

### Health & Info
- `GET /health` - Health check
- `GET /` - Service information

### Task Management
- `POST /tasks/create` - Create task
- `POST /tasks/{task_id}/cancel` - Cancel task
- `GET /tasks/{task_id}` - Get task details
- `GET /tasks` - List tasks
- `POST /tasks/{task_id}/retry` - Retry failed task

### Job Scheduling
- `POST /jobs/schedule` - Schedule job
- `POST /jobs/{job_id}/unschedule` - Unschedule job
- `GET /jobs/{job_id}` - Get job details
- `GET /jobs` - List jobs

### Queue Management
- `GET /queues/status` - Get queue status
- `POST /queues/{queue_name}/pause` - Pause queue
- `POST /queues/{queue_name}/resume` - Resume queue

### Workers
- `GET /workers/status` - Get worker status
- `POST /workers/scale` - Scale workers

## Usage Examples

### Create Task

```python
import httpx

async def create_task():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8034/tasks/create",
            json={
                "task_type": "email_campaign",
                "priority": "high",
                "payload": {
                    "campaign_id": "camp_123",
                    "recipient_count": 1000
                }
            }
        )
        return response.json()
```

### Schedule Job

```python
async def schedule_job():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8034/jobs/schedule",
            json={
                "job_type": "daily_report",
                "schedule": "0 9 * * *",  # Cron expression
                "payload": {
                    "report_type": "daily"
                }
            }
        )
        return response.json()
```

## Task Priorities

- **Critical** - Immediate execution, highest priority
- **High** - Execute within 5 minutes
- **Medium** - Execute within 30 minutes
- **Low** - Execute within 2 hours
- **Background** - Execute when resources available

## Integration with Other Engines

### All Engines
- Submit tasks for asynchronous processing
- Receive task completion notifications
- Monitor task execution status

### Global State Manager
- Store task state
- Track task progress
- Update system state on task completion

## Monitoring

### Metrics
- Task queue length
- Task execution time
- Task success rate
- Worker utilization
- Retry rate
- Dead letter queue size

## License

MIT License

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request
