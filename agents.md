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

1. **Data pipeline** — `combine_exports.py`, load and validate CN data
2. **Insights engine** — pandas queries (agency spend, top suppliers, expiring contracts)
3. **Gradio shell** — themed chat UI, hardcoded example responses
4. **LLM integration** — Gemini for understanding business descriptions + generating summaries
5. **Discovery** — match capabilities to open tenders (start with sample data)
6. **Polish** — streaming, status animations, error handling
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

## Developer Notes

- **Dev Env:** WSL, 3.11 python virtual env.
- **Approach:** Baby steps — one working piece at a time, clear human in the loop to clarify intent.
- **Data:** Raw exports in `data/raw/` (52 files, ~13MB total). Gitignored.
- **LLM costs:** Gemini paid API credits available - will put key into .env (also .gitignored)