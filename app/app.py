"""
app/app.py — TenderTrawl chat UI.

Run locally (from project root):
    python app/app.py

Deploy to Modal:
    modal serve app/deploy.py
    modal deploy app/deploy.py
"""

import json
import os
import sys
import time
import uuid
import warnings
from datetime import datetime, timezone

# Locate 'trawl' package. In Modal it sits next to app.py at /root/trawl;
# locally it's one level up from app/ at the project root.
_HERE = os.path.dirname(os.path.abspath(__file__))
for _candidate in (_HERE, os.path.dirname(_HERE)):
    if os.path.isdir(os.path.join(_candidate, "trawl")):
        if _candidate not in sys.path:
            sys.path.insert(0, _candidate)
        break

import gradio as gr
from dotenv import load_dotenv

from trawl import llm

# Suppress Gradio 5→6 migration warnings (theme/css stay in Blocks for Modal compat)
warnings.filterwarnings("ignore", category=DeprecationWarning, message=".*Gradio 6")

load_dotenv()

# Current open tenders from tenders.gov.au (updated Feb 2026)
EXAMPLE_PROMPTS = [
    "Health survey fieldwork — anthropometric screening and data collection",
    "Environmental consulting — catchment modelling and water quality",
    "International development program management — Southeast Asia",
]

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

_SESSION_ID = str(uuid.uuid4())[:8]
_LOG_DIR: str | None = None


def _log_event(event: dict) -> None:
    if not _LOG_DIR:
        return
    try:
        os.makedirs(_LOG_DIR, exist_ok=True)
        log_path = os.path.join(_LOG_DIR, "tendertrawl_logs.jsonl")
        with open(log_path, "a") as f:
            f.write(json.dumps({**event, "session": _SESSION_ID}) + "\n")
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Chat handler
# ---------------------------------------------------------------------------

def respond(message: str, history: list):
    if not message.strip():
        yield history, "", gr.update()
        return

    history = list(history) + [{"role": "user", "content": message.strip()}]
    yield history, "", gr.update(visible=False)

    # Status: casting
    history = history + [{"role": "assistant", "content": "🎣 Casting the net..."}]
    yield history, "", gr.update(visible=False)
    time.sleep(0.7)

    # Status: checking catch
    history[-1]["content"] = "🎣 Casting the net...\n\n💰 Checking the catch..."
    yield history, "", gr.update(visible=False)
    time.sleep(0.5)

    try:
        full_response, has_tenders = llm.generate_response(message.strip())
        _log_event({
            "ts": datetime.now(timezone.utc).isoformat(),
            "event": "query",
            "query": message.strip(),
            "has_tenders": has_tenders,
            "response_chars": len(full_response),
        })
    except Exception as exc:
        detail = str(exc).strip().replace("\n", " ")
        if len(detail) > 220:
            detail = detail[:220] + "..."
        full_response = (
            "⚠️ I couldn't reach the LLM right now. "
            f"Error: {exc.__class__.__name__}: {detail}. "
            "Check your GEMINI_API_KEY in .env and try again."
        )
        has_tenders = False

    # Stream word by word
    words = full_response.split(" ")
    accumulated = ""
    for i, word in enumerate(words):
        accumulated += word + " "
        history[-1]["content"] = accumulated.rstrip()
        if i % 4 == 0:
            yield history, "", gr.update(visible=False)
            time.sleep(0.018)

    history[-1]["content"] = accumulated.rstrip()
    yield history, "", gr.update(visible=has_tenders)


def _draft_clicked():
    _log_event({
        "ts": datetime.now(timezone.utc).isoformat(),
        "event": "draft_cta_clicked",
    })
    gr.Info("Coming soon! Bid writing is on the roadmap — drop us a note at mmetrics.ai 🚀")


# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------

CSS = """
.gradio-container { max-width: 860px !important; margin: auto !important; }
.message-wrap { font-size: 0.95rem; }
footer { display: none !important; }
/* Hide chatbot per-message action buttons and built-in header buttons */
.message-buttons { display: none !important; }
button[aria-label="Clear"] { display: none !important; }
"""

HEADER = """\
# 🐟 TenderTrawl
**Tell me what your business does — or paste a URL. I'll show you what's open and where the money's been.**
"""


def create_demo(log_dir: str | None = None) -> gr.Blocks:
    global _LOG_DIR
    _LOG_DIR = log_dir

    with gr.Blocks(
        title="TenderTrawl",
        theme=gr.themes.Monochrome(),
        css=CSS,
    ) as demo:

        gr.Markdown(HEADER)

        with gr.Row():
            msg = gr.Textbox(
                placeholder="Describe your business or paste a capabilities URL...",
                lines=1,
                max_lines=4,
                scale=9,
                show_label=False,
                container=False,
                autofocus=True,
            )
            btn = gr.Button("🎣 Trawl", scale=1, variant="primary", min_width=100)

        gr.Examples(
            examples=EXAMPLE_PROMPTS,
            inputs=[msg],
            label="Try one of these to see a demo:",
        )

        chatbot = gr.Chatbot(
            value=[],
            type="messages",
            height=460,
            show_label=False,
            render_markdown=True,
            allow_tags=False,
            show_copy_button=False,
            show_share_button=False,
        )

        draft_btn = gr.Button(
            "📝 Draft a tender response →",
            visible=False,
            size="sm",
            variant="secondary",
        )

        gr.ClearButton(
            components=[msg, chatbot],
            value="Clear",
            size="sm",
            variant="secondary",
        )

        gr.Markdown(
            "_Data: [AusTender](https://www.tenders.gov.au) · "
            "Prototype by [mmetrics.ai](https://mmetrics.ai)_",
        )

        msg.submit(respond, [msg, chatbot], [chatbot, msg, draft_btn])
        btn.click(respond, [msg, chatbot], [chatbot, msg, draft_btn])
        draft_btn.click(_draft_clicked, [], [])

    return demo


if __name__ == "__main__":
    demo = create_demo(log_dir="logs")
    demo.launch()
