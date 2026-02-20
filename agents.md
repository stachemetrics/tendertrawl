# TenderTrawl 🐟💰

**Tell me what your business does. I'll show you what's open — and where the money's been.**

A conversational AI prototype that replaces spreadsheet-driven Australian Government tender discovery with a single chat interface. Describe your business, get matched to open opportunities *and* historical spending insights in one flow. No signup. No keyword configuration. Just ask.

> Prototype #2 in the [42-prototype series](https://mmetrics.ai/posts/bring-your-spreadsheet/) by [MMetrics.ai](https://mmetrics.ai)

---

## The Problem

SMEs chasing Australian Government tenders currently juggle:
- **Email alerts** from keyword-based notification services (Australian Tenders, TenderSearch)
- **A discovery spreadsheet** tracking what's open, what's relevant, and what to chase
- **Manual research** on who's been buying, who's been winning, and when contracts expire
- **Gut feel** for go/no-go decisions on which tenders to invest time in

Existing AI tools (TenderPilot, TenderTrace, BidWriteGPT) focus on bid *writing* or require enterprise sales calls. Nobody lets you try the insight experience immediately.

## The Demo Thesis

> Can a chatbot that understands your business match you to relevant government tenders — and surface historical spending patterns — better than keyword alerts and spreadsheets?

## One Conversation, Not Two Modes

TenderTrawl blends discovery and insights into a single chat. You don't pick a mode — the conversation flows naturally:

```
You:  We're a small cybersecurity consultancy in Canberra,
      specialising in cloud migration and IRAP assessments.

🐟:   Casting the net... 🎣

      I found 3 open tenders that match your capability:

      🎯 ICT Security Assessment Panel — Dept of Finance
         Closes 15 Mar 2026 | Est. value: $2-5M
         "Direct match — IRAP assessment is a listed requirement"

      ⚡ Digital Transformation Services — Services Australia
         Closes 28 Feb 2026 | Est. value: $500K-1M
         "Cloud migration scope, though broader than your niche"

      🤷 IT Support Services — Attorney-General's
         Closes 10 Mar 2026 | Est. value: $200K
         "General IT, light cyber component"

      💰 Here's where it gets interesting — looking at who's been
      spending in your categories over the last 12 months:

      Dept of Defence spent $340M on IT security services
      across 89 contracts. Top winners: Leidos ($45M),
      Accenture ($38M), DXC ($22M).

      12 contracts worth $28M expire in the next 6 months.
      That's where the next wave of opportunities comes from.

      Want me to dig deeper into any of these, or look at a
      different agency?
```

The insight data transforms a simple tender alert into a strategic conversation. "Here's what's open" is table stakes. "Here's where the money has been, who's winning it, and when the doors reopen" — that's the demo's wow moment.

## Data Sources

