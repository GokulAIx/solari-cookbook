"""Agent adapter boundary owned by the reliability lab."""

from __future__ import annotations

import os
from typing import Any, Awaitable, Callable, Protocol

import httpx
from patchright.async_api import Page

from .agent import BrowserAgent
from .models import AgentResult

EventHandler = Callable[[dict[str, Any]], Awaitable[None] | None]


class AgentContext:
    def __init__(self, task: str, page: Page, cdp_endpoint: str, target_url: str) -> None:
        self.task = task
        self.page = page
        self.cdp_endpoint = cdp_endpoint
        self.target_url = target_url


class AgentAdapter(Protocol):
    """Contract for any agent that the lab can test inside a browser session."""

    async def run(self, context: AgentContext, emit: EventHandler | None = None) -> AgentResult:
        ...


class LangGraphReferenceAdapter:
    """The contest demo agent; the lab remains independent of its framework."""

    def __init__(self, *, model: str, max_steps: int) -> None:
        self.model = model
        self.max_steps = max_steps

    async def run(self, context: AgentContext, emit: EventHandler | None = None) -> AgentResult:
        return await BrowserAgent(
            context.page,
            model=self.model,
            max_steps=self.max_steps,
            on_event=emit,
        ).run(context.task)


class HttpAgentAdapter:
    """Connect a customer-owned agent service to the live Solari browser."""

    def __init__(self, endpoint: str, *, timeout_seconds: float = 300) -> None:
        self.endpoint = endpoint
        self.timeout_seconds = timeout_seconds

    async def run(self, context: AgentContext, emit: EventHandler | None = None) -> AgentResult:
        payload = {
            "task": context.task,
            "target_url": context.target_url,
            "cdp_endpoint": context.cdp_endpoint,
            "warning": "This endpoint is a secret. Use it only server-side and do not log or expose it.",
        }
        headers = {}
        token = os.environ.get("CUSTOM_AGENT_TOKEN")
        if token:
            headers["authorization"] = f"Bearer {token}"
        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            response = await client.post(self.endpoint, json=payload, headers=headers)
            response.raise_for_status()
            body = response.json()

        for event in body.get("events", []):
            if emit is not None:
                outcome = emit(event)
                if outcome is not None:
                    await outcome
        return AgentResult(
            claimed_success=bool(body.get("claimed_success", body.get("status") == "success")),
            message=str(body.get("message", "Customer agent returned no message.")),
            actions=int(body.get("steps", body.get("actions", 0))),
            status=str(body.get("status", "unknown")),
        )


def configured_agent(*, model: str, max_steps: int) -> AgentAdapter:
    endpoint = os.environ.get("CUSTOM_AGENT_URL")
    if os.environ.get("AGENT_ADAPTER", "reference") == "http":
        if not endpoint:
            raise RuntimeError("CUSTOM_AGENT_URL is required when AGENT_ADAPTER=http")
        return HttpAgentAdapter(endpoint)
    return LangGraphReferenceAdapter(model=model, max_steps=max_steps)