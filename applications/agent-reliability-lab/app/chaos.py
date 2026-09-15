"""Deterministic browser failures used by reliability experiments."""

from typing import Any, Awaitable, Callable

from patchright.async_api import Page

EventHandler = Callable[[dict[str, Any]], Awaitable[None] | None]


async def inject_ui_mutation(page: Page, on_event: EventHandler | None = None) -> None:
    """Rename the primary cart action without changing application state."""
    await page.evaluate(
        """() => {
            const button = document.querySelector('#add-to-cart');
            if (!button) throw new Error('primary cart button was not found');
            button.textContent = 'Add to basket';
            button.setAttribute('aria-label', 'Add to basket');
        }"""
    )
    if on_event is not None:
        outcome = on_event({"type": "chaos_injected", "data": {"scenario": "ui_mutation"}})
        if outcome is not None:
            await outcome


async def inject_network_failure_once(page: Page, on_event: EventHandler | None = None) -> None:
    """Abort the first cart request and allow later retries through."""
    state = {"failed": False}

    async def handle_route(route: Any) -> None:
        if not state["failed"]:
            state["failed"] = True
            await route.abort("failed")
            if on_event is not None:
                outcome = on_event({
                    "type": "chaos_injected",
                    "data": {"scenario": "network_failure", "request": route.request.url},
                })
                if outcome is not None:
                    await outcome
            return
        await route.continue_()

    await page.route("**/cart-result.json*", handle_route)


async def inject_session_expiration(page: Page, on_event: EventHandler | None = None) -> None:
    """Expire the demo session before the agent's first browser action."""
    await page.evaluate("() => { window.__SESSION_VALID__ = false; }")
    if on_event is not None:
        outcome = on_event({"type": "chaos_injected", "data": {"scenario": "session_expiration"}})
        if outcome is not None:
            await outcome