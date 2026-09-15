---

# Agent Reliability Lab — Final Build Specification

## 0. Product

**Name**

`Agent Reliability Lab`

**Repository**

```text
agent-reliability-lab
```

**One-line description**

> A chaos-testing and verification harness for browser-based AI agents running inside Solari.

**Core idea**

```text
AI Agent
   ↓
Solari Cloud Browser
   ↓
Real task
   ↓
Controlled failure injected
   ↓
Agent attempts recovery
   ↓
Independent verifier checks actual state
   ↓
Reliability result
   ↓
AI diagnosis
```

The core principle:

> **Never trust an AI agent's claim of success until the environment independently confirms it.**

---

# 1. What we're actually building

This is **not** a general-purpose browser automation framework.

It is **not** another AI browser agent.

It is a **testing and reliability layer for browser-based AI agents**.

The agent is the system under test.

Solari provides the remote browser environment.

Our software deliberately makes that environment less friendly and measures what happens.

Conceptually:

```text
             SYSTEM UNDER TEST
             ┌───────────────┐
             │    AI Agent   │
             └───────┬───────┘
                     │
                     ▼
             ┌───────────────┐
             │ SOLARI BROWSER│
             └───────┬───────┘
                     │
              controlled chaos
                     │
          ┌──────────┼──────────┐
          ▼          ▼          ▼
       UI change   Network    Session
                    failure    expiry
          │          │          │
          └──────────┼──────────┘
                     ▼
                Agent result
                     │
                     ▼
                Verification
                     │
                     ▼
               AI diagnosis
```

---

# 2. Final technology decisions

## Backend

**Python**

Use:

```text
Python 3.11+
FastAPI
```

Python is the correct choice because Solari currently provides a first-class `solari-browser` package whose `launch()` method returns a Playwright-compatible browser. ([Solari Docs][1])

## Solari

Install:

```bash
pip install solari-browser
```

No local Chromium installation is required. The browser runs in Solari's cloud infrastructure and the Python SDK connects to it. ([Solari Docs][2])

The basic integration is:

```python
from solari_browser import Solari

async with Solari(api_key=...) as solari:
    async with await solari.launch(recording=True) as browser:
        page = await browser.new_page()
        await page.goto(...)
```

The browser exposes the Playwright surface, so navigation, locators, clicks, typing, evaluation, screenshots, waits, etc. are available. ([Solari Docs][3])

## Database

**SQLite**

No PostgreSQL.

No Redis.

No external infrastructure.

SQLite is enough for:

* runs
* events
* verification results
* analysis
* experiment configuration

## Frontend

Do **not** use Next.js.

There is no good reason to introduce a second major application stack.

Use:

```text
FastAPI
+
Jinja2 templates
+
HTMX
+
plain CSS
```

The backend remains the single application.

This keeps the architecture:

```text
Browser
   ↓
FastAPI
   ├── Agent
   ├── Solari
   ├── Chaos
   ├── Verifier
   ├── Analyzer
   └── SQLite
```

while still allowing us to build a polished dashboard.

---

# 3. Why we're using a custom demo website

We need deterministic experiments.

We will **not** use Amazon, Google Flights, LinkedIn, HubSpot, etc. as our primary demo target.

The target website is our own tiny fake ecommerce application.

Example:

```text
Demo Shop

ThinkPad X1       ₹72,999
Dell XPS          ₹84,999
MacBook Air       ₹89,999

[Add to cart]
```

The task:

> Find the cheapest laptop under ₹80,000 and add it to the cart.

Expected result:

```text
product: ThinkPad X1
price: ₹72,999
quantity: 1
```

This gives us complete control over:

* DOM
* authentication
* session state
* application state
* network behavior
* failure injection
* expected outcome

---

# 4. Final MVP architecture

This is a **single Python application**.

