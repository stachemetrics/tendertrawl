"""
app/deploy.py — Modal deployment for TenderTrawl.

Run from the project root (tendertrawl/):

    Serve with hot-reload (dev):
        modal serve app/deploy.py

    Deploy to production:
        modal deploy app/deploy.py

Requires the 'gemini-secret' Modal secret to exist with GEMINI_API_KEY set.
Check with: modal secret list
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
    .add_local_file("app/app.py", "/root/app.py")
    .add_local_dir("trawl", "/root/trawl", ignore=["__pycache__", "*.pyc"])
    .add_local_file("data/cn_combined.csv", "/root/data/cn_combined.csv")
)


@app.function(
    image=image,
    max_containers=1,
    volumes={"/root/logs": volume},
    secrets=[modal.Secret.from_name("gemini-secret")],
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
