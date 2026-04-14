# 09 — Build Milestones & Acceptance Criteria

## Phase 1 — MVP (Week 1–2)

**Goal:** One working end-to-end report run delivered by email.

### Tasks in Build Order

```
[ ] 1. Project scaffold
      - FastAPI app with health endpoint
      - Docker Compose (postgres, redis, api, worker, beat)
      - Alembic with initial migration
      - Makefile commands (up, down, migrate, test, lint)

[ ] 2. Database models
      - Workspace, User, WorkspaceMember
      - DataSource, ReportTemplate, ReportRun, Delivery, ApiKey
      - Run: alembic upgrade head — verify all tables created

[ ] 3. Auth endpoints
      - POST /auth/register
      - POST /auth/login  →  JWT access + refresh tokens
      - POST /auth/refresh
      - GET /auth/me  →  current user
      - Middleware: require_auth dependency

[ ] 4. Workspace endpoints
      - POST /workspaces
      - GET /workspaces
      - GET /workspaces/:id
      - PATCH /workspaces/:id (owner only)

[ ] 5. DataSource CRUD
      - POST /sources (encrypt config before save)
      - GET /sources
      - GET /sources/:id (never return decrypted config)
      - PATCH /sources/:id
      - DELETE /sources/:id
      - POST /sources/:id/test (PostgreSQL connector only for MVP)

[ ] 6. PostgreSQL connector
      - app/connectors/postgres.py
      - connect, test, query(sql, params) → list[dict]
      - Parameterized queries only — no string interpolation

[ ] 7. ReportTemplate CRUD
      - POST /templates
      - GET /templates
      - GET /templates/:id
      - PUT /templates/:id
      - PATCH /templates/:id
      - DELETE /templates/:id
      - Validate cron expression on save (croniter)
      - Register/unregister in RedBeat on create/update/delete

[ ] 8. Celery + Redis + RedBeat setup
      - celery_app.py with RedBeat scheduler
      - run_report_task task
      - Beat reads templates from DB via RedBeat
      - Verify: create template → beat picks up schedule → task fires

[ ] 9. LLM pipeline — Summary section only
      - AnthropicProvider (claude-sonnet-4-20250514)
      - Fetcher: fetch rows, resolve date params
      - SummaryHandler: build prompt, call LLM, return SectionResult
      - PipelineRunner: fetch → generate → render (basic HTML)
      - ReportRun status updates (queued → running → completed/failed)
      - Store output_html and output_json

[ ] 10. Email delivery
      - SendGrid integration
      - EmailDelivery.send() with HTML wrapping
      - Attach PDF = False for MVP
      - Delivery record created per send

[ ] 11. POST /templates/:id/run (manual trigger)
[ ] 12. GET /runs and GET /runs/:id
[ ] 13. GET /runs/:id/output?format=html|json
```

### MVP Acceptance Criteria

All of these must pass before moving to Phase 2:

- [ ] `POST /auth/register` + `POST /auth/login` returns valid JWT
- [ ] Can create a workspace via API
- [ ] Can add a PostgreSQL data source and `POST /sources/:id/test` returns `{ "status": "ok" }`
- [ ] Can create a report template with one `summary` section and a weekly cron schedule
- [ ] Celery Beat fires the task at the correct scheduled time (verify with a 1-minute cron in testing)
- [ ] Task fetches data from PostgreSQL, calls Anthropic API, produces HTML output
- [ ] `ReportRun.status` transitions: `queued` → `running` → `completed`
- [ ] Email delivered to recipient with rendered HTML content (check SendGrid activity feed)
- [ ] `GET /runs/:id/output?format=html` returns the report HTML
- [ ] `GET /health` returns `{ "status": "ok" }` with all checks passing

---

## Phase 2 — Alpha (Week 3–4)

**Goal:** All section types, all source connectors, Slack delivery.

