# 01 — Product Overview

## Vision

PeriodAI automates the full reporting cycle. Teams stop manually pulling data and writing summaries. Instead, they configure once and receive decision-ready reports on schedule — with AI-written narratives, anomaly explanations, trend forecasts, and recommended actions.

**Tagline:** `// automated intelligence reports — from raw data to decision-ready insights on autopilot`

---

## Problem

- Teams spend hours per week manually pulling data and writing summaries
- BI dashboards show data but do not explain it — no narrative, no recommendations
- Alerts fire but context around anomalies is missing
- Monthly reports miss weekly patterns; report cadence is inconsistent
- Different teams need different views of the same data, requiring manual reformatting

---

## Core Concepts

| Concept | Definition |
|---------|------------|
| **Workspace** | Isolated tenant. All sources, templates, runs, and API keys belong to a workspace. |
| **DataSource** | A configured connection: database, REST API, CSV/XLSX file, or Google Sheets. Credentials encrypted at rest. |
| **ReportTemplate** | Defines what data to fetch, which analysis sections to generate, the schedule, and delivery channels. |
| **Section** | A building block of a report. Each section has a type, a data query, and an LLM prompt. |
| **Schedule** | A cron expression or preset (daily/weekly/monthly) controlling when a report runs. |
| **Run** | A single execution of a template — fetch data → LLM pipeline → render → deliver → store. |
| **Delivery Channel** | Where the completed report is sent: email, Slack, webhook, or API storage. |

---

## User Flow

```
1. Log in to dashboard
2. Add a Data Source (connection string, API key, or file)
3. Create a Report Template
   └── Pick data source(s)
   └── Add sections (summary, chart, anomaly, etc.)
   └── Write LLM prompt per section
4. Set schedule (daily Mon 08:00 UTC) and delivery channels (email + Slack)
5. PeriodAI runs automatically at scheduled time:
   └── Fetch data from source
   └── Run LLM pipeline on each section
   └── Render HTML report + charts
   └── Deliver to all channels
   └── Store run record in history
6. Team receives report in inbox / Slack
7. Agents and integrations access report history via REST API
```

---

## Target Users

- **DevOps / infra teams** — weekly server health and incident summaries
- **Product managers** — daily/weekly product metrics with AI interpretation
- **Sales teams** — pipeline and conversion trend reports
- **Operations teams** — KPI reports replacing manual spreadsheet work
- **AI agents** — programmatic access to report history and on-demand runs

---

## Differentiators vs Traditional BI

| Feature | PeriodAI | Traditional BI |
|---------|----------|----------------|
| Output type | Narrative + charts | Charts only |
| Anomaly explanation | AI-written reason | Alert only |
| Setup time | Minutes | Days / weeks |
| Delivery | Email, Slack, webhook | Dashboard login required |
| Agent accessible | Yes, REST API | No |
| Custom LLM | Claude, Gemini, Ollama | N/A |
| Runs without human | Yes, fully automated | No |

---

## Out of Scope (v1)

These are explicitly **not** in v1. Do not implement them:

- Real-time streaming / event-triggered reports
- Native mobile app
- White-label / custom domain
- Data write-back from report actions
- Report comments / annotations
- Community template marketplace