```text
                         ┌───────────────────────┐
                         │       Web UI          │
                         │ Jinja2 + HTMX + CSS   │
                         └───────────┬───────────┘
                                     │
                                     ▼
                         ┌───────────────────────┐
                         │       FastAPI         │
                         │                       │
                         │ Run Orchestrator      │
                         │ API / UI routes       │
                         └───────────┬───────────┘
                                     │
               ┌─────────────────────┼──────────────────┐
               │                     │                  │
               ▼                     ▼                  ▼
        ┌────────────┐        ┌────────────┐     ┌────────────┐
        │ AI Agent   │        │    Chaos   │     │ Verifier   │
        │            │        │   Engine   │     │            │
        └─────┬──────┘        └─────┬──────┘     └─────┬──────┘
              │                     │                  │
              └─────────────────────┼──────────────────┘
                                    ▼
                            ┌────────────────┐
                            │ Solari Browser │
                            │                │
                            │ Playwright     │
                            │ Recording      │
                            └───────┬────────┘
                                    │
                                    ▼
                              Demo Store
                                    │
                                    ▼
                                 SQLite
```

No microservices.

No workers.

No queue.

No Kubernetes.

No cloud database.

No separate frontend repository.

---

# 5. Repository structure

Use:

```text
agent-reliability-lab/
│
├── app/
│   ├── main.py
│   │
│   ├── api/
│   │   ├── runs.py
│   │   └── demo.py
│   │
│   ├── agent/
│   │   ├── base.py
│   │   ├── browser_agent.py
│   │   └── model.py
│   │
│   ├── chaos/
│   │   ├── base.py
│   │   ├── ui_mutation.py
│   │   ├── network_failure.py
│   │   └── session_expiration.py
│   │
│   ├── verifier/
│   │   ├── base.py
│   │   └── demo_store.py
│   │
│   ├── analysis/
│   │   └── analyzer.py
│   │
│   ├── orchestration/
│   │   └── runner.py
│   │
│   ├── events/
│   │   ├── models.py
│   │   └── store.py
│   │
│   ├── db/
│   │   ├── database.py
│   │   └── models.py
│   │
│   ├── solari/
│   │   └── client.py
│   │
│   ├── templates/
│   │   ├── base.html
│   │   ├── index.html
│   │   ├── run.html
│   │   └── components/
│   │
│   └── static/
│       └── styles.css
│
├── demo/
│   └── store/
│       ├── ...
│
├── tests/
│
├── .env.example
├── requirements.txt
├── README.md
└── run.py
```

This is enough.

---

# 6. The agent

We are building **one deliberately small browser agent**.

We are NOT building a general browser-use framework.

Interface:

```python
class Agent:
    async def run(
        self,
        context: AgentContext
    ) -> AgentResult:
        ...
```

Context:

```python
@dataclass
class AgentContext:
    task: str
    page: Page
    emit_event: Callable
```

Result:

```python
@dataclass
class AgentResult:
    status: Literal["success", "failure", "unknown"]
    final_message: str
    claimed_success: bool
    steps: int
    duration_ms: int
```

---

# 7. Agent action set

Keep it intentionally small.

```text
goto
click
type
press
wait
extract
```

The LLM receives:

```text
TASK:
Find the cheapest laptop under ₹80,000
and add it to the cart.

AVAILABLE ACTIONS:

goto(url)
click(selector)
type(selector, text)
press(key)
wait(milliseconds)
extract(selector)
```

No arbitrary Python execution.

No shell.

No unrestricted computer control.

---

# 8. Agent loop

The loop is:

```text
Observe page
    ↓
Send relevant state to LLM
    ↓
LLM chooses next action
    ↓
Execute action
    ↓
Emit event
    ↓
Repeat
```

Until:

```text
task completed
OR
task failed
OR
max steps reached
```

The agent should also be forced to produce a structured final result:

```json
{
  "status": "success",
  "message": "The ThinkPad X1 was added to the cart."
}
```

This lets us explicitly record:

```text
claimed_success = true
```

without asking another model to guess whether the agent "seemed successful."

---

# 9. Solari integration

The `solari/` module owns the Solari client.

Something conceptually like:

```python
class SolariManager:
    async def launch_browser(self, recording: bool = True):
        ...
```

