# 08 — Frontend Dashboard

## Tech Stack

- **React 18** + **TypeScript**
- **Vite** — build tool
- **TailwindCSS** — styling (dark theme, amber accent `#FF8C42`)
- **Recharts** — dashboard charts
- **React Query (TanStack Query)** — server state, caching, refetching
- **React Router v6** — routing
- **Axios** — HTTP client with auth interceptors
- **React Hook Form** — forms
- **Zod** — client-side validation

---

## Color System

```css
/* tailwind.config.ts — extend colors */
colors: {
  brand: {
    DEFAULT: "#FF8C42",
    light: "#FFF4EC",
    border: "#FFD4B0",
  },
  dark: {
    900: "#06070A",
    800: "#0D0F14",
    700: "#13161E",
    600: "#1A1D24",
  },
  muted: "#4A5060",
}
```

---

## App Routes

```
/login                  — Login page (public)
/register               — Register page (public)
/                       — Redirect to /dashboard
/dashboard              — Overview dashboard
/sources                — Data sources list
/sources/new            — Add data source
/sources/:id            — Edit data source
/templates              — Report templates list
/templates/new          — Create template (section builder)
/templates/:id          — Edit template
/runs                   — Run history
/runs/:id               — Report viewer
/settings               — Workspace settings + API keys
/usage                  — Token usage & cost dashboard
```

---

## Pages

### /dashboard — Overview

**Components:**
- `StatCard` × 4 — Total Runs (this month), Successful Runs, Avg Duration, Token Cost
- `RecentRuns` table — last 10 runs, columns: Template, Status, Triggered By, Duration, Time
- `UpcomingSchedules` list — next 5 scheduled runs with countdown
- `QuickActions` buttons — "+ New Template", "Run All Active", "View Usage"

**Data:** `GET /runs?limit=10`, `GET /usage`, `GET /templates?is_active=true`

**Auto-refresh:** Poll every 30s for run status updates.

---

### /sources — Data Sources

**Components:**
- `SourceCard` grid — name, type badge (colored), test status indicator, last tested time
- Empty state — "No sources yet. Add your first data source."
- `+ Add Source` button → opens `SourceModal`

**SourceModal (Add/Edit):**

```
Step 1: Source Type
  [ PostgreSQL ] [ MySQL ] [ REST API ] [ CSV/XLSX ] [ Google Sheets ]

Step 2: Connection Config
  (Form fields vary by type — see data models spec)
  
Step 3: Test & Save
  [ Test Connection ] → shows success/error inline
  [ Save ]
```

**Type-specific form fields:**

| Type | Fields |
|------|--------|
| postgres/mysql | host, port, database, username, password, SSL toggle |
| mssql | host, port, database, username, password, instance name |
| rest_api | base URL, auth type (none/api_key/bearer/basic), auth value, pagination config |
| csv/xlsx | file upload OR URL input |
| google_sheets | sheet ID, service account JSON upload |

---

### /templates — Report Templates

**Components:**
- `TemplateCard` — name, schedule (human-readable), last run status, active toggle, Edit/Delete/Run buttons
- Active toggle calls `PATCH /templates/:id { "is_active": bool }`
- "Run Now" button calls `POST /templates/:id/run` then redirects to `/runs/:new_run_id`

---

### /templates/new and /templates/:id — Template Editor

**This is the most complex page. Build as a multi-step form:**

```
Step 1: Basic Info
  - Name (required)
  - Description (optional)
  - Data Source(s) — multi-select from available sources

Step 2: Report Sections
  - Section list (drag to reorder)
  - "+ Add Section" button — opens section type picker modal
  - Each section card shows: type badge, title, collapse/expand, edit, delete

  Section Editor (expanded):
    - Title (text input)
    - Type (fixed after creation)
    - Data Source (select — from template's sources)
    - SQL Query (code editor textarea with monospace font)
    - Query Params (key-value pairs for date shortcuts)
    - LLM Prompt (large textarea with placeholder text)
    - Chart Config (shown only for bar_chart/line_chart sections)
      - X column, Y column, chart type, color picker

Step 3: Schedule & Delivery
  - Schedule:
    - Presets: [ Daily 8am ] [ Mon 8am ] [ Fri 8am ] [ 1st of Month ]
    - Custom cron expression toggle (shows input + human-readable preview)
    - Timezone selector (searchable dropdown)
  - Delivery Channels:
    - "+ Add Channel" → picks Email / Slack / Webhook
    - Email config: recipient list, subject template, PDF toggle
    - Slack config: bot token, channel ID, mention users
    - Webhook config: URL, secret, custom headers

Step 4: Preview & Save
  - Summary of all configuration
  - "Run Now after Saving" toggle
  - [ Save ] [ Save & Run ]
```

---

### /runs — Run History

**Components:**
- Filter bar: Template (dropdown), Status (dropdown), Date range picker
- Runs table: columns — Template, Status badge, Triggered By, Duration, Tokens, Cost, Time, Actions
- Status badges: `queued` (gray), `running` (amber pulsing), `completed` (green), `failed` (red)
- Actions: View Report, Download PDF, Re-run

**Auto-refresh:** Any run with `status: "running"` triggers polling every 3s.

---

### /runs/:id — Report Viewer

**Components:**
- Run metadata header: template name, date, duration, token count, delivery status chips
- View toggle: `[ HTML Report ] [ JSON ] [ Raw Data ]`
- HTML Report tab: renders `GET /runs/:id/output?format=html` in an iframe or dangerouslySetInnerHTML
- JSON tab: renders `GET /runs/:id/output?format=json` in a formatted JSON viewer
- PDF download button
- Section metadata accordion: shows per-section status, token usage, duration

---

### /settings — Workspace Settings

**Tabs:**

1. **General** — workspace name, slug, LLM provider + model selector, Ollama URL
2. **Members** — member list with roles, invite by email, remove members
3. **API Keys** — list keys (prefix + name + last used), create new key (show once modal), revoke

---

### /usage — Usage Dashboard

**Components:**
- Date range selector (last 7d / 30d / 90d / custom)
- Summary cards: Total Tokens, Estimated Cost, Report Runs, Avg Cost/Run
- `TokensOverTime` line chart — daily token usage
- `CostByTemplate` bar chart — cost breakdown per template
- `RunsTable` — all runs in period with token/cost columns

---

## API Client Setup

```typescript
// src/api/client.ts
import axios from "axios";

const api = axios.create({ baseURL: import.meta.env.VITE_API_URL });

// Attach JWT on every request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// Auto-refresh on 401
api.interceptors.response.use(
  (r) => r,
  async (error) => {
    if (error.response?.status === 401) {
      await refreshToken();
      return api.request(error.config);
    }
    return Promise.reject(error);
  }
);
```

---

## Key UX Behaviors

- **Optimistic updates** — toggle active/inactive on templates without waiting for server
- **Toast notifications** — success/error for all mutations (use `react-hot-toast`)
- **Loading skeletons** — all data tables show skeleton rows while loading
- **Empty states** — every list page has a helpful empty state with a CTA
- **Confirm dialogs** — delete actions always require a typed confirmation or click-through modal
- **Run status polling** — use React Query's `refetchInterval` when any run is `running` or `queued`
- **Section query preview** — "Test Query" button in section editor runs the query and shows first 10 rows