```
[ ] All 8 section types implemented and rendering correctly
      - summary, metric_cards, trend, bar_chart, line_chart, anomaly, forecast, insight, actions
[ ] Chart rendering: Plotly → PNG → embedded in HTML (kaleido)
[ ] REST API connector (app/connectors/rest_api.py)
      - GET/POST support
      - Auth: none, api_key, bearer, basic
      - Pagination: offset, cursor, page
[ ] CSV/XLSX connector (app/connectors/csv_file.py)
[ ] Slack delivery (app/delivery/slack.py)
      - Block Kit message with summary section
      - Action buttons (View Report)
[ ] Webhook delivery (app/delivery/webhook.py)
      - HMAC-SHA256 signing
[ ] GET /runs (with filters: template_id, status, date range)
[ ] Google Gemini provider (app/llm/gemini.py)
[ ] Ollama provider (app/llm/ollama.py) with configurable base URL
[ ] Token usage tracking per section and per run
[ ] GET /usage endpoint
```

---

## Phase 3 — Frontend (Week 5–6)

**Goal:** Full React dashboard functional.

```
[ ] React + Vite + TypeScript scaffold
[ ] TailwindCSS dark theme configured
[ ] Auth pages: Login, Register
[ ] API client with JWT interceptors + refresh
[ ] Dashboard page (run stats, recent runs, upcoming schedules)
[ ] Sources page (list, add modal with type selector, test button)
[ ] Templates page (list, toggle active, run now)
[ ] Template Editor (multi-step: info → sections → schedule/delivery → save)
[ ] Runs page (list with filters, status badges, auto-refresh)
[ ] Report Viewer (HTML iframe, JSON view, PDF download)
[ ] Settings page (workspace config, members, API keys)
[ ] Usage page (charts, cost breakdown)
```

---

## Phase 4 — Production Ready (Week 7–8)

```
[ ] Multi-workspace scoping verified (no cross-workspace data leakage)
[ ] Role-based access: owner, admin, member permissions enforced
[ ] API key auth (pai_ prefix, bcrypt hash, workspace scoping)
[ ] PDF export: WeasyPrint HTML → PDF, stored (local or S3)
[ ] Google Sheets connector (app/connectors/google_sheets.py)
[ ] OWASP checklist:
      [ ] SQL injection: all queries parameterized — audit all connectors
      [ ] XSS: HTML output sanitized before rendering in frontend
      [ ] Auth: token expiry, refresh rotation, logout blacklist
      [ ] Rate limiting: slowapi on all endpoints
      [ ] CORS: configured for production domain only
[ ] Structured JSON logging (request_id, workspace_id on every line)
[ ] Prometheus metrics endpoint
[ ] Helm chart for Kubernetes
[ ] README with setup guide, environment variable reference
[ ] Full API documentation (auto-generated + manual examples)
[ ] Load test: 100 concurrent scheduled runs, no queue backlog > 60s
```

---

## Testing Strategy

```
backend/tests/
├── conftest.py          — pytest fixtures (test DB, async session, auth headers)
├── test_auth.py         — register, login, refresh, protected routes
├── test_sources.py      — CRUD, encryption, test connectivity
├── test_templates.py    — CRUD, cron validation, schedule registration
├── test_pipeline.py     — mock LLM, verify section outputs
├── test_runs.py         — trigger, poll status, fetch output
├── test_delivery.py     — mock SendGrid/Slack/webhook, verify calls
└── test_usage.py        — token aggregation
```

**Minimum coverage targets for MVP:**
- Auth: 100%
- Sources CRUD + encryption: 100%
- Templates CRUD: 90%
- Pipeline runner (mocked LLM): 80%

**Test database:** Use a separate `periodai_test` database. Reset with `alembic downgrade base && alembic upgrade head` in conftest.

---

## Known Risks & Mitigations

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| LLM timeout on large datasets | Medium | Cap data rows sent to LLM at 100; add 30s timeout per section |
| Celery Beat duplicate tasks (multiple instances) | High | Only ever run 1 Beat instance; enforce in Kubernetes with `replicas: 1` |
| Chart rendering fails (kaleido headless) | Medium | Run in Docker with chrome headless; fallback: skip chart, log warning |
| Slack rate limiting | Low | Add 1s delay between Slack API calls; catch 429 and retry |
| Large HTML report in email (>10MB) | Low | Cap email body at 5MB; if larger, send link-only email |
| Data source credentials leaked in logs | High | Scrub credentials from all log output; never log decrypted config |