Use the official Python SDK:

```text
solari-browser
```

Solari's current Python API supports:

```text
Solari
launch()
BrowserSession
new_page()
new_context()
close()
sessions.get_replay_url()
sessions.download_replay()
```

and `launch(recording=True)` enables recording for the session. ([Solari Docs][3])

Do not implement a custom remote browser layer.

---

# 10. Event system

Everything important emits an event.

```python
@dataclass
class RunEvent:
    id: str
    run_id: str
    timestamp: float
    type: str
    data: dict
```

Core event types:

```text
run_started
browser_started
page_loaded

agent_observation
agent_decision
agent_action

chaos_scheduled
chaos_injected

network_failure
dom_mutation
session_expired

agent_retry
agent_recovery

agent_claimed_success
agent_claimed_failure

verification_started
verification_passed
verification_failed

run_finished
```

Store events in SQLite.

The event stream is the raw evidence used by:

* the timeline
* metrics
* AI analysis
* debugging

---

# 11. Chaos engine

Interface:

```python
class ChaosScenario(ABC):

    @abstractmethod
    async def inject(self, context):
        ...
```

For the MVP:

### Scenario 1 — UI Mutation

**Primary demo scenario.**

Example:

```html
Normal:
<button>Add to cart</button>
```

During chaos:

```html
<button>Add to basket</button>
```

Or:

* remove the exact selector
* rename visible text
* re-render the component
* alter the DOM structure

The goal:

> The environment changes underneath the agent.

This is the scenario we optimize the demo around.

---

# 12. Scenario 2 — Network Failure

Inject a controlled temporary failure against a relevant application request.

Example:

```text
GET /cart
      ↓
delay
      ↓
failure
```

Properties:

```text
controlled
temporary
reproducible
```

Don't take down the entire browser.

Use the Playwright capabilities available through Solari rather than building an independent proxy layer. Solari's browser is Playwright-compatible. ([Solari Docs][4])

---

# 13. Scenario 3 — Session Expiration

Our demo application contains deliberately simple authentication state.

Flow:

```text
Agent enters application
        ↓
Agent performs work
        ↓
Session becomes invalid
        ↓
Agent performs next action
```

The application responds:

```text
401 / session expired
```

A robust agent should recognize this and recover.

---

# 14. Chaos scheduling

Chaos must be deterministic.

Example:

```python
ChaosConfig(
    scenario="ui_mutation",
    trigger="after_action",
    action_index=4,
    seed=12345
)
```

Store:

```text
run_id
experiment_seed
scenario
trigger
action_index
```

No random:

> "At some random point we'll break the browser."

The experiment must be reproducible.

---

# 15. The verifier

This is the most important subsystem.

The verifier operates independently of the agent.

Interface:

```python
class Verifier:
    async def verify(
        self,
        context: VerificationContext
    ) -> VerificationResult:
        ...
```

For the demo store:

```text
Expected:

product = ThinkPad X1
quantity = 1
price = ₹72,999
```

The verifier checks the **actual application state**.

It does NOT ask:

> "Agent, did you succeed?"

It queries the application.

---

# 16. Verification result

Example:

```json
{
  "passed": true,
  "assertions": [
    {
      "name": "correct_product",
      "passed": true
    },
    {
      "name": "correct_quantity",
      "passed": true
    },
    {
      "name": "correct_price",
      "passed": true
    }
  ]
}
```

---

# 17. The signature feature: false success

Suppose the agent produces:

> "The ThinkPad X1 was successfully added to the cart."

But the verifier finds:

```text
cart = []
```

Then:

```text
Agent claimed SUCCESS
        +
Verification FAILED
        =
FALSE SUCCESS
```

This is the central concept of the product.

The UI should make this impossible to miss.

```text
⚠ FALSE SUCCESS

The agent reported success.

Independent verification found:
Cart was empty.
```

This is much stronger than simply saying:

> Test failed.

---

# 18. Run classification

Every run gets one classification.

### SUCCESS

```text
Agent succeeds
+
Verifier passes
```

