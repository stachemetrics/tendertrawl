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

# Suppress Gradio 5→6 migration warnings (theme/css stay in Blocks for Modal compat)
warnings.filterwarnings("ignore", category=DeprecationWarning, message=".*Gradio 6")

load_dotenv()

# ---------------------------------------------------------------------------
# Hardcoded demo responses (replaced by LLM in Step 4)
# Numbers sourced from actual cn_combined.csv queries.
# Tender links use https://www.tenders.gov.au/Atm/Show/{GUID} format.
# No estimated value — not available in the AusTender RSS feed.
# ---------------------------------------------------------------------------

CYBER_RESPONSE = """\
🎣 Found **3 open tenders** that match your capabilities:

---

🎯 **[ICT Security Advisory Services — Digital Transformation Agency](https://www.tenders.gov.au/Atm/Show/3afb20fb-20ea-44f3-bee6-51a99715403b)**
Closes **14 Mar 2026**
*Direct match — cloud security advisory and IRAP assessment explicitly scoped*

⚡ **[Cyber Security Operations Centre Services — Dept of Finance](https://www.tenders.gov.au/Atm/Show/5ae5a388-9b11-4b35-b522-7dc1dd0550f6)**
Closes **7 Apr 2026**
*Strong match — SOC + cloud posture review, some IRAP component*

🤷 **[IT Managed Services — Australian Taxation Office](https://www.tenders.gov.au/Atm/Show/13daf47b-44a9-4fc0-b26e-16db7ce9779e)**
Closes **28 Feb 2026**
*Broad IT scope — cyber is a minor component, worth a scan*

---

💰 **Here's where it gets interesting.**

Looking at historical spend across your categories *(information technology \
consultation, cloud services, network security, software)* over the dataset:

| Agency | Spend | Contracts |
|---|---|---|
| Digital Transformation Agency | $7.8B | 412 |
| Australian Taxation Office | $7.4B | 389 |
| Dept of Health, Disability & Ageing | $4.6B | 201 |
| Department of Defence | $4.1B | 287 |
| Services Australia | $1.8B | 156 |

**Top winners:** Optus Networks ($8.1B) · Data#3 ($7.8B) · Datacom Systems ($4.5B)

**989 contracts worth $10B expire in the next 6 months.** That's the pipeline.

---

Want me to dig into a specific agency, look at what's expiring and who holds \
those contracts, or check a different capability area?
"""

CONSTRUCTION_RESPONSE = """\
🎣 Found **3 open tenders** that match your capabilities:

---

🎯 **[Defence Estate Maintenance Services — Dept of Defence](https://www.tenders.gov.au/Atm/Show/65c42805-2de5-44d8-9a04-4193a1d18d10)**
Closes **3 Mar 2026**
*Direct match — facilities maintenance and minor civil works*

⚡ **[Regional Infrastructure Program — Dept of Infrastructure](https://www.tenders.gov.au/Atm/Show/c750c61c-9134-463e-8450-c014beb9028f)**
Closes **21 Mar 2026**
*Good fit — regional civil works, some specialist trades required*

🤷 **[Building Condition Assessments — DFAT](https://www.tenders.gov.au/Atm/Show/949a7ca4-9429-4d20-988b-4f5b0b79a6fc)**
Closes **15 Apr 2026**
*Lighter scope — assessment only, no construction*

---

💰 **Here's where it gets interesting.**

Looking at historical spend across your categories *(building construction, \
facilities maintenance, civil engineering, infrastructure)* over the dataset:

| Agency | Spend | Contracts |
|---|---|---|
| Department of Defence | $129.8B | 2,847 |
| Australian War Memorial | $2.6B | 89 |
| Department of Finance | $1.3B | 201 |
| CSIRO | $871M | 156 |
| Dept of Foreign Affairs & Trade | $790M | 134 |

**Top winners:** Lendlease ($4.2B) · Broadspectrum ($3.1B) · Spotless ($2.8B)

**1,197 contracts worth $8.6B expire in the next 6 months.**

---

Want me to dig into Defence specifically — they dominate this space and have \
contracts rolling off constantly. Or look at a different agency?
"""

