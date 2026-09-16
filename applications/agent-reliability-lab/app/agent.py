"""LLM-driven browser agent implemented as a bounded LangGraph loop."""

from __future__ import annotations

import json
from typing import Annotated, Any, Awaitable, Callable, Literal, TypedDict

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_core.tools import BaseTool, tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from patchright.async_api import Page

from .models import AgentResult

EventHandler = Callable[[dict[str, Any]], Awaitable[None] | None]


class AgentState(TypedDict, total=False):
    messages: Annotated[list[BaseMessage], add_messages]
    task: str
    action_history: list[dict[str, Any]]
    step_count: int
    final_status: Literal["success", "failure"]
    final_message: str


SYSTEM_PROMPT = """You are a browser task agent operating a remote browser.

Complete the user's task by observing the current page and choosing browser tools.
Use tools for every browser interaction. Do not claim success until you have taken
the action that completes the task and observed the resulting page. When finished,
call finish with status success or failure and a concise message. If an action
fails, observe again and adapt instead of repeating blindly. Never invent page
content, tool results, or application state.
"""


class BrowserAgent:
    def __init__(
        self,
        page: Page,
        *,
        model: str = "gemini-2.5-flash",
        max_steps: int = 12,
        on_event: EventHandler | None = None,
    ) -> None:
        self.page = page
        self.max_steps = max_steps
        self.on_event = on_event
        self.tools = self._build_tools()
        self.llm = ChatGoogleGenerativeAI(model=model, temperature=0)
        self.graph = self._build_graph()

    async def run(self, task: str) -> AgentResult:
        state: AgentState = {
            "task": task,
            "messages": [SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=task)],
            "action_history": [],
            "step_count": 0,
        }
        result = await self.graph.ainvoke(state)
        status = result.get("final_status", "failure")
        message = result.get("final_message", "The agent reached its step limit.")
        return AgentResult(status == "success", message, result.get("step_count", 0), status)

    async def _emit(self, event_type: str, data: dict[str, Any]) -> None:
        if self.on_event is None:
            return
        outcome = self.on_event({"type": event_type, "data": data})
        if outcome is not None:
            await outcome

    def _build_tools(self) -> list[BaseTool]:
        page = self.page

        @tool
        async def observe() -> str:
            """Read the current URL and visible text from the page."""
            text = await page.locator("body").inner_text()
            result = f"URL: {page.url}\nVISIBLE TEXT:\n{text[:8000]}"
            await self._emit("agent_observation", {"url": page.url, "text": text[:8000]})
            return result

        @tool
        async def goto(url: str) -> str:
            """Navigate to a URL when the task requires a different page."""
            response = await page.goto(url, wait_until="domcontentloaded")
            result = f"Navigated to {page.url} (status {response.status if response else 'unknown'})."
            await self._emit("agent_action", {"tool": "goto", "url": url, "result": result})
            return result

        @tool
        async def click(target: str) -> str:
            """Click a visible element by accessible name or exact visible text."""
            for role in ("button", "link"):
                candidate = page.get_by_role(role, name=target)
                if await candidate.count():
                    await candidate.first.click()
                    result = f"Clicked {role} named {target!r}."
                    await self._emit("agent_action", {"tool": "click", "target": target, "result": result})
                    return result
            candidate = page.get_by_text(target, exact=True)
            await candidate.first.click()
            result = f"Clicked visible text {target!r}."
            await self._emit("agent_action", {"tool": "click", "target": target, "result": result})
            return result

        @tool
        async def type_text(target: str, text: str) -> str:
            """Fill a text field by label, placeholder, or CSS selector."""
            candidate = page.get_by_label(target)
            if not await candidate.count():
                candidate = page.get_by_placeholder(target)
            if not await candidate.count():
                candidate = page.locator(target)
            await candidate.first.fill(text)
            result = f"Filled {target!r}."
            await self._emit("agent_action", {"tool": "type_text", "target": target, "result": result})
            return result

        @tool
        async def press(key: str) -> str:
            """Press a keyboard key on the current page."""
            await page.keyboard.press(key)
            result = f"Pressed {key}."
            await self._emit("agent_action", {"tool": "press", "key": key, "result": result})
            return result

        @tool
        async def extract(selector: str) -> str:
            """Extract visible text from a CSS selector."""
            result = (await page.locator(selector).inner_text())[:4000]
            await self._emit("agent_action", {"tool": "extract", "selector": selector, "result": result})
            return result

        @tool
        async def finish(status: Literal["success", "failure"], message: str) -> str:
            """End the task with the agent's claim; this is not verification."""
            await self._emit(f"agent_claimed_{status}", {"message": message})
            return json.dumps({"status": status, "message": message})

        return [observe, goto, click, type_text, press, extract, finish]

    def _build_graph(self):
        graph = StateGraph(AgentState)
        graph.add_node("model", self._call_model)
        graph.add_node("tools", ToolNode(self.tools))
        graph.add_node("finalize", self._finalize)
        graph.add_edge(START, "model")
        graph.add_conditional_edges(
            "model",
            self._route_model,
            {"tools": "tools", "finalize": "finalize", "done": END},
        )
        graph.add_conditional_edges(
            "tools",
            self._route_tools,
            {"model": "model", "finalize": "finalize"},
        )
        graph.add_edge("finalize", END)
        return graph.compile()

    async def _call_model(self, state: AgentState) -> dict[str, Any]:
        step_count = state.get("step_count", 0) + 1
        if step_count > self.max_steps:
            return {"step_count": step_count, "final_status": "failure", "final_message": "Maximum steps reached."}
        response = await self.llm.bind_tools(self.tools).ainvoke(state["messages"])
        action_history = [
            *state.get("action_history", []),
            *[
                {"tool": call["name"], "args": call["args"]}
                for call in response.tool_calls
            ],
        ]
        await self._emit("agent_decision", {"step": step_count, "tool_calls": response.tool_calls})
        return {"messages": [response], "step_count": step_count, "action_history": action_history}

    async def _finalize(self, state: AgentState) -> dict[str, Any]:
        for message in reversed(state["messages"]):
            if not isinstance(message, AIMessage):
                continue
            for call in message.tool_calls:
                if call["name"] != "finish":
                    continue
                claimed = call["args"]
                return {
                    "final_status": claimed["status"],
                    "final_message": claimed["message"],
                }
        return {
            "final_status": "failure",
            "final_message": "The agent stopped without making a final claim.",
        }

    @staticmethod
    def _route_model(state: AgentState) -> str:
        last = state["messages"][-1]
        if state.get("final_status"):
            return "done"
        if not isinstance(last, AIMessage) or not last.tool_calls:
            return "finalize"
        if any(call["name"] == "finish" for call in last.tool_calls):
            return "finalize"
        return tools_condition(state)

    @staticmethod
    def _route_tools(state: AgentState) -> str:
        last = state["messages"][-2]
        if isinstance(last, AIMessage) and any(call["name"] == "finish" for call in last.tool_calls):
            return "finalize"
        return "model"