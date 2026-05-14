<div align="center">

```
██████╗ ███████╗██████╗ ██╗ ██████╗ ██████╗  █████╗ ██╗
██╔══██╗██╔════╝██╔══██╗██║██╔═══██╗██╔══██╗██╔══██╗██║
██████╔╝█████╗  ██████╔╝██║██║   ██║██║  ██║███████║██║
██╔═══╝ ██╔══╝  ██╔══██╗██║██║   ██║██║  ██║██╔══██║██║
██║     ███████╗██║  ██║██║╚██████╔╝██████╔╝██║  ██║██║
╚═╝     ╚══════╝╚═╝  ╚═╝╚═╝ ╚═════╝ ╚═════╝ ╚═╝  ╚═╝╚═╝
```

### 📊 AI-Powered Business Reporting Automation

*Define templates. Schedule runs. Receive intelligent narrative reports — automatically.*

[![Build Status](https://img.shields.io/github/actions/workflow/status/nexuslayer/periodai/ci.yml?branch=main&style=flat-square&logo=github&label=build)](https://github.com/nexuslayer/periodai)
[![Version](https://img.shields.io/badge/version-1.0.0-blue?style=flat-square)](https://github.com/nexuslayer/periodai/releases)
[![License](https://img.shields.io/badge/license-MIT-green?style=flat-square)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61DAFB?style=flat-square&logo=react)](https://react.dev)
[![Celery](https://img.shields.io/badge/Celery-5.4-37814A?style=flat-square)](https://docs.celeryq.dev)
[![Redis](https://img.shields.io/badge/Redis-7-DC382D?style=flat-square&logo=redis&logoColor=white)](https://redis.io)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?style=flat-square&logo=postgresql&logoColor=white)](https://www.postgresql.org)
[![NexusLayer](https://img.shields.io/badge/NexusLayer-Platform-0F172A?style=flat-square)](../README.md)

<br/>

[**Live Demo**](http://192.168.68.111:3003) · [**API Docs**](http://192.168.68.111:8090/docs) · [**Report Bug**](https://github.com/nexuslayer/periodai/issues) · [**Request Feature**](https://github.com/nexuslayer/periodai/issues)

</div>

---

## 📋 Table of Contents

- [✨ Features](#-features)
- [🏗️ Architecture](#%EF%B8%8F-architecture)
- [🚀 Quick Start](#-quick-start)
- [📡 API Reference](#-api-reference)
- [🔧 SDKs & Integration](#-sdks--integration)
- [🔀 Ecosystem Integrations](#-ecosystem-integrations)
- [🤖 Claude Code CLI / MCP](#-claude-code-cli--mcp)
- [⚙️ Configuration](#%EF%B8%8F-configuration)
- [🧑‍💻 Development](#-development)
- [🆚 Why PeriodAI?](#-why-periodai)
- [📄 License](#-license)

---

## ✨ Features

| Feature | Description |
|---|---|
| 📋 **Report Templates** | Define report blueprints — data source, SQL query, narrative instructions, schedule |
| ⏰ **Cron Scheduling** | Cron-based scheduling with timezone support — runs fire automatically |
| 🤖 **AI Narrative Generation** | LLM writes executive summaries, trend analysis, anomaly callouts — in your voice |
| 🗄️ **Multi-Source Data** | Connect PostgreSQL, REST APIs, CSV uploads, or Google Sheets as data sources |
| 📄 **Multiple Output Formats** | Deliver reports as PDF, HTML, Markdown, or JSON |
| 📧 **Delivery Channels** | Email, webhook callback, or download from dashboard |
| 📊 **Run History** | Full audit trail of every run — data snapshot, LLM prompt, output, timing |
| 🔔 **Failure Alerts** | Notify via webhook or email when a run fails |
| 🔁 **Manual Trigger** | Trigger any template on-demand from UI or API |
| 🔐 **Credential Management** | Data source credentials stored encrypted in AgentVault |

---

## 🏗️ Architecture

```mermaid
graph TB
    subgraph Clients["🌐 Clients"]
        Dashboard["React Dashboard\n:3003"]
        ExternalWebhook["External System\nWebhook Trigger"]
        EmailClient["📧 Email Inbox\nReport Delivery"]
    end

    subgraph API["⚙️ FastAPI :8090"]
        TemplateAPI["Template API\nCRUD + Validation"]
        RunAPI["Run API\nTrigger + Status"]
        AuthAPI["Auth API\nJWT Login"]
        WebhookAPI["Webhook Receiver\nFlowMesh triggers"]
    end

    subgraph Workers["⚙️ Celery Workers"]
        Scheduler["Beat Scheduler\nCron trigger"]
        FetchWorker["Data Fetch Worker\nSQL · REST · CSV"]
        LLMWorker["LLM Worker\nNarrative generation"]
        RenderWorker["Render Worker\nPDF · HTML · MD"]
        DeliveryWorker["Delivery Worker\nEmail · Webhook"]
    end

    subgraph Data["💾 Data Layer"]
        PG[("PostgreSQL 16\nTemplates · Runs\nUsers")]
        Redis[("Redis 7\nTask Queue\nRun state")]
    end

    subgraph DataSources["📡 Data Sources"]
        ExtPG["PostgreSQL\nDatabases"]
        RestAPI["REST APIs"]
        CSV["CSV Uploads\nGoogle Sheets"]
    end

    subgraph Platform["🔗 NexusLayer Platform"]
        ModelRouter["🔀 ModelRouter"]
        AgentVault["🔐 AgentVault"]
        WatchGrid["📊 WatchGrid"]
        FlowMesh["🌊 FlowMesh"]
    end

    Dashboard <-->|REST + JWT| API
    ExternalWebhook --> WebhookAPI
    
    API --> PG
    API --> Redis

    Scheduler -->|Enqueue jobs| Redis
    Redis --> FetchWorker
    FetchWorker --> ExtPG
    FetchWorker --> RestAPI
    FetchWorker --> CSV
    FetchWorker -->|Pass data| LLMWorker
    LLMWorker -->|Narrative| RenderWorker
    RenderWorker -->|Output| DeliveryWorker
    DeliveryWorker --> EmailClient

    LLMWorker --> ModelRouter
    FetchWorker --> AgentVault
    Workers --> WatchGrid
    FlowMesh -->|Trigger run| WebhookAPI
```

### Report Run Lifecycle

```mermaid
stateDiagram-v2
    [*] --> PENDING: Cron fires / manual trigger
    PENDING --> FETCHING: Worker picks up job
    FETCHING --> FETCH_ERROR: Data source unreachable
    FETCHING --> GENERATING: Data fetched successfully
    GENERATING --> GENERATION_ERROR: LLM call fails
    GENERATING --> RENDERING: Narrative generated
    RENDERING --> DELIVERING: PDF/HTML/MD built
    DELIVERING --> DELIVERED: Email/webhook sent
    DELIVERED --> [*]

    FETCH_ERROR --> [*]: Alert sent + logged
    GENERATION_ERROR --> [*]: Alert sent + logged
```

---

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose v2
- LLM API key (or ModelRouter configured)

### 1. Clone & Configure

```bash
git clone https://github.com/nexuslayer/periodai.git
cd periodai

cp .env.example .env
```

Edit `.env`:

```bash
# Required
DB_PASSWORD=your_secure_password
SECRET_KEY=your-secret-key-32-chars-min

# LLM (choose one)
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
# OR: MODELROUTER_URL=http://modelrouter:8085

# Email delivery (optional)
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USER=apikey
SMTP_PASSWORD=your_sendgrid_key
SMTP_FROM=reports@yourcompany.com

# Optional: NexusLayer integrations
AGENTVAULT_URL=http://agentvault:8082
WATCHGRID_URL=http://watchgrid:8088
```

### 2. Launch

```bash
docker compose up -d
```

```
✅ PostgreSQL  → localhost:5432
✅ Redis       → localhost:6379
✅ API         → http://localhost:8090
✅ Worker      → (background)
✅ Scheduler   → (background)
✅ Frontend    → http://localhost:3003
```

### 3. Create & Run Your First Report

```bash
# Get token
TOKEN=$(curl -s -X POST http://localhost:8090/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin"}' | jq -r .token)

# Create a weekly sales report template
TEMPLATE=$(curl -s -X POST http://localhost:8090/api/v1/templates \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Weekly Sales Summary",
    "dataSource": {
      "type": "postgresql",
      "connectionString": "postgresql://user:pass@db-host:5432/sales"
    },
    "query": "SELECT date_trunc('"'"'week'"'"', order_date) as week, SUM(amount) as revenue, COUNT(*) as orders FROM orders WHERE order_date >= NOW() - INTERVAL '"'"'8 weeks'"'"' GROUP BY 1 ORDER BY 1 DESC",
    "schedule": "0 8 * * 1",
    "instructions": "Write a concise executive summary. Highlight week-over-week growth, flag any drops > 10%, and suggest one actionable recommendation.",
    "outputFormat": "pdf",
    "delivery": {"type": "email", "recipients": ["ceo@company.com"]}
  }')

echo "Template: $(echo $TEMPLATE | jq -r .id)"

# Trigger manually right now
RUN=$(curl -s -X POST \
  "http://localhost:8090/api/v1/templates/$(echo $TEMPLATE | jq -r .id)/run" \
  -H "Authorization: Bearer $TOKEN")

echo "Run started: $(echo $RUN | jq -r .id)"

# Poll status
watch -n 2 "curl -s http://localhost:8090/api/v1/runs/$(echo $RUN | jq -r .id) \
  -H 'Authorization: Bearer $TOKEN' | jq '{status: .status, progress: .progress}'"
```

---

## 📡 API Reference

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/auth/login` | Login → JWT (`username`, `password`) |
| `POST` | `/api/v1/auth/refresh` | Refresh JWT |
| `GET` | `/api/v1/auth/me` | Current user |

### Templates

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/templates` | List all templates (`?active=true`) |
| `POST` | `/api/v1/templates` | Create report template |
| `GET` | `/api/v1/templates/{id}` | Template details |
| `PUT` | `/api/v1/templates/{id}` | Update template |
| `DELETE` | `/api/v1/templates/{id}` | Delete template |
| `POST` | `/api/v1/templates/{id}/run` | **Trigger manual run** |
| `POST` | `/api/v1/templates/{id}/validate` | Test data source connection + query |

### Runs

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/runs` | List runs (`?templateId=`, `?status=`, `?page=`) |
| `GET` | `/api/v1/runs/{id}` | Run status + metadata |
| `GET` | `/api/v1/runs/{id}/output` | Get report content (Markdown/JSON) |
| `GET` | `/api/v1/runs/{id}/download` | Download report file (PDF/HTML) |
| `DELETE` | `/api/v1/runs/{id}` | Delete run and output |

### Data Sources

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/datasources` | List configured data sources |
| `POST` | `/api/v1/datasources` | Register a data source |
| `POST` | `/api/v1/datasources/{id}/test` | Test connection |
| `DELETE` | `/api/v1/datasources/{id}` | Remove data source |

### Webhooks

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/webhooks/trigger/{templateId}` | Trigger template via webhook (FlowMesh integration) |

<details>
<summary><strong>📄 Interactive API Docs</strong></summary>

FastAPI auto-generates interactive documentation:

- **Swagger UI:** `http://localhost:8090/docs`
- **ReDoc:** `http://localhost:8090/redoc`
- **OpenAPI JSON:** `http://localhost:8090/openapi.json`

</details>

---

## 🔧 SDKs & Integration

### Python Client

```python
import httpx
from typing import Literal

API = "http://localhost:8090"


class PeriodAIClient:
    def __init__(self, username: str, password: str):
        r = httpx.post(f"{API}/api/v1/auth/login",
                       json={"username": username, "password": password})
        r.raise_for_status()
        self._token = r.json()["token"]
        self._h = {"Authorization": f"Bearer {self._token}"}

    def create_template(
        self,
        name: str,
        query: str,
        connection_string: str,
        schedule: str,
        instructions: str,
        output_format: Literal["pdf", "html", "markdown", "json"] = "pdf",
    ) -> dict:
        return httpx.post(f"{API}/api/v1/templates", headers=self._h, json={
            "name": name,
            "dataSource": {"type": "postgresql", "connectionString": connection_string},
            "query": query,
            "schedule": schedule,
            "instructions": instructions,
            "outputFormat": output_format,
        }).json()

    def run(self, template_id: str) -> dict:
        return httpx.post(
            f"{API}/api/v1/templates/{template_id}/run", headers=self._h
        ).json()

    def wait_for_run(self, run_id: str, poll_seconds: int = 5) -> dict:
        import time
        while True:
            run = httpx.get(f"{API}/api/v1/runs/{run_id}", headers=self._h).json()
            if run["status"] in ("DELIVERED", "FETCH_ERROR", "GENERATION_ERROR"):
                return run
            print(f"  ⏳ {run['status']} — {run.get('progress', '')}...")
            time.sleep(poll_seconds)

    def download(self, run_id: str, dest: str):
        content = httpx.get(
            f"{API}/api/v1/runs/{run_id}/download", headers=self._h
        ).content
        with open(dest, "wb") as f:
            f.write(content)
        print(f"✅ Report saved to {dest}")


# --- Usage ---
client = PeriodAIClient("admin", "secret")

template = client.create_template(
    name="Monthly Revenue Report",
    query="""
        SELECT
            to_char(date_trunc('month', created_at), 'Mon YYYY') AS month,
            SUM(amount_cents) / 100.0 AS revenue_usd,
            COUNT(DISTINCT customer_id) AS customers
        FROM orders
        WHERE created_at >= NOW() - INTERVAL '12 months'
        GROUP BY 1
        ORDER BY MIN(created_at) DESC
    """,
    connection_string="postgresql://readonly:pass@db:5432/prod",
    schedule="0 9 1 * *",   # 9am on the 1st of every month
    instructions=(
        "Write an executive summary for the board. Highlight: (1) MoM revenue growth, "
        "(2) customer acquisition trends, (3) any month with > 15% drop and likely cause, "
        "(4) three actionable recommendations for next quarter."
    ),
    output_format="pdf",
)

run = client.run(template["id"])
result = client.wait_for_run(run["id"])

if result["status"] == "DELIVERED":
    client.download(result["id"], "revenue_report.pdf")
else:
    print(f"❌ Run failed: {result.get('error')}")
```

### Webhook Integration

```bash
# Trigger a report from any external system
curl -X POST http://localhost:8090/api/v1/webhooks/trigger/TEMPLATE_ID \
  -H "X-PeriodAI-Secret: your_webhook_secret" \
  -H "Content-Type: application/json" \
  -d '{"context": {"triggered_by": "deploy_pipeline", "version": "v2.4.1"}}'
```

### Google Sheets Data Source

```json
{
  "name": "Weekly OKR Tracker",
  "dataSource": {
    "type": "google_sheets",
    "spreadsheetId": "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgVE2upms",
    "range": "Q3 OKRs!A1:E50",
    "credentials": "{{secrets.google_service_account}}"
  },
  "schedule": "0 9 * * 5",
  "instructions": "Summarize OKR progress for the week. Flag any objective below 70% completion with a red flag emoji and a recommended action."
}
```

---

## 🔀 Ecosystem Integrations

| Product | Direction | Integration |
|---------|-----------|-------------|
| 🔀 [**ModelRouter**](../ModelRouter/README.md) | PeriodAI → ModelRouter | All LLM narrative generation calls routed through ModelRouter for provider fallback, cost caps, and caching |
| 🔐 [**AgentVault**](../AgentVault/README.md) | PeriodAI → AgentVault | Database credentials, API keys, and SMTP passwords stored encrypted; fetched securely at run time |
| 🌊 [**FlowMesh**](../flowmesh/README.md) | FlowMesh → PeriodAI | FlowMesh `WEBHOOK` nodes trigger report runs as pipeline steps — e.g., "run revenue report after nightly ETL completes" |
| 📊 [**WatchGrid**](../watchgrid/README.md) | PeriodAI → WatchGrid | Every run event (started, data fetched, generated, delivered, failed) shipped to WatchGrid with timing and LLM costs |

---

## 🤖 Claude Code CLI / MCP

PeriodAI exposes an MCP server allowing AI agents (including Claude Code CLI) to trigger reports and query run outputs programmatically.

### MCP Tools

| Tool | Description |
|------|-------------|
| `periodai_list_templates` | List all configured report templates |
| `periodai_run_template` | Trigger a report template by ID or name |
| `periodai_get_run` | Get run status and output |
| `periodai_get_report_content` | Retrieve the Markdown content of a completed report |

### Configure MCP

```json
{
  "mcpServers": {
    "periodai": {
      "url": "http://localhost:8090/mcp",
      "headers": {
        "Authorization": "Bearer YOUR_PERIODAI_TOKEN"
      }
    }
  }
}
```

```bash
# Ask Claude to generate a report as part of a task
claude -p "Run the 'Monthly Revenue Report' template, wait for it to complete,
           then summarize the key findings and suggest 3 follow-up tasks" \
  --mcp periodai
```

---

## ⚙️ Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DB_PASSWORD` | ✅ | — | PostgreSQL password |
| `SECRET_KEY` | ✅ | — | FastAPI JWT signing secret |
| `LLM_PROVIDER` | — | `openai` | `openai` \| `anthropic` \| `modelrouter` |
| `OPENAI_API_KEY` | ⚠️ | — | Required if `LLM_PROVIDER=openai` |
| `ANTHROPIC_API_KEY` | ⚠️ | — | Required if `LLM_PROVIDER=anthropic` |
| `MODELROUTER_URL` | ⚠️ | — | Required if `LLM_PROVIDER=modelrouter` |
| `LLM_MODEL` | — | `gpt-4o-mini` | LLM model for narrative generation |
| `REDIS_URL` | — | `redis://redis:6379/0` | Redis connection URL |
| `DATABASE_URL` | — | auto-built | PostgreSQL SQLAlchemy URL |
| `SMTP_HOST` | — | — | SMTP server for email delivery |
| `SMTP_PORT` | — | `587` | SMTP port |
| `SMTP_USER` | — | — | SMTP username |
| `SMTP_PASSWORD` | — | — | SMTP password |
| `SMTP_FROM` | — | — | From address for report emails |
| `WEBHOOK_SECRET` | — | — | HMAC secret for webhook endpoint |
| `MAX_QUERY_ROWS` | — | `10000` | Max rows fetched per data source query |
| `RUN_TIMEOUT_SECONDS` | — | `300` | Max seconds per run (5 min) |
| `AGENTVAULT_URL` | — | — | AgentVault endpoint |
| `WATCHGRID_URL` | — | — | WatchGrid ingest endpoint |

<details>
<summary><strong>Full docker-compose.yml</strong></summary>

```yaml
version: '3.8'
services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: periodai
      POSTGRES_USER: periodai
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes: ["pgdata:/var/lib/postgresql/data"]
    ports: ["5432:5432"]

  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]

  api:
    build: ./periodai
    command: uvicorn app.main:app --host 0.0.0.0 --port 8090
    ports: ["8090:8090"]
    environment:
      DATABASE_URL: postgresql://periodai:${DB_PASSWORD}@postgres:5432/periodai
      REDIS_URL: redis://redis:6379/0
      SECRET_KEY: ${SECRET_KEY}
      LLM_PROVIDER: ${LLM_PROVIDER:-openai}
      OPENAI_API_KEY: ${OPENAI_API_KEY}
    depends_on: [postgres, redis]

  worker:
    build: ./periodai
    command: celery -A app.celery worker --loglevel=info --concurrency=4
    environment:
      DATABASE_URL: postgresql://periodai:${DB_PASSWORD}@postgres:5432/periodai
      REDIS_URL: redis://redis:6379/0
      OPENAI_API_KEY: ${OPENAI_API_KEY}
    depends_on: [postgres, redis]

  scheduler:
    build: ./periodai
    command: celery -A app.celery beat --loglevel=info
    environment:
      DATABASE_URL: postgresql://periodai:${DB_PASSWORD}@postgres:5432/periodai
      REDIS_URL: redis://redis:6379/0
    depends_on: [postgres, redis]

  frontend:
    build: ./frontend
    ports: ["3003:3003"]
    environment:
      REACT_APP_API_URL: http://localhost:8090
    depends_on: [api]

volumes:
  pgdata:
```

</details>

---

## 🧑‍💻 Development

### Local Setup

```bash
git clone https://github.com/nexuslayer/periodai.git
cd periodai

# Start dependencies
docker compose up -d postgres redis

# Backend
cd periodai
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in your values

# Run migrations
alembic upgrade head

# Start API
uvicorn app.main:app --reload --port 8090

# Start worker (separate terminal)
celery -A app.celery worker --loglevel=debug

# Start scheduler (separate terminal)
celery -A app.celery beat --loglevel=debug

# Frontend (separate terminal)
cd ../frontend
npm install && npm start
```

### Project Structure

```
periodai/
├── periodai/                # FastAPI application
│   ├── app/
│   │   ├── api/             # Route handlers (templates, runs, auth)
│   │   ├── models/          # SQLAlchemy models
│   │   ├── schemas/         # Pydantic request/response schemas
│   │   ├── services/
│   │   │   ├── fetcher.py   # Data source fetching (PG, REST, CSV)
│   │   │   ├── llm.py       # LLM narrative generation
│   │   │   ├── renderer.py  # PDF/HTML/MD rendering
│   │   │   └── delivery.py  # Email + webhook delivery
│   │   ├── tasks/           # Celery task definitions
│   │   ├── celery.py        # Celery app config
│   │   └── main.py          # FastAPI app entry
│   ├── alembic/             # DB migrations
│   └── tests/
├── frontend/                # React dashboard
│   └── src/
│       ├── pages/           # Templates, Runs, Settings
│       └── components/      # RunStatus, ReportViewer, etc.
└── docker-compose.yml
```

### Running Tests

```bash
cd periodai
pytest tests/ -v

# With coverage
pytest tests/ --cov=app --cov-report=term-missing

# Integration tests (requires running stack)
pytest tests/integration/ -v --env=integration
```

---

## 🆚 Why PeriodAI?

| Feature | PeriodAI | Tableau | Power BI | Custom Scripts |
|---------|:--------:|:-------:|:--------:|:--------------:|
| **AI narrative generation** | ✅ | ❌ | ⚠️ Copilot only | ❌ |
| **Self-hosted** | ✅ | ❌ | ❌ | ✅ |
| **Cron scheduling** | ✅ | ⚠️ (paid) | ⚠️ (paid) | ✅ (manual) |
| **Multi-source data** | ✅ | ✅ | ✅ | ✅ (fragile) |
| **PDF/HTML/MD output** | ✅ | ⚠️ (PDF only) | ⚠️ | ❌ |
| **Email + webhook delivery** | ✅ | ⚠️ (paid) | ✅ | ✅ (manual) |
| **Template management UI** | ✅ | ✅ | ✅ | ❌ |
| **REST API** | ✅ | ⚠️ limited | ⚠️ limited | ✅ (custom) |
| **Price** | **Free / Self-hosted** | $75+/mo | $10+/mo | Dev time |

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

<div align="center">

**PeriodAI** is part of the **NexusLayer Platform** — a suite of self-hosted AI developer tools.

[AgentShop](../AIAgentRental/README.md) · [BrainVault](../BrainVault/README.md) · [PeriodAI](../PeriodAIProduct/README.md) · [WikiLLM](../WikiLLM/README.md) · [ModelRouter](../ModelRouter/README.md) · [AgentVault](../AgentVault/README.md) · [FlowMesh](../flowmesh/README.md) · [WatchGrid](../watchgrid/README.md)

<br/>

*Your data. Your schedule. Your narrative.*

</div>