### RECOVERED

```text
Chaos injected
+
Agent encounters failure
+
Agent adapts
+
Verifier passes
```

### FAILURE

```text
Chaos injected
+
Agent cannot complete task
+
Verifier fails
```

### FALSE SUCCESS

```text
Agent claims success
+
Verifier fails
```

### UNCERTAIN

```text
Agent stops
+
Final environment is ambiguous
```

---

# 19. Metrics

Keep metrics minimal.

### Task success rate

```text
successful_runs / total_runs
```

### Recovery rate

```text
successful_recoveries / runs_with_chaos
```

### False-success rate

```text
false_successes / total_runs
```

### Average completion time

```text
total_duration / total_runs
```

### Average actions

```text
total_actions / total_runs
```

Nothing more for the MVP.

---

# 20. Reliability score

We can have one composite score for the UI, but it must explicitly be labeled:

> **Reliability Score — internal heuristic**

It is not an industry benchmark.

Example:

```text
100
- task failures
- false successes
- poor recovery
- excessive retries
```

Don't spend engineering time making the mathematics sophisticated.

The value comes from the underlying evidence, not the score formula.

---

# 21. AI analysis

After the run, send the evidence to an LLM.

Input:

```text
Task
Chaos scenario
Agent actions
Errors
Retry behavior
Final response
Verification result
Timing
```

Prompt:

```text
Analyze this agent execution.

Determine:

1. What failed?
2. Why did it fail?
3. Did the agent recover?
4. Did it incorrectly claim success?
5. What change would most likely improve reliability?

Use only the provided execution evidence.
Do not invent events or causes.
```

Output:

```text
Failure:
The agent relied on an exact button selector.

Recovery:
No.

Cause:
After the UI changed, the agent repeated the
old action without re-observing the page.

Recommendation:
Re-observe the page after an element lookup
failure instead of blindly retrying the same selector.
```

**Important architecture rule:**

```text
Verifier → determines truth

LLM → explains truth
```

Never:

```text
LLM → determines truth
```

---

# 22. Dashboard

Only three primary screens.

## Home

```text
Agent Reliability Lab

Test browser agents against
controlled environment failures.

[ Run Experiment ]

Recent Runs
────────────────────────────────────
#104   UI Mutation       FALSE SUCCESS
#103   Network Failure   RECOVERED
#102   Session Expiry    FAILED
```

---

# 23. Run configuration

Keep it very simple.

```text
Task

[ Find the cheapest laptop under ₹80,000
  and add it to the cart. ]


Chaos

○ None
○ UI Mutation
○ Network Failure
○ Session Expiration


Failure point

After action: [ 4 ]

[ Run Experiment ]
```

No complex experiment builder.

---

# 24. Run report

This is the page we polish heavily.

Top:

```text
┌─────────────────────────────────────┐
│ Reliability Score                   │
│                                     │
│              78                     │
│                                     │
│ UI Mutation                         │
│ Result: FALSE SUCCESS               │
└─────────────────────────────────────┘
```

Then:

```text
Task
Find the cheapest laptop under ₹80,000
and add it to the cart.
```

Then execution timeline:

```text
00:00  Browser started

00:02  Agent inspected page

00:04  Agent searched laptops

00:06  Agent selected ThinkPad X1

00:08  CHAOS INJECTED
       UI mutation

00:09  Element not found

00:11  Agent retried

00:13  Agent claimed success

00:13  VERIFICATION FAILED
```

---

# 25. False-success panel

When applicable:

```text
┌─────────────────────────────────────────┐
│ ⚠ FALSE SUCCESS                         │
│                                         │
│ Agent said:                             │
│ "The laptop was added successfully."    │
│                                         │
│ Independent verification:               │
│ Cart was empty.                         │
└─────────────────────────────────────────┘
```

This should be the visual centerpiece of the demo.

---

# 26. AI diagnosis

Below the evidence:

```text
AI DIAGNOSIS

The agent failed to recover from the UI mutation.

It continued using the original selector after
the element changed instead of re-inspecting the
page.

Recommended improvement:

Re-observe the page after an interaction failure.
```

