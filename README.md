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

# Create secret (once)
modal secret create tendertrawl-secrets GEMINI_API_KEY=your-key-here

# Serve with hot-reload (dev)
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

## Known limitations

- Open tender search relies on Gemini's Google Search grounding — results vary by niche
- Category matching uses substring keywords; obscure specialisations may not map cleanly
- `cn_combined.csv` is a point-in-time snapshot; not updated automatically

---

## Build order

- [x] Data pipeline — `combine_exports.py`, validate CN data
- [x] Insights engine — agency spend, top suppliers, expiring contracts
- [x] Gradio shell — dark theme, streaming chat, match score emojis
- [x] LLM integration — Gemini profile extraction + Search-grounded tender discovery
- [ ] Discovery — RSS feed integration for live open tenders
- [ ] Polish — rate limiting, error handling
- [ ] Deploy — Modal, public URL, blog post

---

## License

MIT — see [LICENSE](LICENSE)
