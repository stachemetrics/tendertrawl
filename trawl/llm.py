"""
trawl/llm.py — Gemini helpers (profile extraction + tender search).
"""

from __future__ import annotations

import json
import os
import re
from functools import lru_cache

from google import genai
from google.genai import types

from trawl import insights

MODEL_NAME = "gemini-2.0-flash"


@lru_cache(maxsize=1)
def _client() -> genai.Client:
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("Missing GEMINI_API_KEY or GOOGLE_API_KEY in environment.")
    return genai.Client(api_key=api_key)


def _extract_json(text: str) -> dict:
    if not text:
        return {}
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```[a-zA-Z0-9_-]*\n", "", cleaned)
        cleaned = cleaned.rstrip("`\n ")
    if "{" in cleaned and "}" in cleaned:
        cleaned = cleaned[cleaned.find("{") : cleaned.rfind("}") + 1]
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return {}


def _format_money(value: float) -> str:
    if value >= 1_000_000_000:
        return f"${value / 1_000_000_000:.1f}B"
    if value >= 1_000_000:
        return f"${value / 1_000_000:.1f}M"
    if value >= 1_000:
        return f"${value / 1_000:.1f}K"
    return f"${value:,.0f}"


def extract_profile(user_input: str) -> dict:
    """
    Extract a capability summary + keyword list.
    If input is a URL, use Google Search to ground the summary.
    """
    prompt = f"""
You are TenderTrawl. Determine whether the input is a URL or a plain business description.

If it is a URL, use Google Search to identify the company and its capabilities.
If it is a description, do NOT search.

Return JSON ONLY with fields:
  summary: 1-2 sentences
  keywords: 6-12 short phrases
  url: include the URL if provided or discovered, otherwise empty string
  confidence: low | medium | high

Input:
{user_input}
""".strip()

    client = _client()
    config = types.GenerateContentConfig(
        temperature=0.2,
        response_mime_type="application/json",
        tools=[types.Tool(google_search=types.GoogleSearch())],
    )
    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt,
        config=config,
    )
    data = _extract_json(getattr(response, "text", "") or "")
    if not data:
        return {
            "summary": user_input.strip(),
            "keywords": [],
            "url": "",
            "confidence": "low",
        }

    keywords = data.get("keywords")
    if not isinstance(keywords, list):
        keywords = []

    return {
        "summary": str(data.get("summary") or user_input.strip()),
        "keywords": [str(k).strip() for k in keywords if str(k).strip()],
        "url": str(data.get("url") or "").strip(),
        "confidence": str(data.get("confidence") or "medium").strip().lower(),
    }


def generate_tender_list(profile: dict, user_input: str) -> str:
    """
    Use Google Search to produce a short list of open tenders.
    """
    keywords = profile.get("keywords", [])
    keyword_text = ", ".join(keywords[:8]) if keywords else user_input

    prompt = f"""
Use Google Search to find up to 3 open Australian Government tenders relevant to:
{keyword_text}

Return Markdown ONLY in this format:

🎣 Found **X open tenders** that match your capabilities:

---

🎯 **[Tender title — Agency](link)**
Closes **DATE**
*Short 1-sentence fit rationale*

⚡ **[Tender title — Agency](link)**
Closes **DATE**
*Short 1-sentence fit rationale*

🤷 **[Tender title — Agency](link)**
Closes **DATE**
*Short 1-sentence fit rationale*

If you cannot find tenders, say so directly and suggest the user provide more detail.
""".strip()

    client = _client()
    config = types.GenerateContentConfig(
        temperature=0.4,
        tools=[types.Tool(google_search=types.GoogleSearch())],
    )
    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt,
        config=config,
    )
    return (getattr(response, "text", "") or "").strip()


def insights_markdown(keywords: list[str]) -> str:
    categories = insights.match_categories(keywords)
    summary = insights.category_summary(categories)

    if not categories or summary["contract_count"] == 0:
        return (
            "💰 **Historical spend insights**\n\n"
            "I couldn't map your capabilities to the dataset categories yet. "
            "Give me a bit more detail on your services or industries, and I'll pull spend patterns."
        )

    lines = [
        "💰 **Here's where it gets interesting.**",
        "",
        "Looking at historical spend across your categories "
        f"*({', '.join(categories[:6])})* over the dataset:",
        "",
        "| Agency | Spend | Contracts |",
        "|---|---|---|",
    ]

    for row in summary["top_agencies"]:
        lines.append(
            f"| {row['Agency']} | {_format_money(row['total_value'])} | {int(row['contract_count'])} |"
        )

    top_suppliers = summary["top_suppliers"]
    if top_suppliers:
        winners = " · ".join(
            f"{r['Supplier Name']} ({_format_money(r['total_value'])})" for r in top_suppliers[:3]
        )
        lines.extend(["", f"**Top winners:** {winners}"])

    expiring_value = _format_money(summary["expiring_value"])
    lines.extend(
        [
            "",
            f"**{summary['expiring_count']:,} contracts worth {expiring_value} expire in the next 6 months.**",
        ]
    )

    return "\n".join(lines)


def generate_response(user_input: str) -> str:
    profile = extract_profile(user_input)
    tender_block = generate_tender_list(profile, user_input)
    insight_block = insights_markdown(profile.get("keywords", []))

    closing = (
        "\n\nWant me to dig into a specific agency, "
        "look at expiring contracts, or refine the match with more detail?"
    )

    if tender_block:
        return f"{tender_block}\n\n---\n\n{insight_block}{closing}"

    return f"{insight_block}{closing}"