---

# 27. Solari recording/replay

This is one part of the original spec that we can now make concrete.

Launch sessions with:

```python
recording=True
```

Solari's current Python SDK exposes replay retrieval/download APIs, and the cookbook includes a Python session-recording example. Recording must be enabled when the session is created. ([GitHub][5])

After a run:

```text
[ Watch Solari Replay ]
```

When replay isn't available yet, don't make the UI fail. Show:

```text
Replay processing...
```

and retry/poll briefly.

For the public demo:

```text
Report
   ↓
Watch execution
   ↓
See chaos
   ↓
See agent behavior
   ↓
See verification
```

That is much more compelling than a static screenshot.

---

# 28. Demo application

Tiny fake ecommerce application.

Suggested routes:

```text
/
 /products
 /cart
 /login
```

State:

```text
products
cart
session
```

Models:

```python
Product:
    id
    name
    price
```

```python
CartItem:
    product_id
    quantity
```

That's enough.

Do **not** build a real ecommerce architecture.

---

# 29. Security

Environment variables:

```text
SOLARI_API_KEY=
OPENAI_API_KEY=
DATABASE_URL=sqlite:///./data/app.db
```

The Solari key stays entirely server-side.

Solari's documentation explicitly warns that the API key can access sessions/profiles and must remain private. ([Solari Docs][6])

Never send it to the frontend.

Never put it in:

* HTML
* JavaScript
* logs
* screenshots
* event payloads
* Git

---

# 30. Error handling

Every Solari session must be cleaned up.

Conceptually:

```python
browser = await solari.launch(...)

try:
    ...
finally:
    await browser.close()
```

Run states:

```text
queued
running
completed
failed
```

A failed experiment should still produce a useful run record.

---

# 31. Determinism

An experiment is defined by:

```text
task
scenario
trigger
action_index
seed
```

Save all of these.

A developer should be able to run the same experiment again.

The objective is:

```text
Same test
+
Same chaos configuration
+
Same application
≈
Same class of failure
```

Not probabilistic chaos for its own sake.

---

# 32. Demo shortcuts

On the dashboard, provide:

```text
[ UI Mutation Demo ]

[ Network Failure Demo ]

[ Session Expiration Demo ]
```

These should preconfigure the experiment.

The reviewer shouldn't have to understand the product before seeing it work.

---

# 33. The "wow" demo

The entire public demonstration can be around 60 seconds.

### 0–5 sec

```text
Task:
Find cheapest laptop under ₹80k
and add it to the cart.
```

### 5–15 sec

Agent operates Solari browser.

### 15–20 sec

```text
CHAOS INJECTED
UI MUTATION
```

### 20–30 sec

Agent encounters the changed environment.

### 30–35 sec

Agent says:

> "Successfully added the laptop."

### 35–40 sec

Verifier:

```text
❌ FALSE SUCCESS
```

### 40–50 sec

Show diagnosis:

```text
Agent claimed success.
Application state disagreed.
```

### 50–60 sec

Show Solari replay.

That's the pitch.

---

# 34. What we explicitly are NOT building

```text
❌ User authentication
❌ Teams
❌ Organizations
❌ Billing
❌ Stripe
❌ SaaS subscriptions
❌ Redis
❌ Kafka
❌ Celery
❌ Kubernetes
❌ Microservices
❌ Multi-agent orchestration
❌ 20 chaos scenarios
❌ Generic browser-control framework
❌ Mobile testing
❌ Solari sandbox integration
❌ Solari desktop integration
❌ Production agent ingestion
❌ ML-based reliability scoring
❌ Custom video infrastructure
```

The current Solari platform supports browsers, sandboxes and desktops, but **our MVP is intentionally browser-only**. Solari's own cookbook treats these as distinct execution environments. ([GitHub][5])

---

# 35. Why browser-only?

Because that's enough to demonstrate the fundamental problem:

