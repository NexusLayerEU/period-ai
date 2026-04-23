# 03 — Data Models & Database Schema

## ORM Conventions

- All models inherit from a `Base` with `id` (UUID), `created_at`, `updated_at`
- Use `UUID` primary keys (not integer sequences)
- JSON/JSONB columns use `postgresql.JSONB` type
- Encrypted fields stored as `Text` — encrypt/decrypt in service layer, never in model
- All timestamps are UTC (`timezone=True`)

---

## Models

### Workspace

```python
class Workspace(Base):
    __tablename__ = "workspaces"

    id: UUID (PK)
    name: str (max 100)
    slug: str (unique, max 50, URL-safe)
    owner_id: UUID (FK → users.id)
    llm_provider: str  # "anthropic" | "gemini" | "ollama"
    llm_model: str     # e.g. "claude-sonnet-4-20250514"
    ollama_base_url: str | None
    created_at: datetime
    updated_at: datetime
```

### User

```python
class User(Base):
    __tablename__ = "users"

    id: UUID (PK)
    email: str (unique)
    hashed_password: str
    full_name: str
    is_active: bool (default True)
    created_at: datetime
    updated_at: datetime

# Junction table
class WorkspaceMember(Base):
    __tablename__ = "workspace_members"

    workspace_id: UUID (FK → workspaces.id)
    user_id: UUID (FK → users.id)
    role: str  # "owner" | "admin" | "member"
    joined_at: datetime
    # PK: (workspace_id, user_id)
```

### DataSource

```python
class DataSource(Base):
    __tablename__ = "data_sources"

    id: UUID (PK)
    workspace_id: UUID (FK → workspaces.id)
    name: str (max 100)
    type: str  # "postgres" | "mysql" | "sqlite" | "mssql" |
               # "rest_api" | "csv" | "xlsx" | "google_sheets"
    config_encrypted: str  # AES-256 encrypted JSON blob
    # config shape varies by type — see connectors spec (04)
    last_tested_at: datetime | None
    test_status: str | None  # "ok" | "error"
    test_error: str | None
    created_at: datetime
    updated_at: datetime
```

**config_encrypted decrypted shapes:**

```json
// postgres / mysql / mssql
{
  "host": "db.example.com",
  "port": 5432,
  "database": "mydb",
  "username": "readonly_user",
  "password": "secret",
  "ssl": true
}

// rest_api
{
  "base_url": "https://api.example.com",
  "auth_type": "bearer",        // "none" | "api_key" | "bearer" | "basic"
  "auth_value": "token_here",   // API key or token
  "headers": { "X-Custom": "value" },
  "pagination_type": "offset",  // "none" | "offset" | "cursor" | "page"
  "pagination_param": "offset",
  "page_size": 100
}

// csv / xlsx
{
  "location": "upload",         // "upload" | "url" | "s3"
  "url": "https://...",         // if location=url
  "s3_bucket": "my-bucket",     // if location=s3
  "s3_key": "reports/data.csv"
}

// google_sheets
{
  "sheet_id": "1BxiMVs0X...",
  "service_account_json": "{ ... }"  // service account key JSON
}
```

### ReportTemplate

```python
class ReportTemplate(Base):
    __tablename__ = "report_templates"

    id: UUID (PK)
    workspace_id: UUID (FK → workspaces.id)
    name: str (max 200)
    description: str | None
    source_ids: list[UUID]  # JSONB array of DataSource IDs
    sections: list[dict]    # JSONB — ordered section configs (see below)
    schedule: str           # cron expression e.g. "0 8 * * 1" (Monday 08:00)
    timezone: str           # e.g. "Europe/Tirane", "UTC"
    delivery_channels: list[dict]  # JSONB — channel configs (see 07-delivery.md)
    is_active: bool (default True)
    last_run_at: datetime | None
    created_at: datetime
    updated_at: datetime
```

**sections JSONB array — each item:**

```json
{
  "id": "uuid-string",
  "type": "summary",
  "title": "Weekly Performance Summary",
  "position": 0,
  "source_id": "uuid-of-data-source",
  "query": "SELECT date, revenue, users FROM metrics WHERE date >= :start_date ORDER BY date",
  "query_params": {
    "start_date": "last_7_days"
  },
  "llm_prompt": "Summarize the revenue and user trends. Highlight any week-over-week changes. Be concise and executive-friendly.",
  "chart_config": {
    "x": "date",
    "y": "revenue",
    "color": "#FF8C42",
    "type": "line"
  },
  "output_format": "markdown"
}
```

