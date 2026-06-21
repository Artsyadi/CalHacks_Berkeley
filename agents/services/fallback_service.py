"""Single-call fallback roadmap generator.

Used when the multi-agent pipeline can't complete (a sub-agent failed or
timed out). Produces a useful roadmap directly via ASI:One so the user
always gets an answer — turning a failed tool call into graceful recovery
rather than a dead conversation.
"""
from __future__ import annotations

from agents.services import asi_client

_SYSTEM = (
    "You are an expert learning-roadmap designer. Produce a clear, phased, "
    "time-boxed roadmap for the user's goal. Format in markdown with: a short "
    "summary, then phases (with timeframes) as '### ' headers, each with a "
    "bulleted list of concrete topics. Begin the reply with a single Mermaid "
    "flowchart in a ```mermaid``` block (flowchart TD) showing the phases in "
    "sequence. Suggest the *type* of resource to look for per phase, but do "
    "not invent specific URLs."
)


def generate(query: str) -> str:
    body = asi_client.asi_chat(_SYSTEM, query, temperature=0.4, max_tokens=2500)
    return (
        "Here's your learning roadmap 🚀\n"
        "_(generated in resilient mode — link enrichment was unavailable)_\n\n"
        f"{body}"
    )
