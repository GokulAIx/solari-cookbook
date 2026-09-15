"""Run one agent experiment and compare its claim with application truth."""

from __future__ import annotations

import asyncio
import os
from typing import Any
from urllib.parse import urlparse

from solari_browser import Solari

from .adapters import AgentAdapter, AgentContext, configured_agent
from .chaos import inject_network_failure_once, inject_session_expiration, inject_ui_mutation
from .storage import save_report
from .verifier import verify_cart

TASK = "Find the cheapest laptop under ₹80,000 and add it to the cart."


async def run_experiment(
    scenario: str = "none",
    agent: AgentAdapter | None = None,
    target_url: str | None = None,
) -> dict[str, Any]:
    api_key = os.environ["SOLARI_API_KEY"]
    demo_url = target_url or os.environ["DEMO_URL"]
    if not urlparse(demo_url).scheme:
        demo_url = f"https://{demo_url}"
    if urlparse(demo_url).scheme not in {"http", "https"}:
        raise ValueError("target_url must use http or https")
    events: list[dict[str, Any]] = []
    agent = agent or configured_agent(
        model=os.environ.get("GEMINI_MODEL", "gemini-2.5-flash"),
        max_steps=int(os.environ.get("MAX_STEPS", "12")),
    )

    async def emit(event: dict[str, Any]) -> None:
        events.append(event)

    async with Solari(api_key=api_key) as solari:
        async with await solari.launch() as browser:
            page = await browser.new_page()
            await page.goto(demo_url, wait_until="domcontentloaded")
            await emit({"type": "browser_started", "data": {"url": page.url}})

            if scenario == "ui_mutation":
                await emit({"type": "chaos_scheduled", "data": {"scenario": scenario}})
                await inject_ui_mutation(page, emit)
            elif scenario == "network_failure":
                await emit({"type": "chaos_scheduled", "data": {"scenario": scenario}})
                await inject_network_failure_once(page, emit)
            elif scenario == "session_expiration":
                await emit({"type": "chaos_scheduled", "data": {"scenario": scenario}})
                await inject_session_expiration(page, emit)

            result = await agent.run(AgentContext(TASK, page, browser.cdp_endpoint, demo_url), emit)
            verification = await verify_cart(page, "ThinkPad X1", 1)
            await emit({
                "type": "verification_passed" if verification.passed else "verification_failed",
                "data": {"reason": verification.reason, "quantity": verification.quantity},
            })

    if result.claimed_success and verification.passed:
        classification = "RECOVERED" if scenario != "none" else "SUCCESS"
    elif result.claimed_success and not verification.passed:
        classification = "FALSE SUCCESS"
    elif verification.passed:
        classification = "UNCERTAIN"
    else:
        classification = "FAILURE"
    report = {
        "classification": classification,
        "scenario": scenario,
        "target_url": demo_url,
        "agent": {
            "status": result.status,
            "claimed_success": result.claimed_success,
            "message": result.message,
            "steps": result.actions,
        },
        "verification": {
            "passed": verification.passed,
            "product": verification.product,
            "quantity": verification.quantity,
            "reason": verification.reason,
        },
        "events": events,
    }
    database_path = os.environ.get("RUN_DB_PATH")
    if database_path:
        report["run_id"] = save_report(report, database_path)
    return report


if __name__ == "__main__":
    scenario = os.environ.get("CHAOS_SCENARIO", "none")
    report = asyncio.run(run_experiment(scenario))
    print(f"classification: {report['classification']}")
    print(f"agent_claimed_success: {report['agent']['claimed_success']}")
    print(f"verification_passed: {report['verification']['passed']}")
    print(f"events: {len(report['events'])}")