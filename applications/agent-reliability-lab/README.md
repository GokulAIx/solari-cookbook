# Agent Reliability Lab

Agent Reliability Lab is an experimental reliability-testing application built on Solari. Solari provides the remote browser execution environment; this application deliberately introduces controlled failures, measures agent recovery, and independently verifies the actual application state.

The Gemini/LangGraph browser agent included here is a reference subject under test, not the product itself. The product is the reliability layer around Solari-powered agents.

## Phase 1

Phase 1 proves the smallest end-to-end path:

```text
Python -> Solari -> cloud browser -> public demo -> Playwright interaction -> cleanup
```

The demo is a static site in `demo/`. Deploy that directory as a Vercel project and set its public URL in `DEMO_URL`.

## Run the smoke test

Requirements: Python 3.11+ and a Solari API key.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install .
```

Set the environment variables in the current PowerShell session:

```powershell
$env:SOLARI_API_KEY = "slr_live_..."
$env:DEMO_URL = "https://your-demo.vercel.app"
python -m app.smoke
```

## Run the LLM agent

Once the updated demo is deployed, run the Gemini/LangGraph browser agent:

```powershell
.venv\Scripts\Activate.ps1
python -m app.run_demo
```

The agent receives the natural-language task, observes the page, chooses browser tools, and iterates until it claims success or reaches `MAX_STEPS`. The independent verifier remains a separate component and is not used by the agent to decide whether it succeeded.

## Run an experiment

Run the baseline:

```powershell
.venv\Scripts\python.exe -m app.experiment
```

Run the first controlled UI mutation:

```powershell
$env:CHAOS_SCENARIO = "ui_mutation"
.venv\Scripts\python.exe -m app.experiment
```

Run a one-time network failure against the cart request:

```powershell
$env:CHAOS_SCENARIO = "network_failure"
.venv\Scripts\python.exe -m app.experiment
```

Expire the session before the agent acts:

```powershell
$env:CHAOS_SCENARIO = "session_expiration"
.venv\Scripts\python.exe -m app.experiment
```

The report compares the agent claim with independent application state and classifies the run as `SUCCESS`, `RECOVERED`, `FAILURE`, `FALSE SUCCESS`, or `UNCERTAIN`.

The experiment runner targets the `AgentAdapter` contract. The included Gemini/LangGraph implementation is the reference adapter used by the demo; the reliability layer is designed to test other agents through the same boundary.

### Connect a customer agent

The lab can call a customer-owned agent service instead of the reference agent. Configure this on the server only:

```env
AGENT_ADAPTER=http
CUSTOM_AGENT_URL=https://customer-agent.example.com/agent/run
CUSTOM_AGENT_TOKEN=server_only_shared_secret
```

The lab sends the task and the live Solari `cdp_endpoint` to that server over HTTPS with an optional bearer token. The customer agent drives the browser through CDP and returns JSON such as:

```json
{"status":"success","message":"Task completed","steps":7,"claimed_success":true,"events":[]}
```

The CDP endpoint is a secret. It is never rendered in the dashboard, sent to the browser UI, or written to the report. Chaos injection, verification, classification, and persistence remain owned by the lab.

The dashboard can also send a different `target_url` for an experiment. The current verifier and UI/session scenarios target the demo store contract; a customer website needs its own verifier contract that defines what success means for that application. Network interception is the most portable first scenario.

### What is CDP?

CDP is the Chrome DevTools Protocol, the browser control protocol used to inspect and drive a live Chromium session. Solari gives each browser session a private CDP endpoint. A customer agent uses that endpoint to connect to the exact browser session created by the lab. The endpoint stays server-side and is never shown in the dashboard.

The target URL is the execution target, not automatically ground truth. The lab must never infer success from a generic button click or from the agent's final message.

Experiment reports can be persisted in SQLite by setting `RUN_DB_PATH` (the FastAPI experiment endpoint defaults to `data/runs.db`). The stored report includes the classification, agent claim, verifier result, and event evidence.

To run the FastAPI entry point:

```powershell
python -m app.server
```

Then post a task to `POST /runs` with JSON such as:

```json
{"task":"Find the cheapest laptop under ₹80,000 and add it to the cart."}
```

Expected output:

```text
page: Solari Demo Store
interaction: ThinkPad X1 added to cart
cleanup: browser session released
```

The API key stays server-side. Do not put it in the demo site or commit a populated `.env` file. This application does not modify Solari or claim to be an official Solari feature.

## Deploy the demo to Vercel

Create a Vercel project whose root directory is `demo/`, or deploy the directory directly with the Vercel CLI:

```powershell
vercel demo
```

Copy the resulting public URL into `DEMO_URL`. The cloud browser must be able to reach this URL; a local `localhost` URL will not work.