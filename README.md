# TenderTrawl

**Tell me what your business does. I'll show you what's open — and where the money's been.**

Conversational AI prototype for Australian Government tender discovery. Describe your business, get matched to open opportunities *and* historical spending insights in one chat flow. No signup. No keyword config. Just ask.

> Prototype #2 in the [42-prototype series](https://mmetrics.ai/posts/bring-your-spreadsheet/) by [MMetrics.ai](https://mmetrics.ai)

---

## What it does

Most SMEs chasing government tenders juggle keyword-alert emails, a discovery spreadsheet, and manual research on who's been winning what. TenderTrawl replaces that with a single conversation:

```
You:  We're a small cybersecurity consultancy in Canberra,
      specialising in cloud migration and IRAP assessments.

🐟:   Casting the net... 🎣

      🎯 ICT Security Assessment Panel — Dept of Finance
         Closes 15 Mar 2026

      ⚡ Digital Transformation Services — Services Australia
         Closes 28 Feb 2026

      💰 Dept of Defence spent $340M on IT security services
         across 89 contracts. 12 worth $28M expire in 6 months.
         That's where the next wave comes from.
```

"Here's what's open" is table stakes. "Here's where the money has been, who's winning it, and when the doors reopen" is the value.

---

## Stack

| Component | Tool |
|-----------|------|
| UI | Gradio `gr.Blocks` — dark theme, streaming chat |
| LLM | Google Gemini API (`gemini-2.5-flash` with Search grounding) |
| Data | pandas — AusTender contract notice exports |
| Deploy | Modal |

---

## Project structure

```
tendertrawl/
├── app/
│   ├── app.py             # Gradio UI + chat logic
│   └── deploy.py          # Modal deployment
├── trawl/
│   ├── insights.py        # Pandas queries: agency spend, suppliers, expiring contracts
│   └── llm.py             # Gemini API wrapper
├── data/
│   ├── raw/               # Weekly xlsx exports from AusTender (gitignored)
│   └── cn_combined.csv    # Combined + cleaned dataset (gitignored)
├── scripts/
│   └── combine_exports.py # Concatenate xlsx exports → one CSV
├── .env                   # GEMINI_API_KEY=... (gitignored)
└── requirements.txt
```

---

## Setup

```bash
# Create and activate virtualenv
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set API key
cp .env.example .env
# edit .env → GEMINI_API_KEY=your-key-here

# (Optional) rebuild combined CSV from raw exports
# Download xlsx files from tenders.gov.au/Reports/CnWeeklyExportList → data/raw/
python scripts/combine_exports.py

# Run locally
python app/app.py
# → http://localhost:7860
```

---

## Deploy to Modal

```bash
pip install modal
modal setup

# Needs a Modal secret named 'gemini-secret' with GEMINI_API_KEY set.
# Create it once if it doesn't exist:
modal secret create gemini-secret GEMINI_API_KEY=your-key-here

# Serve with hot-reload (dev) — run from project root
modal serve app/deploy.py

# Deploy to production
modal deploy app/deploy.py
```

Logs persist to `/root/logs/tendertrawl_logs.jsonl` on a Modal Volume.

---

## Data

`data/cn_combined.csv` — ~81K contract notices from [AusTender weekly exports](https://www.tenders.gov.au/Reports/CnWeeklyExportList).

- Date range: Feb 2025 – Feb 2026
- Total value: ~$969B across 127 agencies
- 24K+ unique suppliers, 551 categories
- ~25K contracts expiring within 6 months (~$65B) — the forward opportunity pipeline

---

## Status

Working demo deployed on Modal. End-to-end flow is live: business description → Gemini profile extraction → Google Search-grounded tender discovery → historical spend insights from AusTender data.

**Known issues / next:**
- Response latency is high (~20–30s) — two sequential Gemini Search calls; candidate fix is parallelising `extract_profile` + `generate_tender_list`
- Category matching on niche inputs can produce noisy results (broad keyword expansion)
- `cn_combined.csv` is a Feb 2026 point-in-time snapshot; no auto-refresh
- Bid writing CTA is a stub ("coming soon")

---

## Build order

- [x] Data pipeline — `combine_exports.py`, validate CN data
- [x] Insights engine — agency spend, top suppliers, expiring contracts
- [x] Gradio shell — dark theme, streaming chat, match score emojis
- [x] LLM integration — Gemini 2.5 Flash, Search-grounded profile + tender discovery
- [x] Deploy — Modal, live URL
- [X] Blog post

And if there's interest in taking things further...
- [ ] Performance — parallelise LLM calls, investigate GCP region latency
- [ ] Polish — rate limiting, better error states, refresh data


---

## License

MIT — see [LICENSE](LICENSE)
