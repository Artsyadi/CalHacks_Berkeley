# PromptToPath 🚀

**A better way of learning in the age of AI.**

PromptToPath is a multi-agent system on [Fetch.ai](https://fetch.ai) that turns *any*
learning intent — "become an ML engineer in 6 months", "learn to cook Italian food in
4 weeks", "understand transformers" — into a **personalized, time-boxed roadmap** with a
**visual diagram** and **real, validated learning resources** (YouTube videos, docs,
courses). The entire experience happens inside an **ASI:One** conversation — no custom
frontend required.

It's not another chatbot. Specialized agents **debate, research, and draw**:

- a **Planner** that runs an internal Proposer → Critic → Synthesizer debate (cross-model:
  ASI:One + Claude) so the roadmap is realistic, not generic;
- a **Resource** agent that fetches **real** links from the YouTube Data API and web search,
  then **HTTP-validates every URL** so nothing is hallucinated or dead;
- a **Graph** agent that renders the roadmap as a **Mermaid diagram + outline** in chat;
- an **Orchestrator** that coordinates them, recovers from failures, and (optionally)
  gates a "premium" roadmap behind a **sandboxed Payment Protocol**.

---

## Problem · target user · outcome

- **Problem:** Learners are drowning in content. Generic AI answers give vague advice and
  often invent links. There's no trustworthy, structured, *visual* path with verified resources.
- **Target user:** Anyone learning anything self-directed — career switchers, students,
  hobbyists.
- **Outcome:** One ASI:One message in → a phased, realistic roadmap + a visual map + a set of
  **verified** resources per topic, out.

---

## Architecture

The Orchestrator is the only agent ASI:One talks to. A `SharedAgentState` object flows
through a forward pipeline and returns to the Orchestrator for delivery (minimizes mailbox hops):

```
ASI:One user
    │  ChatMessage (Agent Chat Protocol)
    ▼
Orchestrator ──SharedAgentState──▶ Planner ──▶ Resource ──▶ Graph ──┐
    ▲                                                                │
    └──────────────── SharedAgentState (complete) ◀──────────────────┘
    │  ChatMessage: Mermaid diagram + outline + validated links
    ▼
ASI:One user
```

| Agent | Role | Key tech |
|-------|------|----------|
| **Orchestrator** | Chat Protocol surface; pipeline coordination; timeout fallback; sandboxed Payment Protocol | `chat_protocol_spec`, `payment_protocol_spec` |
| **Planner** | Internal multi-persona **debate** → structured roadmap | ASI:One + Claude (cross-model critic) |
| **Resource** | Real links + **HTTP validation** (drops dead/hallucinated URLs) | YouTube Data API, Tavily |
| **Graph** | Roadmap → **Mermaid** flowchart + markdown outline | pure Python |

**Reliability by design:** every cross-agent hop has a fallback. If a sub-agent fails or the
pipeline times out, the Orchestrator generates a roadmap directly via ASI:One — the conversation
never hard-fails. (See `agents/services/fallback_service.py`.)

---

## Project layout

```
agents/
  config.py                       # .env loading (accepts ASI_ONE_API_KEY or ASI:ONE_API_KEY)
  chat_common.py                  # Agent Chat Protocol helpers
  models/models.py                # SharedAgentState + Roadmap/Phase/Topic/Resource
  services/
    asi_client.py                 # ASI:One (+ optional Claude) LLM calls
    planner_service.py            # Proposer -> Critic -> Synthesizer debate
    resource_service.py           # YouTube + Tavily + link validation
    graph_service.py              # Mermaid + outline rendering
    fallback_service.py           # single-call resilient roadmap
    state_service.py              # in-memory session state
  orchestrator/                   # orchestrator_agent.py, chat_protocol.py, payment_protocol.py, sessions.py
  planner/planner_agent.py
  resource/resource_agent.py
  graph/graph_agent.py
scripts/
  print_addresses.py              # derive agent addresses from seeds
  test_pipeline.py                # local brain test (no mailbox)
```

---

## Setup

Requires **Python 3.11+**.

```bash
python -m venv .venv
# Windows:  .venv\Scripts\activate     | macOS/Linux:  source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # then fill in the values
```

### Environment (`.env`)

| Variable | Required | Where to get it |
|----------|----------|-----------------|
| `ASI_ONE_API_KEY` | ✅ | https://asi1.ai |
| `ANTHROPIC_API_KEY` | optional | https://console.anthropic.com (cross-model debate critic) |
| `YOUTUBE_API_KEY` | for real video links | Google Cloud → enable *YouTube Data API v3* → API key (free) |
| `TAVILY_API_KEY` | for docs/courses | https://tavily.com (free tier) |
| `*_SEED` | ✅ | any unique random strings (no spaces) |
| `*_ADDRESS` | ✅ | run `python -m scripts.print_addresses` and paste in |
| `PAYMENT_SANDBOX` | default `true` | keep `true` — no real charges, no card capture |

Without the resource keys the system still works — it just attaches fewer links (graceful degradation).

---

## Run

1. **Compute agent addresses** and paste them into `.env`:
   ```bash
   python -m scripts.print_addresses
   ```
2. **Quick brain test** (no mailbox needed):
   ```bash
   python -m scripts.test_pipeline "Give me a roadmap to become an ML engineer in 6 months"
   ```
3. **Start all four agents**, each in its own terminal:
   ```bash
   make orchestrator      # or: python -m agents.orchestrator.orchestrator_agent
   make planner           #     python -m agents.planner.planner_agent
   make resource          #     python -m agents.resource.resource_agent
   make graph             #     python -m agents.graph.graph_agent
   ```
   On Windows without `make`, use the `python -m ...` commands directly.
4. **Connect each agent's mailbox:** open the Agent Inspector URL each agent prints on startup
   (or find it on [agentverse.ai](https://agentverse.ai)), and click **Connect → Mailbox**.
5. **Use it in ASI:One:** open [asi1.ai](https://asi1.ai), find the Orchestrator agent, and send:
   > *Give me a roadmap to become an ML engineer in 6 months.*

---

## Testing / demo checklist

- [ ] `scripts/test_pipeline.py` prints a Mermaid diagram + outline.
- [ ] All four agents register on Agentverse (mailbox connected).
- [ ] A roadmap request in ASI:One returns diagram + outline + **validated** links.
- [ ] **Resilience:** kill the Resource agent mid-run → still get a roadmap (fewer links), never an error.
- [ ] Non-technical prompt ("learn to cook Italian food in 4 weeks") also works.

---

## Challenge alignment (ASI:One Agent Challenge)

- ✅ Multiple agents **registered on Agentverse**, discoverable + usable via **ASI:One**
- ✅ **Agent Chat Protocol** implemented
- ✅ Real **tool execution** (YouTube/web APIs + validation) **and** agent-to-agent orchestration
- ✅ Full workflow completes **with no custom frontend**
- 🎁 Bonus: multi-agent debate, real-time data, reliability/recovery, sandboxed Payment Protocol

---

## Monetization (sandboxed Payment Protocol)

PromptToPath has a credible, built-in monetization model: **roadmaps are free; a
$1 "premium" deep-dive roadmap** (expanded resources and detail) is gated behind
Fetch.ai's **Payment Protocol**. The Orchestrator implements the seller role and
publishes the `AgentPaymentProtocol` manifest.

For the hackathon this runs in **sandbox mode** (`PAYMENT_SANDBOX=true`) — **no
cards are collected and no real money moves**. The seller verifies and settles the
transaction automatically so the full `CommitPayment → CompletePayment` handshake
is demonstrable end-to-end.

Demo it against a running orchestrator (no changes to the live agents):
```bash
python -m scripts.payment_demo
# Buyer commits a $1 sandbox payment → Orchestrator auto-completes → "PAYMENT COMPLETE ✅"
```
Swapping in real Stripe checkout is a config change (set `PAYMENT_SANDBOX=false` and
provide Stripe test keys); it's intentionally disabled here.

---

## License

MIT (or your choice).
