# 02 — Technology Stack & Project Structure

## Stack Decisions

| Layer | Technology | Version | Reason |
|-------|-----------|---------|--------|
| Backend API | FastAPI | 0.111+ | Async, auto OpenAPI, lightweight |
| Task queue | Celery | 5.x | Scheduling, retries, result backend |
| Message broker | Redis | 7.x | Celery broker + result backend |
| Database | PostgreSQL | 16.x | JSONB for sections/config, reliable |
| ORM | SQLAlchemy | 2.x (async) | Async sessions with asyncpg |
| Migrations | Alembic | latest | Schema versioning |
| LLM — primary | Anthropic Claude | claude-sonnet-4-20250514 | Default provider |
| LLM — secondary | Google Gemini | gemini-2.0-flash | Alternative provider |
| LLM — local | Ollama | any | Self-hosted, user-provided endpoint |
| Charts | Plotly | latest | Renders to PNG via kaleido |
| Email | SendGrid | v3 API | HTML + attachments |
| Slack | Slack SDK | latest | Rich blocks delivery |
| Auth | PyJWT + bcrypt | latest | JWT access + refresh tokens |
| Frontend | React + Vite | React 18 | SPA |
| Frontend styling | TailwindCSS | 3.x | Dark theme |
| Frontend charts | Recharts | latest | Dashboard charts |
| Containerization | Docker + Compose | latest | Dev and production |
| Deployment | Kubernetes | 1.28+ | Helm chart provided |

---

## Project Structure

```
periodai/
├── README.md
├── docker-compose.yml          # Dev environment
├── docker-compose.prod.yml     # Production
├── Makefile                    # Common commands
│
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── alembic/
│   │   ├── env.py
│   │   └── versions/
│   ├── app/
│   │   ├── main.py             # FastAPI app factory
│   │   ├── config.py           # Settings (pydantic-settings)
│   │   ├── database.py         # Async SQLAlchemy engine + session
│   │   ├── deps.py             # FastAPI dependencies (auth, db session)
│   │   │
│   │   ├── models/             # SQLAlchemy ORM models
│   │   │   ├── workspace.py
│   │   │   ├── user.py
│   │   │   ├── data_source.py
│   │   │   ├── report_template.py
│   │   │   ├── report_run.py
│   │   │   ├── delivery.py
│   │   │   └── api_key.py
│   │   │
│   │   ├── schemas/            # Pydantic request/response schemas
│   │   │   ├── auth.py
│   │   │   ├── workspace.py
│   │   │   ├── data_source.py
│   │   │   ├── template.py
│   │   │   ├── run.py
│   │   │   └── section.py
│   │   │
│   │   ├── routers/            # FastAPI routers
│   │   │   ├── auth.py
│   │   │   ├── workspaces.py
│   │   │   ├── sources.py
│   │   │   ├── templates.py
│   │   │   ├── runs.py
│   │   │   └── usage.py
│   │   │
│   │   ├── services/           # Business logic
│   │   │   ├── auth_service.py
│   │   │   ├── source_service.py
│   │   │   ├── template_service.py
│   │   │   ├── run_service.py
│   │   │   └── usage_service.py
│   │   │
│   │   ├── connectors/         # Data source connectors
│   │   │   ├── base.py         # Abstract base connector
│   │   │   ├── postgres.py
│   │   │   ├── mysql.py
│   │   │   ├── rest_api.py
│   │   │   ├── csv_file.py
│   │   │   └── google_sheets.py
│   │   │
│   │   ├── pipeline/           # LLM report generation pipeline
│   │   │   ├── runner.py       # Orchestrates pipeline stages
│   │   │   ├── fetcher.py      # Stage 1-2: fetch + transform data
│   │   │   ├── generator.py    # Stage 3-4: LLM section generation
│   │   │   ├── renderer.py     # Stage 5: assemble HTML report
│   │   │   └── sections/       # One file per section type
│   │   │       ├── base.py
│   │   │       ├── summary.py
│   │   │       ├── metric_cards.py
│   │   │       ├── trend.py
│   │   │       ├── bar_chart.py
│   │   │       ├── anomaly.py
│   │   │       ├── forecast.py
│   │   │       ├── insight.py
│   │   │       └── actions.py
│   │   │
│   │   ├── llm/                # LLM provider abstraction
│   │   │   ├── base.py         # Abstract LLMProvider
│   │   │   ├── anthropic.py
│   │   │   ├── gemini.py
│   │   │   └── ollama.py
│   │   │
│   │   ├── delivery/           # Report delivery
│   │   │   ├── base.py
│   │   │   ├── email.py
│   │   │   ├── slack.py
│   │   │   ├── webhook.py
│   │   │   └── pdf.py
│   │   │
│   │   ├── scheduler/
│   │   │   ├── celery_app.py   # Celery app factory
│   │   │   ├── tasks.py        # Celery tasks
│   │   │   └── beat.py         # Dynamic beat schedule
│   │   │
│   │   └── utils/
│   │       ├── crypto.py       # AES-256 encrypt/decrypt
│   │       ├── chart.py        # Plotly → PNG helper
│   │       └── logging.py      # Structured JSON logging
│
└── frontend/
    ├── Dockerfile
    ├── package.json
    ├── vite.config.ts
    ├── tailwind.config.ts
    └── src/
        ├── main.tsx
        ├── App.tsx
        ├── api/                # API client (axios)
        ├── pages/
        │   ├── Dashboard.tsx
        │   ├── Sources.tsx
        │   ├── Templates.tsx
        │   ├── TemplateEditor.tsx
        │   ├── Runs.tsx
        │   ├── ReportViewer.tsx
        │   └── Settings.tsx
        ├── components/
        └── hooks/
```

