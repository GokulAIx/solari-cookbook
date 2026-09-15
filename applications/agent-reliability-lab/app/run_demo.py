"""Run the real Gemini/LangGraph agent against the public demo."""

import asyncio
import os
from urllib.parse import urlparse

from solari_browser import Solari

from .agent import BrowserAgent


async def run_demo(task: str = "Find the cheapest laptop under ₹80,000 and add it to the cart.") -> None:
    api_key = os.environ.get("SOLARI_API_KEY")
    demo_url = os.environ.get("DEMO_URL")
    if not api_key:
        raise RuntimeError("SOLARI_API_KEY is required")
    if not demo_url:
        raise RuntimeError("DEMO_URL is required")
    if not os.environ.get("GOOGLE_API_KEY"):
        raise RuntimeError("GOOGLE_API_KEY is required")
    if not urlparse(demo_url).scheme:
        demo_url = f"https://{demo_url}"

    async with Solari(api_key=api_key) as solari:
        async with await solari.launch() as browser:
            page = await browser.new_page()
            await page.goto(demo_url, wait_until="domcontentloaded")

            agent_result = await BrowserAgent(
                page,
                model=os.environ.get("GEMINI_MODEL", "gemini-2.5-flash"),
                max_steps=int(os.environ.get("MAX_STEPS", "12")),
            ).run(task)

            print(f"agent_status: {agent_result.status}")
            print(f"agent_claimed_success: {agent_result.claimed_success}")
            print(f"agent_message: {agent_result.message}")
            print(f"agent_steps: {agent_result.actions}")

    print("cleanup: browser session released")


if __name__ == "__main__":
    asyncio.run(run_demo())