```text
AI agent
   ↓
remote browser
   ↓
changing environment
   ↓
agent reliability
```

Adding desktops and sandboxes would increase scope without improving our core demonstration.

Future expansion can be:

```text
Browser reliability
       ↓
Desktop/computer-use reliability
       ↓
Sandbox/code-agent reliability
```

But not now.

---

# 36. Differentiation

There are already Solari cookbook submissions around browser QA, perturbation, GUI assertions, watchdogs, and self-healing workflows. The cookbook itself currently contains dozens of runnable examples and an active contribution stream. ([GitHub][5])

Therefore our pitch is **not**:

> "I built browser testing."

It is:

> **"I built a reliability lab that deliberately breaks the environment an AI agent is operating in, measures whether the agent recovers, and independently verifies whether its claimed success actually happened."**

The important differentiator:

```text
Chaos
+
Recovery measurement
+
Independent ground truth
+
False-success detection
```

---

# 37. README positioning

```markdown
# Agent Reliability Lab

### Chaos testing for AI agents.

AI agents can say "done" when nothing actually happened.

Agent Reliability Lab runs browser agents inside Solari,
deliberately introduces controlled failures, records their
behavior, and independently verifies whether the requested
task actually succeeded.

> Never trust an agent's "done" until the environment agrees.
```

Then immediately show the demo GIF/video.

---

# 38. Architecture diagram for README

```text
                    AI AGENT
                        │
                        ▼
                 SOLARI BROWSER
                        │
               ┌────────┴────────┐
               │                 │
               ▼                 ▼
         CHAOS ENGINE        EVENT STREAM
               │                 │
               └────────┬────────┘
                        ▼
                    VERIFIER
                        │
                        ▼
                RELIABILITY REPORT
                        │
                        ▼
                  AI DIAGNOSIS
```

---

# 39. Acceptance criteria

## Core

* [ ] Solari Python browser launches.
* [ ] Remote browser successfully opens demo site.
* [ ] Agent completes normal task.
* [ ] Events are persisted.
* [ ] Run report is displayed.

## Chaos

* [ ] UI mutation works.
* [ ] Network failure works.
* [ ] Session expiration works.

## Verification

* [ ] Actual application state is independently checked.
* [ ] False success is detected.
* [ ] Recovery is classified.
* [ ] Assertions explain why verification passed/failed.

## AI

* [ ] LLM produces diagnosis.
* [ ] Diagnosis uses only recorded evidence.
* [ ] Recommendations are displayed.

## Solari

* [ ] Recording can be enabled.
* [ ] Replay URL/download can be retrieved.
* [ ] Replay failure does not break the report.

## Product

* [ ] One-command local setup.
* [ ] One-click demo.
* [ ] Clean README.
* [ ] `.env.example`.
* [ ] No secrets committed.

---

# 40. Definition of done

After setup:

```bash
pip install -r requirements.txt
python run.py
```

open:

```text
http://localhost:8000
```

click:

```text
UI Mutation Demo
```

and see:

```text
Agent executes task
        ↓
Chaos injected
        ↓
Environment changes
        ↓
Agent struggles
        ↓
Agent claims success
        ↓
Verifier checks reality
        ↓
FALSE SUCCESS
        ↓
AI explains why
        ↓
Solari replay
```

That is enough.

---

# 41. Build order

This is the **final implementation order**:

### Phase 1 — Solari proof of life

First prove:

```text
Python
 ↓
solari-browser
 ↓
cloud browser
 ↓
demo site
 ↓
interaction
 ↓
cleanup
```

Do not build the dashboard yet.

The official Python SDK currently makes this straightforward via `pip install solari-browser` and `Solari.launch()`. ([Solari Docs][2])

### Phase 2 — Demo store

Create the deterministic ecommerce app.

### Phase 3 — Basic agent

Make:

```text
Task → Agent → Solari → Cart
```

work **without chaos**.

### Phase 4 — Event logging

Record every meaningful action.

### Phase 5 — Independent verifier

Make ground-truth verification work.

### Phase 6 — UI mutation