---

## docker-compose.yml (Dev)

```yaml
version: "3.9"
services:
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: periodai
      POSTGRES_USER: periodai
      POSTGRES_PASSWORD: periodai_dev
    ports: ["5432:5432"]
    volumes: [postgres_data:/var/lib/postgresql/data]

  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]

  api:
    build: ./backend
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    ports: ["8000:8000"]
    environment:
      DATABASE_URL: postgresql+asyncpg://periodai:periodai_dev@db/periodai
      REDIS_URL: redis://redis:6379/0
      SECRET_KEY: dev-secret-change-in-prod
      ENCRYPTION_KEY: dev-encryption-key-32-chars-long!
    depends_on: [db, redis]
    volumes: [./backend:/app]

  worker:
    build: ./backend
    command: celery -A app.scheduler.celery_app worker --loglevel=info
    environment:
      DATABASE_URL: postgresql+asyncpg://periodai:periodai_dev@db/periodai
      REDIS_URL: redis://redis:6379/0
    depends_on: [db, redis]

  beat:
    build: ./backend
    command: celery -A app.scheduler.celery_app beat --loglevel=info
    environment:
      DATABASE_URL: postgresql+asyncpg://periodai:periodai_dev@db/periodai
      REDIS_URL: redis://redis:6379/0
    depends_on: [db, redis]

  frontend:
    build: ./frontend
    command: npm run dev -- --host
    ports: ["3000:3000"]
    volumes: [./frontend:/app, /app/node_modules]

volumes:
  postgres_data:
```

---

## Environment Variables

```bash
# Backend — required
DATABASE_URL=postgresql+asyncpg://user:pass@host/periodai
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=<random 64-char string>
ENCRYPTION_KEY=<exactly 32 chars for AES-256>

# LLM providers — at least one required
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=AIza...
OLLAMA_BASE_URL=http://localhost:11434   # optional, user-provided

# Email — required for email delivery
SENDGRID_API_KEY=SG....
EMAIL_FROM=reports@nexuslayer.io

# Slack — required for Slack delivery
# (stored per-workspace in DB, not env var)

# Optional
SENTRY_DSN=https://...
LOG_LEVEL=INFO
```

---

## Makefile Commands

```makefile
up:         # docker compose up -d
down:       # docker compose down
migrate:    # alembic upgrade head
seed:       # python scripts/seed.py
test:       # pytest backend/tests/
lint:       # ruff check backend/
fmt:        # ruff format backend/
shell:      # docker compose exec api bash
logs:       # docker compose logs -f api worker
```
