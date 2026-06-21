"""Render an enriched Roadmap as a Mermaid diagram + a markdown outline.

The Mermaid fenced block renders as a visual tree in ASI:One / any
Mermaid-aware client; the markdown outline (with clickable validated links)
is the universal text fallback. Together they satisfy the "visual roadmap
inside the chat, no custom frontend" requirement.
"""
from __future__ import annotations

import re

from agents.models.models import Roadmap


def _mermaid_label(text: str, limit: int = 48) -> str:
    """Make text safe to place inside a Mermaid node label."""
    text = re.sub(r"\s+", " ", text or "").strip()
    text = text.replace('"', "'").replace("(", "[").replace(")", "]")
    text = text.replace("{", "[").replace("}", "]").replace("|", "/")
    if len(text) > limit:
        text = text[: limit - 1].rstrip() + "…"
    return text


def to_mermaid(roadmap: Roadmap) -> str:
    lines = ["flowchart TD"]
    root = "ROOT"
    lines.append(f'    {root}["🎯 {_mermaid_label(roadmap.topic)}"]')

    prev_phase = root
    for pi, phase in enumerate(roadmap.phases):
        pid = f"P{pi}"
        label = phase.title
        if phase.timeframe:
            label = f"{phase.timeframe}: {phase.title}"
        lines.append(f'    {pid}["📅 {_mermaid_label(label)}"]')
        # chain phases in sequence so the timeline reads top-to-bottom
        lines.append(f"    {prev_phase} --> {pid}")
        prev_phase = pid
        for ti, topic in enumerate(phase.topics):
            tid = f"P{pi}T{ti}"
            lines.append(f'    {tid}["{_mermaid_label(topic.name)}"]')
            lines.append(f"    {pid} --> {tid}")
    return "```mermaid\n" + "\n".join(lines) + "\n```"


def to_outline(roadmap: Roadmap) -> str:
    out: list[str] = []
    if roadmap.summary:
        out.append(roadmap.summary)
        out.append("")
    timeline = f" · ⏱ {roadmap.timeline}" if roadmap.timeline else ""
    out.append(f"## 🎯 {roadmap.topic}{timeline}")
    out.append("")

    for phase in roadmap.phases:
        header = phase.title
        if phase.timeframe:
            header = f"{phase.timeframe} — {phase.title}"
        out.append(f"### 📅 {header}")
        if phase.goal:
            out.append(f"*Goal: {phase.goal}*")
        out.append("")
        for topic in phase.topics:
            out.append(f"- **{topic.name}**" + (f" — {topic.detail}" if topic.detail else ""))
            for r in topic.resources:
                icon = {"video": "🎥", "course": "🎓", "doc": "📄"}.get(r.kind, "🔗")
                out.append(f"    - {icon} [{r.title}]({r.url})")
        out.append("")
    return "\n".join(out).strip()


def render(roadmap: Roadmap) -> tuple[str, str]:
    """Return (mermaid, outline)."""
    return to_mermaid(roadmap), to_outline(roadmap)


def compose_reply(mermaid: str, outline: str) -> str:
    """The final message body sent back to the user in chat."""
    has_links = "](http" in outline
    footer = (
        "_Every linked resource above was validated as reachable. "
        "Ask me to adjust the timeline or go deeper on any phase._"
        if has_links
        else "_Ask me to adjust the timeline or go deeper on any phase._"
    )
    return (
        "Here's your personalized learning roadmap 🚀\n\n"
        f"{mermaid}\n\n{outline}\n\n{footer}"
    )
