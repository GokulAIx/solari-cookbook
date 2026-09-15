# Agent Reliability Lab Context

## Product

Agent Reliability Lab is a reliability and stress-testing layer for AI agents that operate inside Solari. The agent is the subject under test. Solari is the remote execution environment. The demo ecommerce site is the controlled test environment.

The core promise is: never trust an agent's success claim until an independent verifier confirms the actual application state.

## Current Implementation

- `app/agent.py`: reference Gemini agent using LangGraph and Solari's Playwright-compatible page.
- `app/adapters.py`: reliability-layer adapter contract plus the LangGraph reference adapter.
- `app/chaos.py`: first deterministic UI mutation, renaming the primary cart action.
- `app/experiment.py`: launches Solari, schedules chaos, runs the reference agent, verifies state, collects events, and classifies the run.
- `app/verifier.py`: independent cart verifier; it does not use the agent's message.
- `app/main.py`: minimal FastAPI `POST /runs` entry point.
- `app/storage.py`: SQLite persistence for complete experiment reports.
- `app/smoke.py`: Solari connectivity smoke test.
- `demo/index.html`: public deterministic ecommerce target with three laptops and DOM-backed cart state.

## Architectural Boundaries

- The LangGraph agent is only a reference/demo subject, not the product architecture.
- The reliability runner accepts an `AgentAdapter`; LangGraph is currently one adapter implementation.
- `HttpAgentAdapter` can call a customer-owned agent service with the live Solari CDP endpoint kept server-side.
- Experiment requests can select a target URL. The reference verifier remains demo-store-specific until a customer supplies an application-specific verifier contract.
- The reliability layer owns experiment lifecycle, chaos scheduling, event collection, verification, classification, and reporting.
- Solari provides the cloud browser and Playwright-compatible control surface; this project does not modify Solari or implement browser infrastructure.
- The verifier determines ground truth. An LLM may later explain evidence but must not determine truth.

## Planned, Not Yet Implemented

- A deployed customer-agent service integration test and protocol hardening.
- A deployed customer-agent service integration test and protocol hardening.
- Solari recording/replay integration.
- Optional LLM diagnosis based only on recorded evidence.

## Development Rule

Every new feature should strengthen the demonstration that Solari can serve as an execution environment for agents and that Agent Reliability Lab can stress-test those agents with controlled, reproducible failures and independent ground-truth verification.