This is the first real chaos experiment.

### Phase 7 — Run report

Build the timeline and false-success UI.

### Phase 8 — AI diagnosis

Add LLM analysis.

### Phase 9 — Network failure

Add second chaos scenario.

### Phase 10 — Session expiration

Add third chaos scenario.

### Phase 11 — Solari replay

Integrate recording/replay into the report.

### Phase 12 — Polish

README, architecture diagram, demo flow, screenshots, demo video.

**Do not start Phase 2 until Phase 1 actually works.**

---

# 42. Time budget

Target:

```text
Phase 1 — Solari integration      30–60 min
Phase 2 — Demo store              45–60 min
Phase 3 — Agent                  ~2 hours
Phase 4 — Events                  ~45 min
Phase 5 — Verifier                ~45 min
Phase 6 — UI mutation             ~60 min
Phase 7 — Report                  ~60 min
Phase 8 — AI analysis             ~45 min
Phase 9/10 — Other chaos          ~60–90 min
Phase 11/12 — replay + polish      ~60 min
```

Roughly:

**8–10 focused hours.**

If one feature starts consuming disproportionate time, **cut it**.

---

# 43. Future roadmap — not MVP

```text
V2

- More chaos primitives
- Regression testing
- CI integration
- GitHub PR checks
- Reliability benchmarks
- Scheduled experiments
- Historical reliability trends
- Agent-to-agent comparison
- Desktop/computer-use testing
- Sandbox/code-agent testing
- Production trace ingestion
```

Do not implement these now.

---

# 44. Final product philosophy

> **Small surface area. Strong engineering. Excellent demo.**

We're not trying to build:

> "The Datadog for AI agents."

We're trying to build:

> **The smallest convincing demonstration that autonomous browser agents need a reliability-testing layer.**

The conceptual difference is:

```text
Traditional automation

Action
  ↓
Expected result


AI browser agent

Action
  ↓
Changing environment
  ↓
Uncertain behavior
  ↓
Maybe recovered
  ↓
Maybe falsely claimed success
```

Our product occupies that missing layer:

```text
                 AI AGENT
                     │
                     ▼
            ┌─────────────────┐
            │ AGENT RELIABILITY│
            │       LAB        │
            └─────────────────┘
               ▲      ▲      ▲
               │      │      │
             chaos  events  verify
               │      │      │
               └──────┼──────┘
                      │
                      ▼
                SOLARI BROWSER
```

### Final one-sentence pitch

> **AI agents can say "done" even when nothing actually happened. Agent Reliability Lab deliberately breaks their environment and independently checks whether they're telling the truth.**

---

## So, yes — we're now on the same page

The major decisions are now locked:

**Python, not TypeScript.**
**FastAPI, not Next.js as the application.**
**`solari-browser`, not the TypeScript SDK.**
**Solari cloud browser only for MVP.**
**Custom deterministic ecommerce site.**
**Standalone project.**
**SQLite.**
**Three chaos scenarios, with UI mutation as the hero demo.**
**Independent verifier is the central technical differentiator.**
**LLM explains failures; it does not determine whether the agent succeeded.**
**Solari recording/replay is used rather than building our own video system.**
**One monolithic application, no unnecessary infrastructure.**


[1]: https://docs.getsolari.com/browser-languages?utm_source=chatgpt.com "Browser SDKs & Languages · Solari Docs"
[2]: https://docs.getsolari.com/sdk/python?utm_source=chatgpt.com "Python SDK · Solari Docs"
[3]: https://docs.getsolari.com/sdk/python/browser?utm_source=chatgpt.com "Python SDK: Browsers · Solari Docs"
[4]: https://docs.getsolari.com/browser-api?utm_source=chatgpt.com "Driving the browser · Solari Docs"
[5]: https://github.com/solari-sdk/solari-cookbook/?utm_source=chatgpt.com "GitHub - solari-sdk/solari-cookbook · GitHub"
[6]: https://docs.getsolari.com/quickstart?utm_source=chatgpt.com "Quickstart · Solari Docs"
