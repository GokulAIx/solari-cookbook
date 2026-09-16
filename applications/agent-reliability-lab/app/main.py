"""Minimal FastAPI entry point for an agent run."""

import asyncio
import os
import sys
from pathlib import Path
from urllib.parse import urlparse

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv
from pydantic import BaseModel
from starlette.requests import Request
from solari_browser import Solari

from .adapters import AgentContext, configured_agent
from .experiment import run_experiment
from .storage import get_report, list_reports

if sys.platform == "win32" and hasattr(asyncio, "WindowsProactorEventLoopPolicy"):
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

load_dotenv()

app = FastAPI(title="Agent Reliability Lab")
APP_ROOT = Path(__file__).resolve().parents[1]
app.mount("/static", StaticFiles(directory=APP_ROOT / "app" / "static"), name="static")
templates = Jinja2Templates(directory=APP_ROOT / "app" / "templates")


class RunRequest(BaseModel):
    task: str
    target_url: str | None = None


class ExperimentRequest(BaseModel):
    scenario: str = "none"
    target_url: str | None = None


def database_path() -> str:
    return os.environ.get("RUN_DB_PATH", str(APP_ROOT / "data" / "runs.db"))


@app.get("/")
async def dashboard(request: Request):
    reports = list_reports(database_path())
    latest_by_scenario = {}
    for report in reports:
        latest_by_scenario.setdefault(report["scenario"], report["classification"])
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "reports": reports,
            "latest_by_scenario": latest_by_scenario,
            "config_target_url": os.environ.get("DEMO_URL", ""),
        },
    )


@app.post("/runs")
async def create_run(request: RunRequest) -> dict[str, object]:
    api_key = os.environ.get("SOLARI_API_KEY")
    demo_url = os.environ.get("DEMO_URL")
    if not api_key or not demo_url or not os.environ.get("GOOGLE_API_KEY"):
        raise HTTPException(status_code=500, detail="Server agent configuration is incomplete")
    if not urlparse(demo_url).scheme:
        demo_url = f"https://{demo_url}"
    try:
        async with Solari(api_key=api_key) as solari:
            async with await solari.launch() as browser:
                page = await browser.new_page()
                await page.goto(demo_url, wait_until="domcontentloaded")
                result = await configured_agent(
                    model=os.environ.get("GEMINI_MODEL", "gemini-2.5-flash"),
                    max_steps=int(os.environ.get("MAX_STEPS", "12")),
                ).run(AgentContext(request.task, page, browser.cdp_endpoint, demo_url))
                return {
                    "status": result.status,
                    "message": result.message,
                    "claimed_success": result.claimed_success,
                    "steps": result.actions,
                }
    except Exception as error:
        raise HTTPException(status_code=502, detail=f"Agent run failed: {error}") from error


@app.post("/experiments")
async def create_experiment(request: ExperimentRequest) -> dict[str, object]:
    os.environ["RUN_DB_PATH"] = database_path()
    try:
        return await run_experiment(request.scenario, target_url=request.target_url)
    except Exception as error:
        raise HTTPException(status_code=502, detail=f"Experiment failed: {error}") from error


@app.get("/experiments/{run_id}")
async def read_experiment(run_id: str) -> dict[str, object]:
    report = get_report(run_id, database_path())
    if report is None:
        raise HTTPException(status_code=404, detail="Experiment not found")

    return {
        "run_id": run_id,
        **report,
    }