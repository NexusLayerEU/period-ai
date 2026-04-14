# 06 — Scheduler & Task Queue

## Architecture

```
┌─────────────────┐     ┌──────────────┐     ┌─────────────────────┐
│  Celery Beat    │────►│  Redis Queue │────►│  Celery Workers     │
│  (scheduler)    │     │  (broker)    │     │  (pipeline runner)  │
└─────────────────┘     └──────────────┘     └─────────────────────┘
        │                                              │
        │ reads schedule from DB                       │ writes results to DB
        ▼                                              ▼
┌─────────────────┐                         ┌──────────────────────┐
│   PostgreSQL    │                         │  PostgreSQL           │
│  (templates)    │                         │  (runs, deliveries)   │
└─────────────────┘                         └──────────────────────┘
```

**Key design decision:** Celery Beat does NOT use a static `beat_schedule` dict. Instead, it uses `celery-redbeat` or a custom `DatabaseScheduler` that reads active `ReportTemplate` schedules from PostgreSQL every 30 seconds and dynamically registers/unregisters periodic tasks.

---

## Celery App Factory

```python
# app/scheduler/celery_app.py
from celery import Celery
from app.config import settings

celery_app = Celery(
    "periodai",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.scheduler.tasks"]
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_acks_late=True,         # ack after task completes, not before
    worker_prefetch_multiplier=1, # one task at a time per worker
    task_reject_on_worker_lost=True,
    result_expires=86400,        # results kept 24h in Redis
)
```

---

## Celery Tasks

```python
# app/scheduler/tasks.py
from app.scheduler.celery_app import celery_app
from app.pipeline.runner import PipelineRunner

@celery_app.task(
    bind=True,
    max_retries=2,
    default_retry_delay=60,
    name="periodai.run_report"
)
def run_report_task(self, template_id: str, triggered_by: str = "schedule"):
    """
    Main report generation task.
    Creates a ReportRun record and executes the full pipeline.
    """
    import asyncio
    from app.database import get_sync_session
    from app.services.run_service import RunService

    try:
        # Run async pipeline in sync Celery task
        asyncio.run(_run_pipeline(template_id, triggered_by))
    except Exception as exc:
        raise self.retry(exc=exc)


async def _run_pipeline(template_id: str, triggered_by: str):
    async with get_async_session() as session:
        template = await session.get(ReportTemplate, template_id)
        if not template or not template.is_active:
            return  # Template deleted or deactivated between scheduling and execution

        # Create run record
        run = ReportRun(
            template_id=template.id,
            workspace_id=template.workspace_id,
            triggered_by=triggered_by,
            status="queued"
        )
        session.add(run)
        await session.commit()

        # Execute pipeline
        runner = PipelineRunner(session)
        await runner.execute(run.id, template)
```

---

## Dynamic Scheduler

Use `celery-redbeat` for dynamic schedule management stored in Redis.

```bash
pip install celery-redbeat
```

```python
# celery_app.conf
celery_app.conf.beat_scheduler = "redbeat.RedBeatScheduler"
celery_app.conf.redbeat_redis_url = settings.REDIS_URL
celery_app.conf.beat_max_loop_interval = 30  # check every 30s
```

### Registering a Template Schedule

When a template is created or updated, register its schedule in RedBeat:

```python
# app/services/template_service.py
from redbeat import RedBeatSchedulerEntry
from celery.schedules import crontab

def register_schedule(template: ReportTemplate):
    """Register or update the Celery Beat schedule for a template."""
    entry_key = f"periodai:template:{template.id}"
    
    # Parse cron string "0 8 * * 1" into crontab
    parts = template.schedule.split()
    schedule = crontab(
        minute=parts[0],
        hour=parts[1],
        day_of_month=parts[2],
        month_of_year=parts[3],
        day_of_week=parts[4]
    )
    
    entry = RedBeatSchedulerEntry(
        name=entry_key,
        task="periodai.run_report",
        schedule=schedule,
        kwargs={"template_id": str(template.id), "triggered_by": "schedule"},
        app=celery_app
    )
    entry.save()

def unregister_schedule(template_id: UUID):
    """Remove schedule when template deleted or deactivated."""
    entry_key = f"periodai:template:{template_id}"
    try:
        entry = RedBeatSchedulerEntry.from_key(entry_key, app=celery_app)
        entry.delete()
    except KeyError:
        pass  # Already removed
```

### Hook register/unregister into template CRUD:

```python
# In template_service.py
async def create_template(data, workspace) -> ReportTemplate:
    template = ReportTemplate(**data)
    session.add(template)
    await session.commit()
    if template.is_active:
        register_schedule(template)
    return template

async def update_template(template_id, data) -> ReportTemplate:
    # ... apply updates ...
    await session.commit()
    if template.is_active:
        register_schedule(template)  # upsert
    else:
        unregister_schedule(template_id)
    return template

async def delete_template(template_id):
    unregister_schedule(template_id)
    # ... delete from DB ...
```

---

## Manual Run (API Trigger)

```python
# app/routers/templates.py
@router.post("/{template_id}/run", status_code=202)
async def trigger_run(template_id: UUID, ...):
    template = await get_template_or_404(template_id, workspace)
    
    # Queue Celery task immediately
    task = run_report_task.apply_async(
        kwargs={"template_id": str(template_id), "triggered_by": "manual"},
        countdown=0
    )
    
    return {
        "run_id": "...",   # created inside task
        "status": "queued",
        "task_id": task.id,
        "message": "Report generation queued. Poll GET /runs/{run_id} for status."
    }
```

---

## Missed Run Behavior

When a worker restarts after downtime:

- **Default (skip):** RedBeat skips missed runs by default — the next scheduled run proceeds normally
- **Configuration:** Set `beat_catchup_on_start = False` in Celery config (default behavior)
- Do **not** auto-run all missed schedules — this could trigger 10s of reports unexpectedly

---

## Worker Startup Command

```bash
# Single worker process (development)
celery -A app.scheduler.celery_app worker --loglevel=info --concurrency=4

# Beat scheduler (one instance only — never scale this)
celery -A app.scheduler.celery_app beat --loglevel=info

# Combined for dev (NOT for production)
celery -A app.scheduler.celery_app worker --beat --loglevel=info
```

**Critical:** Never run more than **one** Beat instance. Multiple beats = duplicate scheduled tasks.

---

## Cron Expression Validation

Validate cron expressions when saving a template:

```python
from croniter import croniter

def validate_cron(expression: str) -> bool:
    """Returns True if cron expression is valid."""
    try:
        return croniter.is_valid(expression)
    except Exception:
        return False

# Common presets to cron mapping (expose in UI)
PRESETS = {
    "daily_8am":       "0 8 * * *",
    "weekly_monday":   "0 8 * * 1",
    "weekly_friday":   "0 8 * * 5",
    "monthly_1st":     "0 8 1 * *",
    "every_6_hours":   "0 */6 * * *",
}
```

---

## Observability

Expose these Prometheus metrics from the worker:

```python
# Using prometheus_client
report_runs_total = Counter("periodai_runs_total", "Total report runs", ["status", "triggered_by"])
report_run_duration = Histogram("periodai_run_duration_seconds", "Run duration", ["template_id"])
queue_depth = Gauge("periodai_queue_depth", "Celery queue depth")
```

Log every pipeline stage with structured JSON:

```python
logger.info("pipeline_stage", extra={
    "run_id": str(run.id),
    "template_id": str(template.id),
    "workspace_id": str(template.workspace_id),
    "stage": "generate",
    "section_id": section.id,
    "tokens": response.total_tokens,
    "duration_ms": elapsed_ms
})
```