### Historical Contract Notices (`data/cn_combined.csv`)
- **Source:** AusTender weekly Contract Notice exports from [tenders.gov.au/reports/list](https://www.tenders.gov.au/reports/list)
- **Format:** 52 `.xlsx` files, bulk downloaded. Each has metadata in rows 1-2, header at row 3
- **Combined via:** `scripts/combine_exports.py` → single cleaned CSV
- **Coverage:** ~12 months of awarded contracts across all federal agencies

| Column | Use |
|--------|-----|
| `Agency` | Who's buying |
| `Category` | Plain English category (no UNSPSC codes needed) |
| `Value` | Contract value (parsed to float) |
| `Description` | Free text — great for LLM matching |
| `Start Date` / `End Date` | Contract period → expiry = future opportunity |
| `Supplier Name` | Who's winning this work |
| `Procurement Method` | Open / Limited / Prequalified tender |
| `CN ID` | Unique contract notice identifier |
| `ATM ID` | Links to original Approach to Market |
| `SON ID` | Links to Standing Offer Notice (panel) |
| `Consultancy` | Yes/No flag |

### Open Approaches to Market (live fetch — future)
- **Source:** AusTender search at [tenders.gov.au/atm/search](https://www.tenders.gov.au/atm/search)
- **Status:** Start with curated sample data; add live scraping once core UX is proven

### OCDS API (stretch goal)
- **Source:** [data.open-contracting.org](https://data.open-contracting.org/en/publication/19)
- **Format:** JSON API, 450K+ contracts back to 2004
- **Use:** Deeper historical analysis if the demo warrants it

## Tech Stack

| Component | Tool | Notes |
|-----------|------|-------|
| UI | Gradio `gr.Blocks` | Dark theme, streaming chat, 🐟💰 branding |
| LLM | Google Gemini API | Free tier, `gemini-2.0-flash` |
| Data | pandas + openpyxl | CN export analysis |
| Scraping | httpx + BeautifulSoup | Company URLs, AusTender ATMs |
| Deploy | Modal | Same pattern as Snifftest prototype |
| Logging | Modal Volume | Persistent log storage per session |

## Project Structure

```
tendertrawl/
├── app.py                 # Gradio UI + chat logic (single entry point)
├── deploy.py              # Modal deployment harness
├── trawl/
│   ├── __init__.py
│   ├── insights.py        # Pandas queries: agency spend, top suppliers, expiring contracts
│   ├── discovery.py       # Match user business description to open tenders
│   ├── llm.py             # Gemini API wrapper (extract capabilities, generate summaries)
│   └── scraper.py         # Fetch company website, parse capability keywords
├── data/
│   ├── raw/               # 52 original .xlsx exports (gitignored)
│   ├── cn_combined.csv    # Combined + cleaned output (gitignored)
│   └── sample.csv         # Small sample for testing/demo (committed)
├── scripts/
│   └── combine_exports.py # Concatenate 52 xlsx → one clean CSV
├── requirements.txt
├── .env.example           # GOOGLE_API_KEY=your-key-here
├── .gitignore
└── README.md
```

## Modal Deployment Pattern (from Snifftest)

`deploy.py` follows the proven pattern:

```python
import modal

app = modal.App("tendertrawl")

image = modal.Image.debian_slim(python_version="3.12").pip_install(
    "fastapi[standard]",
    "gradio~=5.7",
    "requests",
    "google-genai",
    "pandas",
    "openpyxl",
    "httpx",
    "beautifulsoup4",
)

volume = modal.Volume.from_name("tendertrawl-logs", create_if_missing=True)

@app.function(
    image=image,
    max_containers=1,
    volumes={"/logs": volume},
    secrets=[modal.Secret.from_name("tendertrawl-secrets")],
)
@modal.concurrent(max_inputs=100)
@modal.asgi_app()
def web():
    import sys
    sys.path.insert(0, "/root")
    from fastapi import FastAPI
    from gradio.routes import mount_gradio_app
    from app import create_demo
    demo = create_demo()
    return mount_gradio_app(app=FastAPI(), blocks=demo, path="/")
```

**Key lessons from Snifftest deploy:**
- Always include `requests` in pip_install (undeclared Gradio dependency)
- Use `max_containers=1` for Gradio sticky sessions
- `modal.Volume` for persistent logging across restarts
- Mount local files or inline — Modal doesn't see your local filesystem

## Gradio UX Goals

- **Dark theme** matching mmetrics.ai terminal aesthetic
- **Streaming chat** with character-by-character responses
- **Avatars:** 🐟 for the bot, 💼 for the user
- **Rich markdown:** tables for spend data, emoji for match scores
- **Status updates:** "🎣 Casting the net..." → "💰 Checking the catch..."
- **Fun personality:** The bot is a fishing guide for government contracts

### Match Score System
| Emoji | Label | Meaning |
|-------|-------|---------|
| 🎯 | Strong catch | Direct capability match + recent agency spend |
| ⚡ | Worth a look | Partial match or adjacent category |
| 🤷 | Long shot | Weak match, but agency has budget in area |

## Build Order

1. ✅ **Data pipeline** — `combine_exports.py`, load and validate CN data
2. ✅ **Insights engine** — pandas queries (agency spend, top suppliers, expiring contracts)
3. ✅ **Gradio shell** — dark theme, streaming chat, URL input, clear button, hardcoded demo responses; tender links use `tenders.gov.au/Atm/Show/{GUID}`; no estimated value (not in RSS feed)
4. **LLM integration** — Gemini for understanding business descriptions + generating summaries
5. **Discovery** — match capabilities to open tenders via AusTender RSS feed + sample data
6. **Polish** — error handling, deploy-ready config
7. **Deploy** — Modal config, public URL, blog post

## Competitive Context

| Player | Focus | Price | Our Edge |
|--------|-------|-------|----------|
| TenderPilot | AI bid writing | Waitlist/paid | We do discovery + insights, try immediately |
| TenderTrace | Market intelligence | Enterprise SaaS | Same insight value, free to try |
| Australian Tenders | Keyword alerts | $$/year | We match by capability, not keywords |
| GovBid | Discovery + writing | Paid | Conversational UX, no config required |
| BidWriteGPT | Bid writing | Enterprise | Different focus entirely |

**Our positioning:** Try it now. No signup. Tell me what you do, I'll tell you what to chase and why.

## Data Notes

`data/cn_combined.csv`
============================================================
📊 DATASET SUMMARY
============================================================
  Total rows:          81,105
  Columns:             31
  Date range:          2002-07-28 00:00:00 → 2026-02-13 18:25:00
  Total value:         $968,898,575,024
  Mean contract:       $11,946,225
  Median contract:     $135,974
  Unique agencies:     127
  Top 5 by spend:
    $786,228,393,727  Department of Defence
    $33,036,241,645  Australian Taxation Office
    $22,506,094,988  Department of Home Affairs
    $15,487,060,021  National Blood Authority
    $13,545,585,142  Department of Health, Disability and Ageing
  Unique categories:   551
  Unique suppliers:    24279
  Expiring <6 months:  24,891 contracts ($64,712,013,225)

  Procurement methods:
    40,705 (50.2%)  Open tender
    40,273 (49.7%)  Limited tender
       125 ( 0.2%)  Prequalified tender
         1 ( 0.0%)  Software
         1 ( 0.0%)  Computer services
============================================================

  Columns: ['Agency', 'Parent CN ID', 'CN ID', 'Publish Date', 'Amendment Publish Date', 'Status', 'Start Date', 'End Date', 'Value', 'Description', 'Agency Ref. ID', 'Category', 'Procurement Method', 'ATM ID', 'SON ID', 'Confidentiality - Contract', 'Confidentiality - Contract Reason(s)', 'Confidentiality - Outputs', 'Confidentiality - Outputs Reason(s)', 'Consultancy', 'Consultancy Reason(s)', 'Amendment Reason', 'Supplier Name', 'Supplier City', 'Supplier Postcode', 'Supplier Country', 'Supplier ABNExempt', 'Supplier ABN', 'Agency Branch', 'Agency Divison', 'Agency Postcode']

## Modal Rules and Guidelines for LLMs

This file provides rules and guidelines for LLMs when implementing Modal code.

### General

- Modal is a serverless cloud platform for running Python code with minimal configuration
- Designed for AI/ML workloads but supports general-purpose cloud compute
- Serverless billing model - you only pay for resources used

### Modal documentation

- Extensive documentation is available at: modal.com/docs (and in markdown format at modal.com/llms-full.txt)
- A large collection of examples is available at: modal.com/docs/examples (and github.com/modal-labs/modal-examples)
- Reference documentation is available at: modal.com/docs/reference

Always refer to documentation and examples for up-to-date functionality and exact syntax.

### Core Modal concepts

### App

- A group of functions, classes and sandboxes that are deployed together.

### Function

- The basic unit of serverless execution on Modal.
- Each Function executes in its own container, and you can configure different Images for different Functions within the same App:

  ```python
  image = (
    modal.Image.debian_slim(python_version="3.12")
    .pip_install("torch", "transformers")
    .apt_install("ffmpeg")
    .run_commands("mkdir -p /models")
  )

  @app.function(image=image)
  def square(x: int) -> int:
    return x * x
  ```

- You can configure individual hardware requirements (CPU, memory, GPUs, etc.) for each Function.

  ```python
  @app.function(
    gpu="H100",
    memory=4096,
    cpu=2,
  )
  def inference():
    ...
  ```

  Some examples specificly for GPUs:

  ```python
  @app.function(gpu="A10G")  # Single GPU, e.g. T4, A10G, A100, H100, or "any"
  @app.function(gpu="A100:2")  # Multiple GPUs, e.g. 2x A100 GPUs
  @app.function(gpu=["H100", "A100", "any"]) # GPU with fallbacks
  ```

- Functions can be invoked in a number of ways. Some of the most common are:
  - `foo.remote()` - Run the Function in a separate container in the cloud. This is by far the most common.
  - `foo.local()` - Run the Function in the same context as the caller. Note: This does not necessarily mean locally on your machine.
  - `foo.map()` - Parallel map over a set of inputs.
  - `foo.spawn()` - Calls the function with the given arguments, without waiting for the results. Terminating the App will also terminate spawned functions.
- Web endpoint: You can turn any Function into an HTTP web endpoint served by adding a decorator:

  ```python
  @app.function()
  @modal.fastapi_endpoint()
  def fastapi_endpoint():
    return {"status": "ok"}

  @app.function()
  @modal.asgi_app()
  def asgi_app():
    app = FastAPI()
    ...
    return app
  ```

- You can run Functions on a schedule using e.g. `@app.function(schedule=modal.Period(minutes=5))` or `@app.function(schedule=modal.Cron("0 9 * * *"))`.

### Classes (a.k.a. `Cls`)

- For stateful operations with startup/shutdown lifecycle hooks. Example:

  ```python
  @app.cls(gpu="A100")
  class ModelServer:
      @modal.enter()
      def load_model(self):
          # Runs once when container starts
          self.model = load_model()

      @modal.method()
      def predict(self, text: str) -> str:
          return self.model.generate(text)

      @modal.exit()
      def cleanup(self):
          # Runs when container stops
          cleanup()
  ```

### Other important concepts

- Image: Represents a container image that Functions can run in.
- Sandbox: Allows defining containers at runtime and securely running arbitrary code inside them.
- Volume: Provide a high-performance distributed file system for your Modal applications.
- Secret: Enables securely providing credentials and other sensitive information to your Modal Functions.
- Dict: Distributed key/value store, managed by Modal.
- Queue: Distributed, FIFO queue, managed by Modal.

### Differences from standard Python development

- Modal always executes code in the cloud, even while you are developing. You can use Environments for separating development and production deployments.
- Dependencies: It's common and encouraged to have different dependency requirements for different Functions within the same App. Consider defining dependencies in Image definitions (see Image docs) that are attached to Functions, rather than in global `requirements.txt`/`pyproject.toml` files, and putting `import` statements inside the Function `def`. Any code in the global scope needs to be executable in all environments where that App source will be used (locally, and any of the Images the App uses).

### Modal coding style

- Modal Apps, Volumes, and Secrets should be named using kebab-case.
- Always use `import modal`, and qualified names like `modal.App()`, `modal.Image.debian_slim()`.
- Modal evolves quickly, and prints helpful deprecation warnings when you `modal run` an App that uses deprecated features. When writing new code, never use deprecated features.

### Common commands

Running `modal --help` gives you a list of all available commands. All commands also support `--help` for more details.

### Running your Modal app during development

- `modal run path/to/your/app.py` - Run your app on Modal.
- `modal run -m module.path.to.app` - Run your app on Modal, using the Python module path.
- `modal serve modal_server.py` - Run web endpoint(s) associated with a Modal app, and hot-reload code on changes. Will print a URL to the web endpoint(s). Note: you need to use `Ctrl+C` to interrupt `modal serve`.

### Deploying your Modal app

- `modal deploy path/to/your/app.py` - Deploy your app (Functions, web endpoints, etc.) to Modal.
- `modal deploy -m module.path.to.app` - Deploy your app to Modal, using the Python module path.

Logs:

- `modal app logs <app_name>` - Stream logs for a deployed app. Note: you need to use `Ctrl+C` to interrupt the stream.

### Resource management

- There are CLI commands for interacting with resources like `modal app list`, `modal volume list`, and similarly for `secret`, `dict`, `queue`, etc.
- These also support other command than `list` - use e.g. `modal app --help` for more.

### Testing and debugging

- When using `app.deploy()`, you can wrap it in a `with modal.enable_output():` block to get more output.

## Developer Notes

- **Dev Env:** WSL, 3.11 python virtual env.
- **Approach:** Baby steps — one working piece at a time, clear human in the loop to clarify intent. Always building with deployment in ind
- **Data:** Raw exports in `data/raw/` (52 files, ~13MB total). Gitignored.
- **LLM costs:** Gemini paid API credits available - will put key into .env (also .gitignored)