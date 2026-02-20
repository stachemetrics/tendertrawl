"""
app.py — TenderTrawl chat UI.

Run locally:
    python app.py

Step 3: Gradio shell with hardcoded demo responses.
Step 4 will replace DEMO_RESPONSES with live LLM + insights calls.
"""

import time
import warnings

import gradio as gr
from dotenv import load_dotenv

from trawl import llm

# Suppress Gradio 5→6 migration warnings (theme/css stay in Blocks for Modal compat)
warnings.filterwarnings("ignore", category=DeprecationWarning, message=".*Gradio 6")

load_dotenv()

EXAMPLE_PROMPTS = [
    "Canberra cyber consultancy — IRAP and cloud security",
    "Sydney civil engineering — defence facilities",
    "Radiation safety services — Lucas Heights NSW",
]


# ---------------------------------------------------------------------------
# Chat handler
# ---------------------------------------------------------------------------

def respond(message: str, history: list):
    if not message.strip():
        yield history, ""
        return
    history = list(history) + [{"role": "user", "content": message.strip()}]
    yield history, ""

    # Status: casting
    history = history + [{"role": "assistant", "content": "🎣 Casting the net..."}]
    yield history, ""
    time.sleep(0.7)

    # Status: checking catch
    history[-1]["content"] = "🎣 Casting the net...\n\n💰 Checking the catch..."
    yield history, ""
    time.sleep(0.5)

    try:
        full_response = llm.generate_response(message.strip())
    except Exception as exc:
        detail = str(exc).strip().replace("\n", " ")
        if len(detail) > 220:
            detail = detail[:220] + "..."
        full_response = (
            "⚠️ I couldn't reach the LLM right now. "
            f"Error: {exc.__class__.__name__}: {detail}. "
            "Check your GEMINI_API_KEY in .env and try again."
        )

    # Stream word by word
    words = full_response.split(" ")
    accumulated = ""
    for i, word in enumerate(words):
        accumulated += word + " "
        history[-1]["content"] = accumulated.rstrip()
        if i % 4 == 0:
            yield history, ""
            time.sleep(0.018)

    history[-1]["content"] = accumulated.rstrip()
    yield history, ""


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


def create_demo() -> gr.Blocks:
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

        msg.submit(respond, [msg, chatbot], [chatbot, msg])
        btn.click(respond, [msg, chatbot], [chatbot, msg])

    return demo


if __name__ == "__main__":
    demo = create_demo()
    demo.launch()
