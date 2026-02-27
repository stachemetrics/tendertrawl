"""
app/deploy.py — Modal deployment for TenderTrawl.

Serve locally (hot-reload):
    modal serve app/deploy.py

Deploy to production:
    modal deploy app/deploy.py

Requires a Modal secret named "tendertrawl-secrets" with GEMINI_API_KEY set.
Create it once with:
    modal secret create tendertrawl-secrets GEMINI_API_KEY=your-key-here
"""

import modal

app = modal.App("tendertrawl")

volume = modal.Volume.from_name("tendertrawl-logs", create_if_missing=True)

image = (
    modal.Image.debian_slim(python_version="3.12")
    .pip_install(
        "fastapi[standard]",
        "gradio~=5.7",
        "requests",
        "google-genai",
        "pandas",
        "openpyxl",
        "httpx",
        "beautifulsoup4",
        "python-dotenv",
    )
    .copy_local_file("app/app.py", "/root/app.py")
    .copy_local_dir("trawl", "/root/trawl")
    .copy_local_file("data/cn_combined.csv", "/root/data/cn_combined.csv")
)


@app.function(
    image=image,
    max_containers=1,
    volumes={"/root/logs": volume},
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
    demo = create_demo(log_dir="/root/logs")
    return mount_gradio_app(app=FastAPI(), blocks=demo, path="/")
