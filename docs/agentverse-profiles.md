# Agentverse Profile Copy — PromptToPath

Copy-paste each block into the matching field on agentverse.ai. The
**Orchestrator** is the public-facing agent users talk to via ASI:One — make its
profile the strongest. The other three are internal workers.

Repo: https://github.com/Artsyadi/CalHacks_Berkeley

---

## 1) Orchestrator  → `prompttopath-orchestrator`

**Handle:** `prompttopath` (fallbacks if taken: `prompttopath-ai`, `prompttopath-roadmap`)

**Avatar idea:** 🚀 or 🧠 on a solid color, or a simple "P→P" monogram.

**About / Description (short bio, shown in search):**
> Turn any learning goal into a personalized, time-boxed roadmap with a visual diagram and verified video/doc/course links. Powered by a team of collaborating agents — just tell it what you want to learn.

**README / Agent Guide:**
```markdown
# PromptToPath 🚀 — Your AI Learning Roadmap Architect

Tell PromptToPath what you want to learn — anything from *"become an ML engineer
in 6 months"* to *"learn to cook Italian food"* or *"I want to learn how to dance"* —
and get back a personalized, phased, time-boxed roadmap with:

- 🗺️ a visual **Mermaid diagram** of your learning path
- 📅 **phase-by-phase milestones** with a realistic timeline
- 🎥 **verified, clickable resources** (YouTube videos, docs, courses) for each topic

## How to use
Just send your learning goal in plain English. Examples:
- "Give me a roadmap to become an ML engineer in 6 months"
- "Teach me to cook Italian food in 4 weeks"
- "I want to learn how to dance"

You'll get a complete roadmap back in under a minute.

## Why it's more than a chatbot
PromptToPath orchestrates a **team of specialized agents**:
- 🧭 **Planner** — runs a multi-pass debate to design a realistic, phased roadmap
- 🔎 **Resource** — finds and HTTP-validates real learning links (no dead/hallucinated URLs)
- 🗺️ **Graph** — renders the roadmap as a visual diagram + outline

This orchestrator coordinates them and returns the final result, with graceful
fallback if any step is temporarily unavailable.

## Details
- Built with **Fetch.ai uAgents** + **ASI:One**; cross-checked with Claude.
- Includes a **sandboxed Payment Protocol** demo (no real charges, no card capture).
- Open source: https://github.com/Artsyadi/CalHacks_Berkeley
- Contact: dawale@usc.edu
```

---

## 2) Planner  → `prompttopath-planner`

**Handle:** `prompttopath-planner`

**Avatar idea:** 🧭 (compass) on a solid color.

**About / Description:**
> Internal PromptToPath agent — runs a multi-pass debate to design realistic, phased, time-boxed learning roadmaps. To use the full experience, talk to the PromptToPath orchestrator.

**README / Agent Guide:**
```markdown
# PromptToPath · Planner 🧭

The planning brain of the **PromptToPath** multi-agent system.

## Purpose
Turns a learning goal into a structured, realistic roadmap using a two-pass
**propose → critique-and-finalize** debate:
1. **Propose** — drafts a concise phased roadmap with a realistic timeline.
2. **Critique & finalize** — checks for unrealistic pacing, missing prerequisites,
   wrong ordering, and scope creep, then emits the corrected roadmap as structured JSON.

## Output
Phases → timeframes → goals → key topics, ready for downstream resource enrichment
and diagram rendering.

## Note
This is an internal component. For the full experience (roadmap + verified links +
diagram), talk to the **PromptToPath** orchestrator agent.

- Built with Fetch.ai uAgents + ASI:One. Open source: https://github.com/Artsyadi/CalHacks_Berkeley · dawale@usc.edu
```

---

## 3) Resource  → `prompttopath-resource`

**Handle:** `prompttopath-resource`

**Avatar idea:** 🔎 (magnifying glass) on a solid color.

**About / Description:**
> Internal PromptToPath agent — finds and HTTP-validates real learning resources (YouTube videos, docs, courses) for each roadmap topic, so links are never broken or hallucinated.

**README / Agent Guide:**
```markdown
# PromptToPath · Resource 🔎

The resource-finder of the **PromptToPath** multi-agent system.

## Purpose
Attaches **real, validated** learning links to each roadmap topic:
- Searches the live web for relevant videos, docs, and courses.
- **HTTP-validates every URL** (concurrently, with a hard time budget) and drops
  anything unreachable — so the roadmap never ships dead or hallucinated links.
- Best-effort by design: if a source is unavailable, the roadmap simply carries
  fewer links rather than failing.

## Note
This is an internal component. For the full experience, talk to the **PromptToPath**
orchestrator agent.

- Built with Fetch.ai uAgents. Open source: https://github.com/Artsyadi/CalHacks_Berkeley · dawale@usc.edu
```

---

## 4) Graph  → `prompttopath-graph`

**Handle:** `prompttopath-graph`

**Avatar idea:** 🗺️ (map) on a solid color.

**About / Description:**
> Internal PromptToPath agent — renders enriched learning roadmaps as a visual Mermaid diagram plus a clean markdown outline for display inside chat.

**README / Agent Guide:**
```markdown
# PromptToPath · Graph 🗺️

The visualizer of the **PromptToPath** multi-agent system.

## Purpose
Converts an enriched roadmap into chat-ready output:
- A **Mermaid flowchart** showing phases and topics in sequence.
- A **markdown outline** with goals and inline, clickable validated resource links.

Renders as a diagram in Mermaid-aware clients and degrades gracefully to readable
text everywhere else — no custom frontend required.

## Note
This is an internal component. For the full experience, talk to the **PromptToPath**
orchestrator agent.

- Built with Fetch.ai uAgents. Open source: https://github.com/Artsyadi/CalHacks_Berkeley · dawale@usc.edu
```
