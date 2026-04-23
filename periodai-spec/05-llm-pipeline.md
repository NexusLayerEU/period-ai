# 05 — LLM Processing Pipeline

## Pipeline Overview

Every report run executes 7 stages in sequence. Stages 4 (Generate) runs sections in parallel where possible.

```
Stage 1: FETCH      — Query all data sources for this template
Stage 2: TRANSFORM  — Apply time-range resolution, aggregations, filters
Stage 3: INJECT     — Build LLM context per section (data + prompt template)
Stage 4: GENERATE   — Call LLM for each section (parallel async tasks)
Stage 5: RENDER     — Assemble sections into HTML report + embed charts
Stage 6: DELIVER    — Send to all configured delivery channels
Stage 7: STORE      — Persist run record, output, token usage
```

---

## Pipeline Runner

```python
# app/pipeline/runner.py

class PipelineRunner:
    async def execute(self, run_id: UUID, template: ReportTemplate) -> ReportRun:
        run = await self.update_status(run_id, "running")
        try:
            # Stage 1-2: Fetch and transform
            data_by_section = await self.fetcher.fetch_all(template)

            # Stage 3-4: Generate sections (parallel)
            section_results = await self.generator.generate_all(
                template.sections,
                data_by_section,
                llm_provider=template.workspace.llm_provider
            )

            # Stage 5: Render
            html_output = await self.renderer.render(template, section_results)
            json_output = self.renderer.to_json(template, section_results)

            # Stage 6: Deliver
            await self.deliver_all(run, html_output, template.delivery_channels)

            # Stage 7: Store
            return await self.finalize(run, html_output, json_output, section_results)

        except Exception as e:
            await self.fail(run, str(e))
            raise
```

---

## Stage 1-2: Fetch & Transform

```python
# app/pipeline/fetcher.py

class Fetcher:
    async def fetch_all(self, template: ReportTemplate) -> dict[str, list[dict]]:
        """Returns { section_id: [row_dicts] } for all sections."""
        results = {}
        for section in template.sections:
            connector = get_connector(section.source_id)
            params = self.resolve_query_params(section.query_params)
            rows = await connector.query(section.query, params)
            results[section.id] = rows
        return results

    def resolve_query_params(self, params: dict) -> dict:
        """Resolve date shortcuts to actual datetime values."""
        resolved = {}
        now = datetime.utcnow()
        shortcuts = {
            "last_7_days":  now - timedelta(days=7),
            "last_30_days": now - timedelta(days=30),
            "last_90_days": now - timedelta(days=90),
            "this_week":    now - timedelta(days=now.weekday()),
            "this_month":   now.replace(day=1),
            "last_week":    ...,  # implement full date logic
            "last_month":   ...,
        }
        for k, v in params.items():
            resolved[k] = shortcuts.get(v, v)
        return resolved
```

---

## Stage 3-4: LLM Generation

```python
# app/pipeline/generator.py

class SectionGenerator:
    async def generate_all(
        self,
        sections: list[SectionConfig],
        data: dict[str, list[dict]],
        llm_provider: str
    ) -> list[SectionResult]:
        """Generate all sections concurrently."""
        tasks = [
            self.generate_section(section, data[section.id], llm_provider)
            for section in sections
        ]
        return await asyncio.gather(*tasks, return_exceptions=True)

    async def generate_section(
        self,
        section: SectionConfig,
        rows: list[dict],
        llm_provider: str
    ) -> SectionResult:
        handler = get_section_handler(section.type)
        return await handler.generate(section, rows, llm_provider)
```

---

## LLM Provider Abstraction

```python
# app/llm/base.py

class LLMProvider(ABC):
    @abstractmethod
    async def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 1000
    ) -> LLMResponse:
        ...

@dataclass
class LLMResponse:
    content: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    model: str
```

```python
# app/llm/anthropic.py

class AnthropicProvider(LLMProvider):
    async def complete(self, system_prompt, user_prompt, max_tokens=1000):
        client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        msg = await client.messages.create(
            model=settings.ANTHROPIC_MODEL,
            max_tokens=max_tokens,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}]
        )
        return LLMResponse(
            content=msg.content[0].text,
            input_tokens=msg.usage.input_tokens,
            output_tokens=msg.usage.output_tokens,
            total_tokens=msg.usage.input_tokens + msg.usage.output_tokens,
            model=msg.model
        )
```

