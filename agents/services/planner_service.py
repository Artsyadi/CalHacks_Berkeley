"""Planner debate: turn a learning intent into a structured Roadmap.

Runs a small multi-persona debate to avoid generic, single-shot output:

  1. Proposer  — drafts a phased, time-boxed roadmap.
  2. Critic    — attacks pacing, gaps, scope, realism (optionally Claude,
                 for genuine cross-model diversity; falls back to ASI:One).
  3. Synthesizer — returns the final roadmap as strict JSON we parse.

Everything is best-effort with graceful fallback so the pipeline never
hard-fails (a scored reliability requirement).
"""
from __future__ import annotations

import json
import re

from agents.models.models import Phase, Resource, Roadmap, Topic
from agents.services import asi_client


def _proposer(query: str) -> str:
    """First pass — a concise draft roadmap (ASI:One for consistent latency)."""
    system = (
        "You are an expert curriculum designer. Given a learning goal, produce "
        "a realistic, phased, time-boxed roadmap. Cover any domain (technical, "
        "creative, physical, professional). Be CONCISE: 4-6 phases, 2-3 key "
        "topics per phase, short phrases not paragraphs."
    )
    user = (
        f"Learning goal: {query}\n\n"
        "Draft a concise phased roadmap with a realistic overall timeline. "
        "For each phase: timeframe, one-line goal, 2-3 topic names."
    )
    return asi_client.asi_chat(system, user, temperature=0.5, max_tokens=900)


_JSON_INSTRUCTIONS = """Return ONLY valid JSON (no markdown fences, no prose) matching exactly:
{
  "topic": "<what the learner wants to learn>",
  "timeline": "<overall timeline, e.g. '6 months'>",
  "summary": "<2-3 sentence overview>",
  "phases": [
    {
      "title": "<phase name>",
      "timeframe": "<e.g. 'Weeks 1-4'>",
      "goal": "<what they achieve in this phase>",
      "topics": [
        {"name": "<topic/skill>", "detail": "<one line on what & why>"}
      ]
    }
  ]
}"""


def _synthesize(query: str, draft: str) -> str:
    """Second perspective — ASI:One critiques the draft, then finalizes it.

    Folds the critic role in: the model first reasons about pacing/gaps/ordering,
    then emits the corrected roadmap as JSON. One call instead of two.
    """
    system = (
        "You are a demanding curriculum designer finalizing a roadmap. First "
        "critique the draft for unrealistic pacing, missing prerequisites, wrong "
        "ordering, and scope creep, then FIX those issues. Keep it tight: 4-6 "
        "phases, 2-3 topics per phase, one-line details. " + _JSON_INSTRUCTIONS
    )
    user = (
        f"Learning goal: {query}\n\nDraft roadmap to refine:\n{draft}\n\n"
        "Now output the final, corrected JSON."
    )
    return asi_client.asi_chat(
        system, user, temperature=0.2, max_tokens=2400, json_mode=True
    )


def _balanced_object(text: str) -> str | None:
    """Return the first brace-balanced {...} substring (ignoring braces in strings)."""
    start = text.find("{")
    if start == -1:
        return None
    depth, in_str, esc = 0, False, False
    for i in range(start, len(text)):
        c = text[i]
        if in_str:
            if esc:
                esc = False
            elif c == "\\":
                esc = True
            elif c == '"':
                in_str = False
        else:
            if c == '"':
                in_str = True
            elif c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    return text[start : i + 1]
    return None  # unbalanced (likely truncated)


def _extract_json(text: str) -> dict:
    """Pull the first JSON object out of a model response, repairing common issues."""
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*\n?", "", text)
        text = re.sub(r"\n?```$", "", text).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    candidate = _balanced_object(text) or text
    # Repair trailing commas before } or ] which are the most common defect.
    candidate = re.sub(r",(\s*[}\]])", r"\1", candidate)
    return json.loads(candidate)


def _to_roadmap(data: dict, query: str) -> Roadmap:
    phases = []
    for p in data.get("phases", []):
        topics = [
            Topic(name=t.get("name", ""), detail=t.get("detail", ""), resources=[])
            for t in p.get("topics", [])
            if t.get("name")
        ]
        phases.append(
            Phase(
                title=p.get("title", ""),
                timeframe=p.get("timeframe", ""),
                goal=p.get("goal", ""),
                topics=topics,
            )
        )
    return Roadmap(
        topic=data.get("topic", query),
        timeline=data.get("timeline", ""),
        summary=data.get("summary", ""),
        phases=phases,
    )


def build_roadmap(query: str) -> Roadmap:
    """Two-call cross-model debate: Claude proposes, ASI:One critiques+finalizes.

    Raises only if the final JSON can't be parsed into any phases.
    """
    draft = _proposer(query)            # Claude (cross-model perspective)
    final = _synthesize(query, draft)   # ASI:One: self-critique + final JSON
    data = _extract_json(final)
    roadmap = _to_roadmap(data, query)
    if not roadmap.phases:
        raise ValueError("Planner produced no phases")
    return roadmap