**query_params date shortcuts** (resolved at runtime):

| Shortcut | Resolves to |
|----------|-------------|
| `last_7_days` | today - 7 days |
| `last_30_days` | today - 30 days |
| `last_90_days` | today - 90 days |
| `this_week` | Monday of current week |
| `this_month` | 1st of current month |
| `last_week` | previous Mon-Sun |
| `last_month` | previous calendar month |

### ReportRun

```python
class ReportRun(Base):
    __tablename__ = "report_runs"

    id: UUID (PK)
    template_id: UUID (FK → report_templates.id)
    workspace_id: UUID (FK → workspaces.id)
    triggered_by: str  # "schedule" | "manual" | "api"
    status: str        # "queued" | "running" | "completed" | "failed"
    started_at: datetime | None
    completed_at: datetime | None
    duration_ms: int | None
    output_html: str | None       # Full rendered HTML report
    output_json: dict | None      # JSONB — structured report data
    output_pdf_url: str | None    # URL to stored PDF
    total_tokens: int | None
    total_cost_usd: float | None
    section_metadata: dict | None # JSONB — per-section token usage, status, errors
    error_message: str | None
    created_at: datetime
    updated_at: datetime
```

**section_metadata shape:**

```json
{
  "sections": [
    {
      "id": "section-uuid",
      "type": "summary",
      "status": "completed",
      "tokens_used": 823,
      "duration_ms": 1240,
      "error": null
    },
    {
      "id": "section-uuid-2",
      "type": "anomaly",
      "status": "failed",
      "tokens_used": 0,
      "duration_ms": 0,
      "error": "LLM timeout after 3 retries"
    }
  ]
}
```

### Delivery

```python
class Delivery(Base):
    __tablename__ = "deliveries"

    id: UUID (PK)
    run_id: UUID (FK → report_runs.id)
    channel: str    # "email" | "slack" | "webhook" | "storage"
    status: str     # "pending" | "sent" | "failed"
    sent_at: datetime | None
    error: str | None
    metadata: dict | None  # JSONB — recipient, message_ts, etc.
    created_at: datetime
```

### ApiKey

```python
class ApiKey(Base):
    __tablename__ = "api_keys"

    id: UUID (PK)
    workspace_id: UUID (FK → workspaces.id)
    name: str (max 100)
    key_hash: str     # bcrypt hash of the actual key
    key_prefix: str   # first 8 chars of key shown in UI (e.g. "pai_k8x2")
    last_used_at: datetime | None
    created_at: datetime
    # Note: actual key is shown ONCE at creation — never stored in plaintext
```

---

## Alembic Setup

```python
# alembic/env.py — key parts
from app.database import Base
from app.models import *  # ensure all models imported

target_metadata = Base.metadata

def run_migrations_online():
    connectable = create_engine(settings.DATABASE_URL.replace("+asyncpg", ""))
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()
```

---

## Crypto Utility

```python
# app/utils/crypto.py
import base64
from cryptography.fernet import Fernet
from app.config import settings

def get_fernet() -> Fernet:
    key = base64.urlsafe_b64encode(settings.ENCRYPTION_KEY.encode()[:32])
    return Fernet(key)

def encrypt(value: str) -> str:
    return get_fernet().encrypt(value.encode()).decode()

def decrypt(value: str) -> str:
    return get_fernet().decrypt(value.encode()).decode()

# Usage in service:
# source.config_encrypted = encrypt(json.dumps(config_dict))
# config = json.loads(decrypt(source.config_encrypted))
```

---

## Initial Migration Checklist

After running `alembic revision --autogenerate -m "initial"` verify:

- [ ] All UUID primary keys use `gen_random_uuid()` as server default
- [ ] `created_at` / `updated_at` have `server_default=func.now()`
- [ ] `updated_at` has `onupdate=func.now()`
- [ ] Index on `report_runs(workspace_id, status)`
- [ ] Index on `report_runs(template_id, created_at DESC)`
- [ ] Index on `data_sources(workspace_id)`
- [ ] Index on `report_templates(workspace_id, is_active)`
