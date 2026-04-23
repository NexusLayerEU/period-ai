# PeriodAI — Usage Guide

> Automate the full reporting cycle: connect data, build narrative templates, schedule delivery, receive decision-ready reports.

**API:** `http://192.168.68.111:8090`  
**UI:** `http://192.168.68.111:3003`

---

## Table of Contents

1. [What is PeriodAI?](#1-what-is-periodai)
2. [Quick Start](#2-quick-start)
3. [Authentication](#3-authentication)
4. [Data Source Configuration](#4-data-source-configuration)
5. [Template Building](#5-template-building)
6. [Schedule Configuration](#6-schedule-configuration)
7. [Delivery Channels](#7-delivery-channels)
8. [Running Reports](#8-running-reports)
9. [API Reference](#9-api-reference)
10. [Agent API Access](#10-agent-api-access)
11. [Integration Examples](#11-integration-examples)
12. [Complete Example: Weekly DevOps Metrics Report](#12-complete-example-weekly-devops-metrics-report)

---

## 1. What is PeriodAI?

PeriodAI automates the full reporting cycle for teams that need regular, narrative-driven insights from their data.

**Core workflow:**

```
Data Sources → Report Templates → Scheduler → LLM Engine → Delivery
   (DB/API/CSV)    (sections+prompts)  (cron)    (narrative)  (email/Slack/webhook)
```

**What you get:**
- AI-written narrative summaries that explain *why* metrics changed — not just raw numbers
- Automatic anomaly detection with natural-language explanations
- Trend forecasts and actionable recommendations
- Reports delivered as formatted HTML/PDF to email, Slack, or any webhook
- Full REST API for programmatic access by agents and integrations

PeriodAI uses [ModelRouter](../ModelRouter) for all LLM operations and [AgentVault](../AgentVault) for secure credential storage.

---

## 2. Quick Start

The fastest path from zero to a scheduled report.

### Step 1 — Register and Login

```bash
# Register
curl -s -X POST http://192.168.68.111:8090/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "you@company.com",
    "password": "yourpassword",
    "full_name": "Your Name"
  }'

# Login — save the access_token
TOKEN=$(curl -s -X POST http://192.168.68.111:8090/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"you@company.com","password":"yourpassword"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

echo "Token: $TOKEN"
```

### Step 2 — Create a Workspace

```bash
curl -s -X POST http://192.168.68.111:8090/api/v1/workspaces \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Engineering Analytics",
    "slug": "eng-analytics",
    "llm_provider": "anthropic",
    "llm_model": "claude-sonnet-4-20250514"
  }'
```

Save the returned `id` as `WORKSPACE_ID`.

### Step 3 — Add a Data Source

```bash
curl -s -X POST http://192.168.68.111:8090/api/v1/workspaces/$WORKSPACE_ID/data-sources \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Production DB",
    "type": "postgresql",
    "connectionString": "postgresql://user:pass@db.internal:5432/prod"
  }'
```

### Step 4 — Create a Report Template

```bash
curl -s -X POST http://192.168.68.111:8090/api/v1/workspaces/$WORKSPACE_ID/templates \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Weekly Engineering Report",
    "schedule": "0 9 * * 1",
    "sections": [
      {
        "type": "summary",
        "title": "Executive Summary",
        "dataSourceId": "<data-source-id>",
        "query": "SELECT date, deploys, incidents, p95_latency_ms FROM metrics WHERE date >= NOW() - INTERVAL '\''7 days'\''",
        "prompt": "Summarize the key engineering metrics for this week. Highlight any significant changes compared to previous periods."
      },
      {
        "type": "anomaly",
        "title": "Anomalies & Alerts",
        "dataSourceId": "<data-source-id>",
        "query": "SELECT * FROM metrics WHERE date >= NOW() - INTERVAL '\''7 days'\''",
        "prompt": "Identify any anomalies or concerning trends in the data. Explain the likely cause and impact."
      }
    ],
    "deliveryChannels": [
      {
        "type": "slack",
        "webhookUrl": "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
      }
    ]
  }'
```

### Step 5 — Trigger a Test Run

```bash
curl -s -X POST http://192.168.68.111:8090/api/v1/workspaces/$WORKSPACE_ID/templates/$TEMPLATE_ID/run \
  -H "Authorization: Bearer $TOKEN"
```

Your report will be generated immediately and sent to Slack.

---

## 3. Authentication

### User JWT (Interactive / UI)

```bash
# Login
POST /api/v1/auth/login
{"email": "user@company.com", "password": "secret"}

# Response
{
  "access_token": "eyJhbGci...",
  "refresh_token": "eyJhbGci...",
  "token_type": "bearer",
  "expires_in": 3600
}

# Use in all requests
Authorization: Bearer <access_token>
```

**Refresh before expiry:**

```bash
curl -X POST http://192.168.68.111:8090/api/v1/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "<refresh_token>"}'
```

### API Key (Agents / Integrations)

API keys use the `pai_` prefix and are scoped to a workspace. They never expire.

```bash
# All requests using an API key
Authorization: Bearer pai_<workspace_key>
```

API keys grant `member`-level access to the workspace they belong to. Generate them in the UI under **Workspace Settings → API Keys**, or via:

```bash
curl -X POST http://192.168.68.111:8090/api/v1/workspaces/$WORKSPACE_ID/api-keys \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "FlowMesh Integration"}'
```

---

## 4. Data Source Configuration

### PostgreSQL

```json
{
  "name": "Production DB",
  "type": "postgresql",
  "connectionString": "postgresql://reporter:password@db.internal:5432/production"
}
```

**With AgentVault credentials (recommended):**

```json
{
  "name": "Production DB",
  "type": "postgresql",
  "connectionString": "postgresql://{agentVaultRef:db-reporter-user}:{agentVaultRef:db-reporter-pass}@db.internal:5432/production"
}
```

See [Section 11 — AgentVault Integration](#periodai--agentvault) for full details.

### MySQL

```json
{
  "name": "Analytics DB",
  "type": "mysql",
  "connectionString": "mysql://analyst:pass@mysql.internal:3306/analytics"
}
```

### REST API

```json
{
  "name": "GitHub API",
  "type": "rest_api",
  "url": "https://api.github.com/repos/myorg/myrepo/stats/commit_activity",
  "credentials": {
    "type": "bearer",
    "token": "ghp_xxxxxxxxxxxxxxxxxxxx"
  }
}
```

With custom headers and pagination:

```json
{
  "name": "Internal Metrics API",
  "type": "rest_api",
  "url": "https://metrics.internal/api/weekly",
  "credentials": {
    "type": "header",
    "headers": {
      "X-API-Key": "secret-key",
      "X-Org-ID": "nexlayer"
    }
  },
  "pagination": {
    "type": "cursor",
    "param": "cursor",
    "limit": 100
  }
}
```

### CSV

```json
{
  "name": "Monthly Sales Export",
  "type": "csv",
  "fileId": "uploads/sales-2025-04.csv"
}
```

Upload via UI drag-and-drop or API:

```bash
curl -X POST http://192.168.68.111:8090/api/v1/workspaces/$WORKSPACE_ID/data-sources/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@./sales-2025-04.csv" \
  -F "name=Monthly Sales"
```

### Google Sheets

```json
{
  "name": "OKR Tracker",
  "type": "google_sheets",
  "fileId": "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgVE2upms",
  "credentials": {
    "type": "service_account",
    "serviceAccountJson": "{...}"
  }
}
```

---

## 5. Template Building

A template defines what sections appear in the report, what data feeds each section, and how the AI should narrate the content.

### Template Structure

```json
{
  "name": "Weekly Engineering Digest",
  "schedule": "0 9 * * 1",
  "sections": [ /* array of section objects */ ],
  "deliveryChannels": [ /* array of delivery config objects */ ]
}
```

### Section Types

#### `summary` — AI Narrative Summary

Generates a prose summary of the query results.

```json
{
  "type": "summary",
  "title": "This Week in Engineering",
  "dataSourceId": "ds_abc123",
  "query": "SELECT week, deploys, p95_ms, error_rate FROM weekly_stats ORDER BY week DESC LIMIT 4",
  "prompt": "Write a concise executive summary of engineering performance this week. Compare to the prior 3 weeks. Use plain English — no jargon."
}
```

#### `chart` — Rendered Chart with AI Description

```json
{
  "type": "chart",
  "title": "Deployment Frequency",
  "dataSourceId": "ds_abc123",
  "query": "SELECT date, count(*) as deploys FROM deployments GROUP BY date ORDER BY date DESC LIMIT 30",
  "chartConfig": {
    "type": "line",
    "x": "date",
    "y": "deploys",
    "color": "#6366f1"
  },
  "prompt": "Describe the deployment trend visible in this chart. Note any spikes or drops."
}
```

#### `anomaly` — AI Anomaly Detection

```json
{
  "type": "anomaly",
  "title": "Anomalies & Alerts",
  "dataSourceId": "ds_abc123",
  "query": "SELECT * FROM metrics WHERE created_at >= NOW() - INTERVAL '7 days'",
  "prompt": "Identify any statistical anomalies or concerning patterns. For each anomaly, explain: what happened, likely cause, and recommended action.",
  "sensitivity": "medium"
}
```

Sensitivity options: `low` | `medium` | `high`

#### `forecast` — Trend Prediction

```json
{
  "type": "forecast",
  "title": "Next 30-Day Forecast",
  "dataSourceId": "ds_abc123",
  "query": "SELECT date, value FROM kpi_daily ORDER BY date DESC LIMIT 90",
  "prompt": "Based on the historical data, forecast the next 30 days. Identify if we are on track for monthly targets.",
  "horizonDays": 30
}
```

#### `recommendation` — Actionable Recommendations

```json
{
  "type": "recommendation",
  "title": "Recommended Actions",
  "dataSourceId": "ds_abc123",
  "query": "SELECT * FROM weekly_summary LIMIT 1",
  "prompt": "Based on this week's metrics, provide 3 specific, actionable recommendations for the engineering team. Prioritize by impact."
}
```

#### `raw_table` — Data Table

```json
{
  "type": "raw_table",
  "title": "Top 10 Slowest Queries",
  "dataSourceId": "ds_abc123",
  "query": "SELECT query_text, avg_ms, call_count FROM pg_stat_statements ORDER BY avg_ms DESC LIMIT 10",
  "columns": ["query_text", "avg_ms", "call_count"]
}
```

### Python — Create Template Programmatically

```python
import requests

BASE = "http://192.168.68.111:8090/api/v1"

def create_devops_template(token: str, workspace_id: str, datasource_id: str) -> dict:
    template = {
        "name": "Weekly DevOps Report",
        "schedule": "0 9 * * 1",
        "sections": [
            {
                "type": "summary",
                "title": "Executive Summary",
                "dataSourceId": datasource_id,
                "query": """
                    SELECT
                        date_trunc('day', created_at) as day,
                        COUNT(*) FILTER (WHERE type='deploy') as deploys,
                        COUNT(*) FILTER (WHERE type='incident') as incidents,
                        AVG(duration_ms) as avg_duration_ms
                    FROM events
                    WHERE created_at >= NOW() - INTERVAL '7 days'
                    GROUP BY 1 ORDER BY 1
                """,
                "prompt": (
                    "Write a concise executive summary of this week's DevOps metrics. "
                    "Highlight deployment velocity, incident rate, and performance. "
                    "Compare to any available historical context."
                )
            },
            {
                "type": "anomaly",
                "title": "Anomalies & Alerts",
                "dataSourceId": datasource_id,
                "query": "SELECT * FROM events WHERE created_at >= NOW() - INTERVAL '7 days'",
                "prompt": "Detect any anomalies. For each one: describe what happened, the likely cause, and the recommended fix.",
                "sensitivity": "medium"
            },
            {
                "type": "recommendation",
                "title": "Action Items",
                "dataSourceId": datasource_id,
                "query": "SELECT * FROM weekly_summary ORDER BY week DESC LIMIT 2",
                "prompt": "Give 3 specific, high-priority action items based on this week's data."
            }
        ],
        "deliveryChannels": [
            {
                "type": "slack",
                "webhookUrl": "https://hooks.slack.com/services/T00/B00/xxx"
            },
            {
                "type": "email",
                "recipients": ["engineering@company.com"],
                "subject": "Weekly DevOps Report — {{report_date}}",
                "includePdf": True
            }
        ]
    }

    resp = requests.post(
        f"{BASE}/workspaces/{workspace_id}/templates",
        headers={"Authorization": f"Bearer {token}"},
        json=template
    )
    resp.raise_for_status()
    return resp.json()
```

---

## 6. Schedule Configuration

Schedules use standard **cron expressions** (`minute hour day month weekday`).

| Preset | Cron | Description |
|--------|------|-------------|
| Daily at 9am | `0 9 * * *` | Every day at 09:00 |
| Weekly Monday 9am | `0 9 * * 1` | Every Monday at 09:00 |
| Monthly 1st at 8am | `0 8 1 * *` | First day of month at 08:00 |
| Bi-weekly | `0 9 * * 1/2` | Every other Monday |
| Weekdays only | `0 8 * * 1-5` | Mon–Fri at 08:00 |
| Twice daily | `0 8,17 * * *` | 08:00 and 17:00 daily |
| Every 6 hours | `0 */6 * * *` | Every 6 hours |

**Named presets** (convenience aliases):

| Preset string | Equivalent cron |
|---------------|-----------------|
| `daily` | `0 9 * * *` |
| `weekly` | `0 9 * * 1` |
| `monthly` | `0 8 1 * *` |

```json
{
  "schedule": "weekly"
}
```

All schedule times are in the workspace timezone (default: UTC). Set timezone in Workspace Settings.

---

## 7. Delivery Channels

### Email

```json
{
  "type": "email",
  "recipients": ["cto@company.com", "team@company.com"],
  "subject": "{{report_name}} — {{report_date}}",
  "replyTo": "noreply@nexlayer.io",
  "includePdf": true
}
```

**Subject template variables:** `{{report_name}}`, `{{report_date}}`, `{{workspace_name}}`

### Slack

```json
{
  "type": "slack",
  "webhookUrl": "https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX"
}
```

The Slack message includes a summary card with a link to the full HTML report.

**Get a Slack Incoming Webhook:**
1. Go to `https://api.slack.com/apps` → Create App → Incoming Webhooks
2. Enable and add to channel
3. Copy the webhook URL

### Generic Webhook

PeriodAI POSTs report metadata + HTML to your endpoint.

```json
{
  "type": "webhook",
  "url": "https://your-system.internal/hooks/periodai",
  "method": "POST",
  "headers": {
    "Authorization": "Bearer your-internal-token",
    "X-Source": "periodai"
  },
  "includeHtml": true
}
```

**Payload shape:**

```json
{
  "event": "report.completed",
  "run_id": "run_abc123",
  "template_id": "tmpl_xyz",
  "template_name": "Weekly DevOps Report",
  "workspace_id": "ws_000",
  "generated_at": "2025-04-21T09:00:02Z",
  "html": "<html>...</html>",
  "report_url": "http://192.168.68.111:8090/api/v1/workspaces/ws_000/runs/run_abc123"
}
```

### API Storage

Stores the report in PeriodAI — retrieve it via API later. Useful for custom dashboards or agents.

```json
{
  "type": "api_storage"
}
```

Retrieve:

```bash
curl http://192.168.68.111:8090/api/v1/workspaces/$WORKSPACE_ID/runs/$RUN_ID \
  -H "Authorization: Bearer $TOKEN"
```

---

## 8. Running Reports

### Trigger Immediate Run

```bash
curl -X POST http://192.168.68.111:8090/api/v1/workspaces/$WORKSPACE_ID/templates/$TEMPLATE_ID/run \
  -H "Authorization: Bearer $TOKEN"
```

### List All Runs

```bash
curl http://192.168.68.111:8090/api/v1/workspaces/$WORKSPACE_ID/runs \
  -H "Authorization: Bearer $TOKEN"
```

### Get Run Result

```bash
# Get JSON metadata + rendered HTML
curl http://192.168.68.111:8090/api/v1/workspaces/$WORKSPACE_ID/runs/$RUN_ID \
  -H "Authorization: Bearer $TOKEN"
```

### Export Report

```bash
# Export as PDF
curl "http://192.168.68.111:8090/api/v1/workspaces/$WORKSPACE_ID/runs/$RUN_ID/export?format=pdf" \
  -H "Authorization: Bearer $TOKEN" \
  -o report.pdf

# Export as HTML
curl "http://192.168.68.111:8090/api/v1/workspaces/$WORKSPACE_ID/runs/$RUN_ID/export?format=html" \
  -H "Authorization: Bearer $TOKEN" \
  -o report.html
```

---

## 9. API Reference

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/auth/register` | Create account |
| `POST` | `/api/v1/auth/login` | Login → JWT tokens |
| `POST` | `/api/v1/auth/refresh` | Refresh access token |

### Workspaces

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/workspaces` | Create workspace |
| `GET` | `/api/v1/workspaces` | List my workspaces |
| `GET` | `/api/v1/workspaces/{id}` | Get workspace |
| `PATCH` | `/api/v1/workspaces/{id}` | Update settings |
| `GET` | `/api/v1/workspaces/{id}/members` | List members |
| `POST` | `/api/v1/workspaces/{id}/members` | Invite member |
| `DELETE` | `/api/v1/workspaces/{id}/members/{uid}` | Remove member |
| `POST` | `/api/v1/workspaces/{id}/api-keys` | Generate API key |

### Data Sources

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/workspaces/{id}/data-sources` | Add data source |
| `GET` | `/api/v1/workspaces/{id}/data-sources` | List data sources |
| `GET` | `/api/v1/workspaces/{id}/data-sources/{dsid}` | Get data source |
| `PATCH` | `/api/v1/workspaces/{id}/data-sources/{dsid}` | Update data source |
| `DELETE` | `/api/v1/workspaces/{id}/data-sources/{dsid}` | Delete data source |
| `POST` | `/api/v1/workspaces/{id}/data-sources/upload` | Upload CSV file |

### Templates

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/workspaces/{id}/templates` | Create template |
| `GET` | `/api/v1/workspaces/{id}/templates` | List templates |
| `GET` | `/api/v1/workspaces/{id}/templates/{tid}` | Get template |
| `PATCH` | `/api/v1/workspaces/{id}/templates/{tid}` | Update template |
| `DELETE` | `/api/v1/workspaces/{id}/templates/{tid}` | Delete template |
| `POST` | `/api/v1/workspaces/{id}/templates/{tid}/run` | Trigger immediate run |

### Runs

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/workspaces/{id}/runs` | List all runs |
| `GET` | `/api/v1/workspaces/{id}/runs/{rid}` | Get run result + HTML |
| `GET` | `/api/v1/workspaces/{id}/runs/{rid}/export?format=pdf\|html\|json` | Export report |

---

## 10. Agent API Access

Agents and CI/CD systems access PeriodAI using workspace-scoped API keys (`pai_...`) instead of user JWTs. This avoids managing user credentials in automation.

### Generate an API Key

```bash
curl -X POST http://192.168.68.111:8090/api/v1/workspaces/$WORKSPACE_ID/api-keys \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "CI Pipeline Key"}'

# Response
{
  "id": "key_abc123",
  "name": "CI Pipeline Key",
  "key": "pai_ws_abc123_xxxxxxxxxxxxxxxxxxxxxxxx",
  "workspace_id": "ws_000",
  "created_at": "2025-04-21T10:00:00Z"
}
```

### Use API Key in Requests

```bash
export PAI_KEY="pai_ws_abc123_xxxxxxxxxxxxxxxxxxxxxxxx"

# Trigger report run (no workspace ID needed — inferred from key)
curl -X POST http://192.168.68.111:8090/api/v1/templates/$TEMPLATE_ID/run \
  -H "Authorization: Bearer $PAI_KEY"

# Retrieve latest run
curl http://192.168.68.111:8090/api/v1/runs/latest \
  -H "Authorization: Bearer $PAI_KEY"
```

### Python Agent Example

```python
import requests

class PeriodAIAgent:
    """Lightweight PeriodAI client for agent use."""

    def __init__(self, api_key: str, base_url: str = "http://192.168.68.111:8090/api/v1"):
        self.base = base_url
        self.session = requests.Session()
        self.session.headers.update({"Authorization": f"Bearer {api_key}"})

    def trigger_report(self, template_id: str) -> dict:
        resp = self.session.post(f"{self.base}/templates/{template_id}/run")
        resp.raise_for_status()
        return resp.json()  # {"run_id": "...", "status": "running"}

    def get_run(self, run_id: str) -> dict:
        resp = self.session.get(f"{self.base}/runs/{run_id}")
        resp.raise_for_status()
        return resp.json()

    def wait_for_run(self, run_id: str, poll_interval: int = 5, timeout: int = 300) -> dict:
        import time
        deadline = time.time() + timeout
        while time.time() < deadline:
            run = self.get_run(run_id)
            if run["status"] in ("completed", "failed"):
                return run
            time.sleep(poll_interval)
        raise TimeoutError(f"Run {run_id} did not complete within {timeout}s")

    def export_report(self, run_id: str, fmt: str = "pdf") -> bytes:
        resp = self.session.get(f"{self.base}/runs/{run_id}/export", params={"format": fmt})
        resp.raise_for_status()
        return resp.content


# Usage
agent = PeriodAIAgent(api_key="pai_ws_abc123_xxxx")
run = agent.trigger_report("tmpl_devops_weekly")
result = agent.wait_for_run(run["run_id"])
print(f"Report status: {result['status']}")
if result["status"] == "completed":
    pdf = agent.export_report(result["id"], fmt="pdf")
    with open("weekly_report.pdf", "wb") as f:
        f.write(pdf)
```

---

## 11. Integration Examples

### PeriodAI + ModelRouter

ModelRouter is PeriodAI's LLM backend. Configure which provider and model powers each workspace's reports.

**Set at workspace creation:**

```json
{
  "name": "Engineering Analytics",
  "slug": "eng-analytics",
  "llm_provider": "anthropic",
  "llm_model": "claude-sonnet-4-20250514"
}
```

**Switch to Gemini:**

```bash
curl -X PATCH http://192.168.68.111:8090/api/v1/workspaces/$WORKSPACE_ID \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "llm_provider": "gemini",
    "llm_model": "gemini-2.5-pro"
  }'
```

**Use local Ollama (air-gapped):**

```bash
curl -X PATCH http://192.168.68.111:8090/api/v1/workspaces/$WORKSPACE_ID \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "llm_provider": "ollama",
    "llm_model": "llama3.3:70b",
    "ollama_base_url": "http://gpu-server.internal:11434"
  }'
```

All requests route through [ModelRouter](../ModelRouter) which handles provider failover, cost tracking, and rate limiting. Monitor LLM spend per report in [WatchGrid](../watchgrid).

---

### PeriodAI + AgentVault

Store database passwords and API credentials in [AgentVault](../AgentVault) rather than in PeriodAI config. PeriodAI fetches secrets at run time using vault references.

**Store secret in AgentVault:**

```bash
curl -X POST http://192.168.68.111:8200/api/v1/secrets \
  -H "Authorization: Bearer $VAULT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "key": "prod-db-password",
    "value": "super-secret-db-pass",
    "tags": ["database", "production"]
  }'
```

**Reference it in PeriodAI data source:**

```json
{
  "name": "Production DB",
  "type": "postgresql",
  "connectionString": "postgresql://reporter:{agentVaultRef:prod-db-password}@db.internal:5432/prod"
}
```

PeriodAI resolves `{agentVaultRef:key}` tokens at run time, keeping credentials out of the database.

**Python helper:**

```python
import requests

def create_datasource_with_vault_ref(token: str, workspace_id: str, vault_key: str) -> dict:
    """Create a PeriodAI data source where the DB password lives in AgentVault."""
    payload = {
        "name": "Production PostgreSQL",
        "type": "postgresql",
        "connectionString": f"postgresql://reporter:{{agentVaultRef:{vault_key}}}@db.internal:5432/prod"
    }
    resp = requests.post(
        f"http://192.168.68.111:8090/api/v1/workspaces/{workspace_id}/data-sources",
        headers={"Authorization": f"Bearer {token}"},
        json=payload
    )
    resp.raise_for_status()
    return resp.json()
```

---

### PeriodAI + FlowMesh

[FlowMesh](../flowmesh) pipelines can trigger PeriodAI report runs using the **WEBHOOK** node.

**FlowMesh node configuration:**

```json
{
  "nodeType": "WEBHOOK",
  "name": "Trigger PeriodAI Report",
  "config": {
    "method": "POST",
    "url": "http://192.168.68.111:8090/api/v1/templates/{{template_id}}/run",
    "headers": {
      "Authorization": "Bearer pai_ws_abc123_xxxx",
      "Content-Type": "application/json"
    }
  }
}
```

**Example pipeline: Generate report after nightly ETL completes**

```json
{
  "name": "Nightly Analytics Pipeline",
  "nodes": [
    {
      "id": "etl",
      "type": "SCRIPT",
      "name": "Run ETL",
      "config": { "command": "python /jobs/etl_daily.py" }
    },
    {
      "id": "report",
      "type": "WEBHOOK",
      "name": "Trigger PeriodAI",
      "config": {
        "url": "http://192.168.68.111:8090/api/v1/templates/tmpl_daily_digest/run",
        "method": "POST",
        "headers": { "Authorization": "Bearer pai_ws_abc123_xxxx" }
      },
      "dependsOn": ["etl"]
    }
  ]
}
```

PeriodAI generates and delivers the report — your pipeline moves on.

---

### PeriodAI + WatchGrid

[WatchGrid](../watchgrid) monitors LLM token costs per report run. Every time PeriodAI calls ModelRouter, costs are tagged and visible in WatchGrid.

**View costs in WatchGrid:**

```bash
# LLM costs for all PeriodAI runs this month
curl "http://192.168.68.111:9000/api/v1/costs?service=periodai&period=month" \
  -H "Authorization: Bearer $WATCHGRID_TOKEN"
```

**Response:**

```json
{
  "service": "periodai",
  "period": "2025-04",
  "total_usd": 4.23,
  "by_template": {
    "Weekly DevOps Report": { "runs": 4, "tokens": 42000, "usd": 1.68 },
    "Monthly Exec Summary":  { "runs": 1, "tokens": 18000, "usd": 0.72 }
  }
}
```

Set cost alerts in WatchGrid to notify when a single report run exceeds a threshold (useful for catching runaway anomaly detection sections on large datasets).

---

### PeriodAI + BrainVault

After a report run completes, key insights can be pushed to [BrainVault](../BrainVault) as personal notes — searchable and linkable from your knowledge base.

```python
import requests
import json

PERIODAI = "http://192.168.68.111:8090/api/v1"
BRAINVAULT = "http://192.168.68.111:8500/api/v1"

def push_report_insights_to_brainvault(
    pai_key: str,
    bv_token: str,
    workspace_id: str,
    run_id: str,
    notebook_id: str
):
    # Fetch the run result from PeriodAI
    run = requests.get(
        f"{PERIODAI}/workspaces/{workspace_id}/runs/{run_id}",
        headers={"Authorization": f"Bearer {pai_key}"}
    ).json()

    # Extract key insights from the report sections
    sections = run.get("sections", [])
    insights = []
    for section in sections:
        if section["type"] in ("summary", "anomaly", "recommendation"):
            insights.append(f"## {section['title']}\n\n{section['content']}")

    note_content = "\n\n---\n\n".join(insights)

    # Create a note in BrainVault
    note = {
        "title": f"Report: {run['template_name']} — {run['generated_at'][:10]}",
        "content": note_content,
        "tags": ["report", "periodai", run["template_name"].lower().replace(" ", "-")],
        "notebookId": notebook_id
    }

    resp = requests.post(
        f"{BRAINVAULT}/notes",
        headers={"Authorization": f"Bearer {bv_token}", "Content-Type": "application/json"},
        json=note
    )
    resp.raise_for_status()
    print(f"Insight note created: {resp.json()['id']}")
```

---

## 12. Complete Example: Weekly DevOps Metrics Report

This end-to-end example creates a production-ready weekly DevOps report:
- **Source:** PostgreSQL `metrics` database
- **Sections:** Summary, Anomaly detection, Recommendations
- **Schedule:** Every Monday at 9am
- **Delivery:** Slack #eng-reports channel

```python
#!/usr/bin/env python3
"""
Weekly DevOps metrics report — full setup script.

Prerequisites:
  - PeriodAI running at http://192.168.68.111:8090
  - PostgreSQL metrics DB accessible
  - Slack incoming webhook created
"""

import requests
import json

BASE = "http://192.168.68.111:8090/api/v1"

def setup_devops_report(
    email: str,
    password: str,
    pg_conn: str,
    slack_webhook: str
) -> dict:

    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})

    # 1. Login
    r = s.post(f"{BASE}/auth/login", json={"email": email, "password": password})
    r.raise_for_status()
    token = r.json()["access_token"]
    s.headers.update({"Authorization": f"Bearer {token}"})
    print("✓ Authenticated")

    # 2. Create workspace
    r = s.post(f"{BASE}/workspaces", json={
        "name": "DevOps Analytics",
        "slug": "devops-analytics",
        "llm_provider": "anthropic",
        "llm_model": "claude-sonnet-4-20250514"
    })
    r.raise_for_status()
    ws_id = r.json()["id"]
    print(f"✓ Workspace created: {ws_id}")

    # 3. Add PostgreSQL data source
    r = s.post(f"{BASE}/workspaces/{ws_id}/data-sources", json={
        "name": "Metrics DB",
        "type": "postgresql",
        "connectionString": pg_conn
    })
    r.raise_for_status()
    ds_id = r.json()["id"]
    print(f"✓ Data source created: {ds_id}")

    # 4. Create the weekly template
    template = {
        "name": "Weekly DevOps Report",
        "schedule": "0 9 * * 1",  # Every Monday 09:00 UTC
        "sections": [
            {
                "type": "summary",
                "title": "Weekly Summary",
                "dataSourceId": ds_id,
                "query": """
                    SELECT
                        date_trunc('day', ts)::date AS day,
                        SUM(deploys)        AS deploys,
                        SUM(incidents)      AS incidents,
                        ROUND(AVG(p95_ms))  AS p95_latency_ms,
                        ROUND(AVG(error_rate_pct), 2) AS error_rate_pct
                    FROM devops_metrics
                    WHERE ts >= NOW() - INTERVAL '7 days'
                    GROUP BY 1
                    ORDER BY 1
                """,
                "prompt": (
                    "You are a senior SRE writing a weekly digest for engineering leadership. "
                    "Summarize deployment frequency, incident rate, p95 latency, and error rate for this week. "
                    "Highlight the most important change vs. last week and its significance. Keep it to 3 paragraphs."
                )
            },
            {
                "type": "chart",
                "title": "Deployment Frequency",
                "dataSourceId": ds_id,
                "query": """
                    SELECT date_trunc('day', ts)::date AS day, SUM(deploys) AS deploys
                    FROM devops_metrics
                    WHERE ts >= NOW() - INTERVAL '28 days'
                    GROUP BY 1 ORDER BY 1
                """,
                "chartConfig": {"type": "bar", "x": "day", "y": "deploys"},
                "prompt": "Describe the deployment frequency trend over the past 4 weeks."
            },
            {
                "type": "anomaly",
                "title": "Anomalies & Alerts",
                "dataSourceId": ds_id,
                "query": """
                    SELECT ts, service, metric_name, value, baseline_value,
                           ROUND(((value - baseline_value) / NULLIF(baseline_value,0)) * 100, 1) AS pct_deviation
                    FROM devops_metrics_raw
                    WHERE ts >= NOW() - INTERVAL '7 days'
                    ORDER BY ABS(value - baseline_value) DESC
                """,
                "prompt": (
                    "Identify any metrics that are significantly outside their normal range. "
                    "For each anomaly: name the metric, state the deviation, explain the most likely cause, "
                    "and suggest a concrete remediation step."
                ),
                "sensitivity": "medium"
            },
            {
                "type": "recommendation",
                "title": "Action Items for Next Week",
                "dataSourceId": ds_id,
                "query": "SELECT * FROM weekly_devops_summary ORDER BY week DESC LIMIT 2",
                "prompt": (
                    "Based on this week's metrics, provide exactly 3 action items for the DevOps team. "
                    "Each item must be specific, measurable, and achievable in one sprint. "
                    "Format as a numbered list: <action> — <expected outcome>."
                )
            }
        ],
        "deliveryChannels": [
            {
                "type": "slack",
                "webhookUrl": slack_webhook
            },
            {
                "type": "api_storage"  # also available via API for dashboards
            }
        ]
    }

    r = s.post(f"{BASE}/workspaces/{ws_id}/templates", json=template)
    r.raise_for_status()
    tmpl_id = r.json()["id"]
    print(f"✓ Template created: {tmpl_id}")

    # 5. Trigger a test run
    r = s.post(f"{BASE}/workspaces/{ws_id}/templates/{tmpl_id}/run")
    r.raise_for_status()
    run = r.json()
    print(f"✓ Test run triggered: {run['run_id']} (check Slack in ~60s)")

    return {"workspace_id": ws_id, "template_id": tmpl_id, "run_id": run["run_id"]}


if __name__ == "__main__":
    result = setup_devops_report(
        email="you@company.com",
        password="yourpassword",
        pg_conn="postgresql://reporter:secret@db.internal:5432/metrics",
        slack_webhook="https://hooks.slack.com/services/T00/B00/xxx"
    )
    print("\nSetup complete:")
    print(json.dumps(result, indent=2))
```

**What happens every Monday at 9am:**

1. PeriodAI scheduler fires, starts a report run
2. Queries PostgreSQL for last 7 days of metrics
3. Passes data to ModelRouter → Anthropic Claude
4. Claude writes each section as narrative text
5. Anomaly section automatically flags any metric > 2σ from baseline
6. Report is assembled as formatted HTML
7. Slack message posted to `#eng-reports` with summary card
8. Full report stored in `api_storage` for dashboard access

**To retrieve the latest report programmatically:**

```bash
# Get most recent run
LATEST_RUN=$(curl -s "http://192.168.68.111:8090/api/v1/workspaces/$WS_ID/runs?limit=1" \
  -H "Authorization: Bearer $TOKEN" | python3 -c "import sys,json; print(json.load(sys.stdin)['runs'][0]['id'])")

# Export as PDF
curl "http://192.168.68.111:8090/api/v1/workspaces/$WS_ID/runs/$LATEST_RUN/export?format=pdf" \
  -H "Authorization: Bearer $TOKEN" -o weekly-devops-report.pdf
```