**Retry logic (apply to all providers):**
```python
@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=10))
async def complete_with_retry(self, ...):
    return await self.complete(...)
```

---

## Section Types

### Base Section Handler

```python
# app/pipeline/sections/base.py

class BaseSectionHandler(ABC):
    SYSTEM_PROMPT = ""  # Override in subclass

    async def generate(
        self,
        section: SectionConfig,
        rows: list[dict],
        llm_provider: str
    ) -> SectionResult:
        llm = get_provider(llm_provider)
        user_prompt = self.build_prompt(section, rows)
        response = await llm.complete(self.SYSTEM_PROMPT, user_prompt)
        return SectionResult(
            section_id=section.id,
            type=section.type,
            title=section.title,
            content=response.content,
            chart_data=self.prepare_chart_data(section, rows),
            tokens_used=response.total_tokens,
            status="completed"
        )

    def build_prompt(self, section, rows) -> str:
        data_preview = json.dumps(rows[:50], indent=2)  # cap at 50 rows
        return f"""Section: {section.title}
Data ({len(rows)} rows, showing first 50):
{data_preview}

Instructions: {section.llm_prompt}"""

    def prepare_chart_data(self, section, rows) -> dict | None:
        return None  # Override in chart-producing sections
```

---

### Section Type: summary

**Purpose:** AI-written executive summary paragraph(s) of the data.

```python
SYSTEM_PROMPT = """You are a business intelligence analyst. 
Write clear, concise executive summaries from raw data.
Use plain prose — no bullet points unless explicitly requested.
Quantify changes with percentages and absolute numbers.
Highlight the most significant finding first.
Keep summaries under 150 words unless the section prompt specifies otherwise."""
```

**Output:** Markdown text string.

---

### Section Type: metric_cards

**Purpose:** Extract key numbers to display as highlighted metric cards.

```python
SYSTEM_PROMPT = """You are a data analyst. 
Extract the most important metrics from the data.
Return ONLY valid JSON — no explanation, no markdown, no code fences.
Format: { "metrics": [{ "label": "...", "value": "...", "change": "+12%", "trend": "up" }] }
Include at most 6 metrics.
"trend" must be "up", "down", or "neutral"."""
```

**Output:** JSON string. Parse in renderer to render as cards.

---

### Section Type: trend

**Purpose:** AI narrative describing directional movement over time.

```python
SYSTEM_PROMPT = """You are a trend analyst.
Describe the trend in the data over time.
Identify: direction (up/down/flat), rate of change, any inflection points, seasonality.
Compare beginning vs end of the period.
Be specific with numbers.
Write in 2-3 sentences."""
```

**Output:** Markdown text.

---

### Section Type: bar_chart / line_chart

**Purpose:** Render a chart from the query data. No LLM call needed — data goes directly to renderer.

```python
class BarChartHandler(BaseSectionHandler):
    async def generate(self, section, rows, llm_provider):
        # No LLM call — just structure the data for rendering
        return SectionResult(
            section_id=section.id,
            type=section.type,
            title=section.title,
            content=None,
            chart_data={
                "rows": rows,
                "config": section.chart_config
            },
            tokens_used=0,
            status="completed"
        )
```

**chart_config fields:**

```json
{
  "type": "bar",     // "bar" | "line" | "area" | "pie"
  "x": "date",       // column name for X axis
  "y": "revenue",    // column name for Y axis (or list for multi-series)
  "color": "#FF8C42",
  "title": "Daily Revenue"
}
```

---

### Section Type: anomaly

**Purpose:** AI identifies and explains outliers in the data.

```python
SYSTEM_PROMPT = """You are an anomaly detection specialist.
Analyze the data for outliers, spikes, drops, or unusual patterns.
For each anomaly found:
  1. Describe what is anomalous (specific value, date, or pattern)
  2. Quantify how unusual it is (X% above/below average, X standard deviations)
  3. Suggest a possible explanation
If no anomalies are found, say "No significant anomalies detected in this period."
Be concise. Maximum 3 anomalies."""
```

**Output:** Markdown with clear anomaly descriptions.

---

### Section Type: forecast

**Purpose:** AI projects the next period based on historical trend.

