"""Windows-safe local server launcher for the Solari/Patchright integration."""

import asyncio
import sys

import uvicorn


def main() -> None:
    if sys.platform == "win32" and hasattr(asyncio, "WindowsProactorEventLoopPolicy"):
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000)


if __name__ == "__main__":
    main()