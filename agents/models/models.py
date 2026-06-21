"""Shared data models passed between PromptToPath agents.

``SharedAgentState`` is the single object that flows through the whole
pipeline (Orchestrator -> Planner -> Resource -> Graph -> Orchestrator),
mirroring the Fetch.ai hackathon-quickstarter pattern. It is a uagents
``Model`` so it can be sent directly over the network with ``ctx.send``.
"""
from __future__ import annotations

from typing import List, Optional

from uagents import Model


class Resource(Model):
    """A single validated learning resource attached to a roadmap topic."""

    title: str
    url: str
    kind: str = "link"          # "video" | "doc" | "course" | "link"
    source: str = ""            # "youtube" | "tavily" | ...


class Topic(Model):
    """A concrete topic/skill within a phase, with its resources."""

    name: str
    detail: str = ""
    resources: List[Resource] = []


class Phase(Model):
    """A time-boxed stage of the roadmap (e.g. 'Weeks 1-4: Foundations')."""

    title: str
    timeframe: str = ""         # human-readable, e.g. "Weeks 1-4"
    goal: str = ""
    topics: List[Topic] = []


class Roadmap(Model):
    """The full structured roadmap produced by the Planner."""

    topic: str = ""             # what the user wants to learn
    timeline: str = ""          # overall timeline, e.g. "6 months"
    summary: str = ""
    phases: List[Phase] = []


class SharedAgentState(Model):
    """The object that travels through the agent pipeline."""

    chat_session_id: str
    user_sender_address: str
    query: str

    # progressively filled by each agent
    roadmap: Optional[Roadmap] = None
    mermaid: Optional[str] = None
    outline: Optional[str] = None

    stage: str = "new"          # new|planned|resourced|graphed|complete|error
    error: Optional[str] = None
