# 04 — REST API Specification

## Base URL

```
Development:  http://localhost:8000/api/v1
Production:   https://api.periodai.io/api/v1
```

## Authentication

All endpoints (except `/auth/*` and `/health`) require:

```
Authorization: Bearer <jwt_access_token>
```

API key authentication (for agents/integrations):

```
Authorization: Bearer pai_<workspace_key>
```

API keys are resolved to a workspace at request time. They do not have user-level permissions — they act as workspace members with `member` role.

---

## Auth Endpoints

### POST /auth/register
Create a new user account.

**Request:**
```json
{
  "email": "thomas@nexlayer.io",
  "password": "min-8-chars",
  "full_name": "Thomas"
}
```

**Response 201:**
```json
{
  "id": "uuid",
  "email": "thomas@nexlayer.io",
  "full_name": "Thomas",
  "created_at": "2026-04-11T08:00:00Z"
}
```

### POST /auth/login
Get JWT tokens.

**Request:**
```json
{
  "email": "thomas@nexlayer.io",
  "password": "secret"
}
```

**Response 200:**
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

### POST /auth/refresh
**Request:** `{ "refresh_token": "eyJ..." }`  
**Response:** New `access_token` + `refresh_token`

---

## Workspace Endpoints

### POST /workspaces
Create a workspace. Caller becomes owner.

**Request:**
```json
{
  "name": "Nexlayer Analytics",
  "slug": "nexlayer",
  "llm_provider": "anthropic",
  "llm_model": "claude-sonnet-4-20250514"
}
```

**Response 201:** Full workspace object.

### GET /workspaces
List workspaces the authenticated user belongs to.

### GET /workspaces/{workspace_id}
Get workspace details.

### PATCH /workspaces/{workspace_id}
Update workspace settings (owner/admin only).  
Patchable: `name`, `llm_provider`, `llm_model`, `ollama_base_url`

### GET /workspaces/{workspace_id}/members
List members and their roles.

### POST /workspaces/{workspace_id}/members
Invite a member.  
**Request:** `{ "email": "...", "role": "member" }`

### DELETE /workspaces/{workspace_id}/members/{user_id}
Remove a member (owner/admin only).

---

## Data Source Endpoints

All source endpoints are scoped to a workspace via the JWT workspace context or `X-Workspace-ID` header.

### GET /sources
List all data sources in the workspace.

**Response 200:**
```json
{
  "items": [
    {
      "id": "uuid",
      "name": "Production DB",
      "type": "postgres",
      "test_status": "ok",
      "last_tested_at": "2026-04-11T07:00:00Z",
      "created_at": "2026-04-01T00:00:00Z"
    }
  ],
  "total": 1
}
```

### POST /sources
Create a data source.

**Request:**
```json
{
  "name": "Production DB",
  "type": "postgres",
  "config": {
    "host": "db.example.com",
    "port": 5432,
    "database": "analytics",
    "username": "readonly",
    "password": "secret",
    "ssl": true
  }
}
```

Config is encrypted server-side before storage. **Never return decrypted config in any response.**

**Response 201:**
```json
{
  "id": "uuid",
  "name": "Production DB",
  "type": "postgres",
  "test_status": null,
  "last_tested_at": null,
  "created_at": "..."
}
```

### GET /sources/{source_id}
Get source details. **Never include decrypted config.**

### PATCH /sources/{source_id}
Update name or config.

### DELETE /sources/{source_id}
Delete source. Fail with `409 Conflict` if source is used by any active template.

### POST /sources/{source_id}/test
Test connectivity. Runs synchronously (timeout 10s).

**Response 200:**
```json
{
  "status": "ok",
  "message": "Connected successfully. PostgreSQL 16.2",
  "tested_at": "2026-04-11T08:00:00Z"
}
```

**Response 422 (failure):**
```json
{
  "status": "error",
  "message": "Connection refused: db.example.com:5432",
  "tested_at": "..."
}
```

---

## Report Template Endpoints

### GET /templates
List templates in the workspace.

**Query params:**
- `is_active` — boolean filter
- `limit` — default 20, max 100
- `offset` — pagination

### POST /templates
Create a template.

**Request:**
```json
{
  "name": "Weekly Revenue Report",
  "description": "Monday morning revenue summary for the team",
  "source_ids": ["uuid-of-source"],
  "sections": [
    {
      "id": "sec-1",
      "type": "summary",
      "title": "Executive Summary",
      "position": 0,
      "source_id": "uuid-of-source",
      "query": "SELECT date, revenue FROM sales WHERE date >= :start_date",
      "query_params": { "start_date": "last_7_days" },
      "llm_prompt": "Summarize revenue trends. Highlight week-over-week changes. Be concise.",
      "output_format": "markdown"
    },
    {
      "id": "sec-2",
      "type": "bar_chart",
      "title": "Daily Revenue",
      "position": 1,
      "source_id": "uuid-of-source",
      "query": "SELECT date, revenue FROM sales WHERE date >= :start_date ORDER BY date",
      "query_params": { "start_date": "last_7_days" },
      "chart_config": { "x": "date", "y": "revenue", "color": "#FF8C42", "type": "bar" }
    }
  ],
  "schedule": "0 8 * * 1",
  "timezone": "Europe/Tirane",
  "delivery_channels": [
    {
      "type": "email",
      "recipients": ["team@nexlayer.io"],
      "subject": "Weekly Revenue Report — {{report_date}}"
    },
    {
      "type": "slack",
      "channel_id": "C0123456789",
      "bot_token_encrypted": "..."
    }
  ],
  "is_active": true
}
```

