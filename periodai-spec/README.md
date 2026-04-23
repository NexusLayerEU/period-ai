# PeriodAI — Agent Build Instructions

**Company:** Nexlayer  
**Product:** PeriodAI — Automated Intelligence Reporting Engine  
**Version:** 1.0.0  
**Status:** Ready for Development

---

## What You Are Building

PeriodAI is a backend service + web dashboard that:
1. Connects to data sources (databases, REST APIs, spreadsheets)
2. Runs AI-powered analysis on a schedule (daily, weekly, monthly, cron)
3. Generates narrative reports (not just charts — written summaries, anomaly explanations, forecasts)
4. Delivers reports via email, Slack, webhook, or API

**Read all spec files before writing any code.**

---

## Spec Files — Read in This Order

| # | File | Contents |
|---|------|----------|
| 1 | `01-overview.md` | Product vision, concepts, user flow |
| 2 | `02-tech-stack.md` | Technology decisions, project structure |
| 3 | `03-data-models.md` | Database schema, entity definitions |
| 4 | `04-api-spec.md` | All REST API endpoints with request/response shapes |
| 5 | `05-llm-pipeline.md` | LLM processing pipeline, section types, prompt templates |
| 6 | `06-scheduler.md` | Scheduling engine, Celery setup, job execution |
| 7 | `07-delivery.md` | Email, Slack, webhook, PDF delivery implementations |
| 8 | `08-frontend.md` | React dashboard pages and component spec |
| 9 | `09-milestones.md` | MVP scope, build order, acceptance criteria |

---

## Build Order

```
Phase 1 — Backend Core
  1. Project scaffold (FastAPI + Docker Compose)
  2. Database models + Alembic migrations
  3. Auth (JWT + workspaces)
  4. DataSource CRUD + DB connector
  5. ReportTemplate CRUD
  6. Celery + Redis scheduler
  7. LLM pipeline (Summary section only)
  8. Email delivery

Phase 2 — Full Features
  9. All 8 section types
  10. REST API connector for data sources
  11. Chart rendering → PNG
  12. Slack + webhook delivery
  13. PDF export

Phase 3 — Frontend
  14. React app scaffold
  15. Dashboard, Sources, Templates, Runs pages
  16. Report viewer

Phase 4 — Production
  17. Multi-workspace + roles
  18. API key management
  19. Usage tracking
  20. Kubernetes Helm chart
```

---

## Key Constraints

- **Never write raw SQL with string interpolation** — always use parameterized queries
- **Credentials encrypted at rest** — AES-256 for data source configs
- **All LLM calls are async** — use `asyncio` and Celery tasks
- **OpenAPI spec auto-generated** — FastAPI handles this, ensure all endpoints have proper type annotations
- **Token usage tracked per run** — store in `ReportRun.total_tokens` and per-section in run metadata
