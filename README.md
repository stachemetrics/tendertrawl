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

      I found 3 open tenders that match your capability:

      🎯 ICT Security Assessment Panel — Dept of Finance
         Closes 15 Mar 2026 | Est. value: $2-5M

      ⚡ Digital Transformation Services — Services Australia
         Closes 28 Feb 2026 | Est. value: $500K-1M

      💰 Dept of Defence spent $340M on IT security services
         across 89 contracts. 12 worth $28M expire in 6 months.
         That's where the next wave comes from.
```

"Here's what's open" is table stakes. "Here's where the money has been, who's winning it, and when the doors reopen" is the demo's value.

---

## Stack

| Component | Tool |
|-----------|------|
| UI | Gradio `gr.Blocks` — dark theme, streaming chat |
| LLM | Google Gemini API (`gemini-2.0-flash`) |
| Data | pandas + openpyxl |
| Scraping | httpx + BeautifulSoup |
| Deploy | Modal |

---

## Project structure

```
tendertrawl/
├── app.py                 # Gradio UI + chat logic
├── deploy.py              # Modal deployment harness
├── trawl/
│   ├── insights.py        # Pandas queries: agency spend, suppliers, expiring contracts
│   ├── discovery.py       # Match business description to open tenders
│   ├── llm.py             # Gemini API wrapper
│   └── scraper.py         # Fetch company website, parse capability keywords
├── data/
│   ├── raw/               # 52 xlsx exports (gitignored)
│   ├── cn_combined.csv    # Combined + cleaned (gitignored)
│   └── sample.csv         # Small sample for dev/demo (committed)
├── scripts/
│   └── combine_exports.py # Concatenate 52 xlsx → one CSV
├── .env                   # GEMINI_API_KEY=... (gitignored)
└── requirements.txt
```

---

## Setup

```bash
# Create and activate virtualenv
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set API key
cp .env.example .env
# edit .env → GEMINI_API_KEY=your-key-here

# (Optional) rebuild combined CSV from raw exports
python scripts/combine_exports.py

# Run locally
python app.py
```

---

## Data

`data/cn_combined.csv` — ~81K contract notices from [AusTender weekly exports](https://www.tenders.gov.au/Reports/CnWeeklyExportList).

- Date range: Feb 2025 – Feb 2026
- Total value: ~$969B
- 127 unique agencies, 24K+ suppliers, 551 categories
- ~25K contracts expiring within 6 months (~$65B) — the opportunity pipeline

Raw `.xlsx` exports live in `data/raw/` (gitignored). Download from [tenders.gov.au](https://www.tenders.gov.au/Reports/CnWeeklyExportList), move to `./data/raw/` and run `combine_exports.py` to rebuild.

---

## Build order

- [x] Data pipeline — `combine_exports.py`, validate CN data
- [x] Insights engine — pandas queries (agency spend, top suppliers, expiring contracts)
- [x] Gradio shell — themed chat UI, hardcoded demo responses, streaming, URL input, clear button
- [ ] LLM integration — Gemini for business description understanding + response generation
- [ ] Discovery — match capabilities to open tenders (RSS feed + sample data)
- [ ] Polish — error handling, deploy-ready config
- [ ] Deploy — Modal config, public URL