**Response 201:** Full template object.

### GET /templates/{template_id}
Get template with all sections and delivery config.

### PUT /templates/{template_id}
Full update (replace all fields).

### PATCH /templates/{template_id}
Partial update. Supports: `name`, `description`, `sections`, `schedule`, `timezone`, `delivery_channels`, `is_active`

### DELETE /templates/{template_id}
Delete template and all associated runs.

### POST /templates/{template_id}/run
Trigger a manual run immediately.

**Response 202:**
```json
{
  "run_id": "uuid",
  "status": "queued",
  "message": "Report generation queued. Poll GET /runs/{run_id} for status."
}
```

---

## Report Run Endpoints

### GET /runs
List runs in the workspace.

**Query params:**
- `template_id` — filter by template
- `status` — filter: `queued|running|completed|failed`
- `from_date` / `to_date` — ISO date strings
- `limit` — default 20, max 100
- `offset`

**Response 200:**
```json
{
  "items": [
    {
      "id": "uuid",
      "template_id": "uuid",
      "template_name": "Weekly Revenue Report",
      "triggered_by": "schedule",
      "status": "completed",
      "started_at": "2026-04-07T08:00:02Z",
      "completed_at": "2026-04-07T08:00:34Z",
      "duration_ms": 31840,
      "total_tokens": 2847,
      "total_cost_usd": 0.0142
    }
  ],
  "total": 47
}
```

### GET /runs/{run_id}
Full run details including section metadata.

### GET /runs/{run_id}/output
Get the report output.

**Query param:** `format` — `html` (default) | `json` | `markdown`

**Response 200 (html):**
```
Content-Type: text/html
<full rendered HTML report>
```

**Response 200 (json):**
```json
{
  "run_id": "uuid",
  "template_name": "Weekly Revenue Report",
  "generated_at": "2026-04-07T08:00:34Z",
  "period": { "start": "2026-03-31", "end": "2026-04-06" },
  "sections": [
    {
      "id": "sec-1",
      "type": "summary",
      "title": "Executive Summary",
      "content": "Revenue grew 12% week-over-week...",
      "data": [...]
    }
  ]
}
```

### GET /runs/{run_id}/pdf
Download PDF. Returns binary PDF or 404 if not yet generated.

---

## API Key Endpoints

### GET /api-keys
List API keys in the workspace (prefix + metadata only, never full key).

### POST /api-keys
Create an API key.

**Request:** `{ "name": "Agent Integration" }`

**Response 201:**
```json
{
  "id": "uuid",
  "name": "Agent Integration",
  "key": "pai_k8x2abc123...",   // ONLY time the full key is returned
  "key_prefix": "pai_k8x2",
  "created_at": "..."
}
```

### DELETE /api-keys/{key_id}
Revoke a key immediately.

---

## Usage Endpoint

### GET /usage
Token and cost summary for the workspace.

**Query params:** `from_date`, `to_date`

**Response 200:**
```json
{
  "period": { "from": "2026-04-01", "to": "2026-04-11" },
  "total_tokens": 48291,
  "total_cost_usd": 0.241,
  "by_template": [
    {
      "template_id": "uuid",
      "template_name": "Weekly Revenue Report",
      "runs": 2,
      "tokens": 5694,
      "cost_usd": 0.0285
    }
  ],
  "by_day": [
    { "date": "2026-04-07", "tokens": 2847, "cost_usd": 0.0142 }
  ]
}
```

---

## Health Endpoint

### GET /health

```json
{
  "status": "ok",
  "checks": {
    "database": "ok",
    "redis": "ok",
    "llm_provider": "ok"
  },
  "version": "1.0.0"
}
```

---

## Error Response Format

All errors follow this shape:

```json
{
  "error": {
    "code": "TEMPLATE_NOT_FOUND",
    "message": "Report template uuid not found in this workspace",
    "details": {}
  }
}
```

**Standard HTTP status codes:**

| Code | Meaning |
|------|---------|
| 400 | Bad request / validation error |
| 401 | Missing or invalid token |
| 403 | Authenticated but insufficient permissions |
| 404 | Resource not found |
| 409 | Conflict (e.g. deleting a source still in use) |
| 422 | Unprocessable entity (FastAPI validation) |
| 429 | Rate limited |
| 500 | Internal server error |

---

## Rate Limits

| Tier | Limit |
|------|-------|
| Free | 60 requests / minute per workspace |
| Growth | 300 requests / minute |
| Enterprise | Custom |

Rate limit headers returned on every response:
```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 54
X-RateLimit-Reset: 1712829600
```

---

## OpenAPI

FastAPI generates the OpenAPI 3.1 spec automatically.  
Available at: `GET /api/openapi.json`  
Interactive docs: `GET /docs` (dev only)

**Requirements for good spec generation:**
- All Pydantic models must have `model_config = ConfigDict(json_schema_extra={"example": {...}})`
- All router functions must have docstrings (used as operation descriptions)
- All response models explicitly declared with `response_model=`