```python
SYSTEM_PROMPT = """You are a forecasting analyst.
Based on the historical data provided, project the likely value(s) for the next period.
State:
  1. Your forecast value or range
  2. The trend basis for your projection (linear, seasonal, other)
  3. Key assumptions and risks
  4. Confidence level: low / medium / high
Be explicit that this is a projection, not a guarantee.
Keep the forecast under 100 words."""
```

**Output:** Markdown text.

---

### Section Type: insight

**Purpose:** Free-form custom analysis. The section's `llm_prompt` is the entire instruction.

```python
SYSTEM_PROMPT = """You are a business intelligence analyst.
Answer the question or follow the instruction provided.
Be specific, data-driven, and concise.
Use the provided data as your primary source."""
```

The `llm_prompt` from the section config is used verbatim as the instruction to the LLM.

**Output:** Markdown text.

---

### Section Type: actions

**Purpose:** AI-generated recommended next steps based on the report data.

```python
SYSTEM_PROMPT = """You are a strategic advisor reviewing business data.
Based on the data, generate 3-5 concrete, actionable recommendations.
Each action must be:
  - Specific and achievable
  - Tied to a data point from the report
  - Assigned a priority: HIGH / MEDIUM / LOW
Return ONLY valid JSON, no markdown, no code fences:
{ "actions": [{ "priority": "HIGH", "action": "...", "rationale": "..." }] }"""
```

**Output:** JSON string. Parse in renderer to render as action cards.

---

## Stage 5: Renderer

```python
# app/pipeline/renderer.py

class ReportRenderer:
    def render(self, template: ReportTemplate, results: list[SectionResult]) -> str:
        """Assemble all sections into a complete HTML report."""
        sections_html = []
        for result in sorted(results, key=lambda r: r.position):
            html = self.render_section(result)
            sections_html.append(html)
        return self.wrap_in_template(template.name, sections_html)

    def render_section(self, result: SectionResult) -> str:
        if result.status == "failed":
            return f'<div class="section error">Section "{result.title}" failed: {result.error}</div>'
        
        if result.type in ("bar_chart", "line_chart"):
            chart_png_b64 = generate_chart_png(result.chart_data)
            return f'<div class="section chart"><h2>{result.title}</h2><img src="data:image/png;base64,{chart_png_b64}"/></div>'
        
        if result.type in ("metric_cards", "actions"):
            data = json.loads(result.content)
            return self.render_structured(result.type, result.title, data)
        
        # Default: markdown content
        html_content = markdown.markdown(result.content)
        return f'<div class="section"><h2>{result.title}</h2>{html_content}</div>'
```

---

## Chart Rendering (Plotly → PNG)

```python
# app/utils/chart.py
import plotly.graph_objects as go
import kaleido  # pip install kaleido

def generate_chart_png(chart_data: dict) -> str:
    """Render chart to base64 PNG for embedding in HTML/email."""
    rows = chart_data["rows"]
    cfg = chart_data["config"]
    
    x_vals = [r[cfg["x"]] for r in rows]
    y_vals = [r[cfg["y"]] for r in rows]
    
    if cfg["type"] == "bar":
        fig = go.Figure(go.Bar(x=x_vals, y=y_vals, marker_color=cfg.get("color", "#FF8C42")))
    elif cfg["type"] == "line":
        fig = go.Figure(go.Scatter(x=x_vals, y=y_vals, mode="lines+markers"))
    
    fig.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(family="Arial", size=12),
        margin=dict(l=40, r=20, t=40, b=40),
        title=cfg.get("title", "")
    )
    
    img_bytes = fig.to_image(format="png", width=800, height=400)
    return base64.b64encode(img_bytes).decode()
```

---

## Token Cost Estimation

Store cost per run using these rates (update as pricing changes):

| Provider | Model | Input (per 1M tokens) | Output (per 1M tokens) |
|----------|-------|-----------------------|------------------------|
| Anthropic | claude-sonnet-4 | $3.00 | $15.00 |
| Google | gemini-2.0-flash | $0.075 | $0.30 |
| Ollama | any | $0.00 | $0.00 |

```python
def calculate_cost(provider, input_tokens, output_tokens) -> float:
    rates = {
        "anthropic": (3.00, 15.00),
        "gemini": (0.075, 0.30),
        "ollama": (0.0, 0.0),
    }
    in_rate, out_rate = rates.get(provider, (0, 0))
    return (input_tokens * in_rate + output_tokens * out_rate) / 1_000_000
```