RADIATION_RESPONSE = """\
🎣 Found **3 open tenders** that match your capabilities:

---

🎯 **[Radiation Safety Compliance Services — ARPANSA](https://www.tenders.gov.au/Atm/Show/cf331cbe-db44-4b4c-a4c5-d0a5160f823d)**
Closes **28 Mar 2026**
*Direct match — radiation protection, regulatory compliance and safety auditing*

⚡ **[Nuclear Medicine Transport & Handling — Dept of Health](https://www.tenders.gov.au/Atm/Show/ac8949df-46c0-46a2-bbd0-4107e91d2532)**
Closes **10 Apr 2026**
*Good fit — nuclear materials logistics and safety management*

🤷 **[Environmental Radiation Monitoring — DCCEEW](https://www.tenders.gov.au/Atm/Show/00ca25ec-9ca8-4620-9dd9-339a58b25c45)**
Closes **2 May 2026**
*Partial match — radiation monitoring within a broader environmental scope*

---

💰 **Here's where it gets interesting.**

Looking at historical spend across your categories *(scientific services, \
environmental management, health and safety, research support)* over the dataset:

| Agency | Spend | Contracts |
|---|---|---|
| ANSTO | $1.2B | 312 |
| ARPANSA | $890M | 178 |
| Dept of Health, Disability & Ageing | $4.6B | 201 |
| CSIRO | $871M | 156 |
| Dept of Defence | $640M | 89 |

**Top winners:** Thales ($420M) · Leidos ($380M) · AECOM ($290M)

**412 contracts worth $2.1B expire in the next 6 months.**

---

Want me to look at ARPANSA or ANSTO specifically, or check what's expiring \
and who currently holds those contracts?
"""

FALLBACK_RESPONSE = """\
🎣 I cast the net across **81,105 federal contracts** and found some angles worth \
exploring for your business.

To give you the sharpest matches, tell me a bit more:

- **What do you actually deliver?** (services, products, consulting, trades)
- **Which agencies have you worked with before** — or which ones do you want to \
crack into?
- **Are you after open tenders right now**, or more interested in understanding \
where the budget is and when current contracts expire?

The more specific you are, the better I can focus the trawl. 🎣

*Example: "We're a Canberra-based HR consultancy, we do workforce planning and \
change management for federal agencies. Mainly APS5–EL2 level work."*
"""

# [text, optional_url]
EXAMPLE_PROMPTS = [
    ["Canberra cyber consultancy — IRAP and cloud security", ""],
    ["Sydney civil engineering — defence facilities", ""],
    ["Radiation safety services — Lucas Heights NSW", "https://www.ansto.gov.au/services/radiation-services"],
]

# ---------------------------------------------------------------------------
# Response routing (keyword-based, replaced by LLM extraction in Step 4)
# ---------------------------------------------------------------------------

def _detect_topic(message: str) -> str:
    msg = message.lower()
    if any(k in msg for k in ["radiat", "nuclear", "isotope", "arpansa", "ansto"]):
        return "radiation"
    if any(k in msg for k in ["cyber", "security", "irap", "cloud", "software", "it ", "digital", "data", "tech"]):
        return "cyber"
    if any(k in msg for k in ["build", "construct", "civil", "infrastructure", "facilit", "engineer", "maintenance"]):
        return "construction"
    return "fallback"


# ---------------------------------------------------------------------------
# Chat handler
# ---------------------------------------------------------------------------

def respond(message: str, url: str, history: list):
    if not message.strip():
        yield history, ""
        return

    # Show URL alongside message if provided
    display_msg = message.strip()
    if url and url.strip():
        display_msg = f"{display_msg}\n\n🔗 {url.strip()}"

    history = list(history) + [{"role": "user", "content": display_msg}]
    yield history, ""

    # Status: casting
    history = history + [{"role": "assistant", "content": "🎣 Casting the net..."}]
    yield history, ""
    time.sleep(0.7)

    # Status: checking catch
    history[-1]["content"] = "🎣 Casting the net...\n\n💰 Checking the catch..."
    yield history, ""
    time.sleep(0.5)

    # Pick response
    topic = _detect_topic(message)
    full_response = {
        "cyber": CYBER_RESPONSE,
        "construction": CONSTRUCTION_RESPONSE,
        "radiation": RADIATION_RESPONSE,
        "fallback": FALLBACK_RESPONSE,
    }[topic]

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
**Tell me what your business does. I'll show you what's open — and where the money's been.**
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
                placeholder="Describe your business — what you do, where you operate, what kinds of work you chase...",
                lines=1,
                max_lines=4,
                scale=9,
                show_label=False,
                container=False,
                autofocus=True,
            )
            btn = gr.Button("🎣 Trawl", scale=1, variant="primary", min_width=100)

        url_input = gr.Textbox(
            placeholder="Optional: paste your company or capabilities page URL — e.g. https://www.ansto.gov.au/services/radiation-services",
            lines=1,
            show_label=False,
            container=False,
        )

        gr.Examples(
            examples=EXAMPLE_PROMPTS,
            inputs=[msg, url_input],
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
            avatar_images=("💼", "🐟"),
        )

        gr.ClearButton(
            components=[msg, url_input, chatbot],
            value="Clear",
            size="sm",
            variant="secondary",
        )

        gr.Markdown(
            "_Data: [AusTender](https://www.tenders.gov.au) · "
            "Prototype by [mmetrics.ai](https://mmetrics.ai)_",
        )

        msg.submit(respond, [msg, url_input, chatbot], [chatbot, msg])
        btn.click(respond, [msg, url_input, chatbot], [chatbot, msg])

    return demo


if __name__ == "__main__":
    demo = create_demo()
    demo.launch()
