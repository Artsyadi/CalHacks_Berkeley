"""Local end-to-end test of the pipeline BRAINS (no agents / no mailbox).

Runs Planner debate -> Resource enrichment -> Graph rendering directly so we
can validate the core logic before wiring up Agentverse mailboxes.

Run:  python -m scripts.test_pipeline "your learning goal"
"""
from __future__ import annotations

import sys

# Windows consoles default to cp1252 and choke on emoji; force UTF-8 output.
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from agents.services import graph_service, planner_service, resource_service


def main() -> None:
    query = " ".join(sys.argv[1:]) or "Give me a roadmap to become an ML engineer in 6 months"
    print(f"\n=== GOAL: {query} ===\n")

    print("[1/3] Planner debate (Proposer -> Critic -> Synthesizer)…")
    roadmap = planner_service.build_roadmap(query)
    print(f"  -> {len(roadmap.phases)} phases, timeline: {roadmap.timeline!r}")

    print("[2/3] Resource enrichment (YouTube + Tavily + validation)…")
    roadmap = resource_service.enrich(roadmap)
    n_links = sum(len(t.resources) for p in roadmap.phases for t in p.topics)
    print(f"  -> {n_links} validated links attached")

    print("[3/3] Graph rendering (Mermaid + outline)…\n")
    mermaid, outline = graph_service.render(roadmap)

    print("------ MERMAID ------")
    print(mermaid)
    print("\n------ OUTLINE ------")
    print(outline)


if __name__ == "__main__":
    main()
