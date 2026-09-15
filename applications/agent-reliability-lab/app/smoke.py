"""Prove that a Python process can drive the public demo through Solari."""

import asyncio
import os
from urllib.parse import urlparse

from solari_browser import Solari


async def run_smoke_test() -> None:
    api_key = os.environ.get("SOLARI_API_KEY")
    demo_url = os.environ.get("DEMO_URL")

    if not api_key:
        raise RuntimeError("SOLARI_API_KEY is required")
    if not demo_url:
        raise RuntimeError("DEMO_URL is required")
    if not urlparse(demo_url).scheme:
        demo_url = f"https://{demo_url}"

    async with Solari(api_key=api_key) as solari:
        async with await solari.launch() as browser:
            page = await browser.new_page()
            await page.goto(demo_url, wait_until="domcontentloaded")

            heading = await page.get_by_role("heading", name="Solari Demo Store").inner_text()
            await page.locator("#add-to-cart").click()
            confirmation = await page.get_by_role("status").inner_text()

            print(f"page: {heading}")
            print(f"interaction: {confirmation}")

    print("cleanup: browser session released")


if __name__ == "__main__":
    asyncio.run(run_smoke_test())