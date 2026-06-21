"""Shared helpers for the Agent Chat Protocol used by every agent.

Keeps the boilerplate (acknowledging messages, extracting text, building a
final reply with an end-of-session marker) in one place.
"""
from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from uagents import Context
from uagents_core.contrib.protocols.chat import (
    ChatAcknowledgement,
    ChatMessage,
    EndSessionContent,
    TextContent,
)


def extract_text(msg: ChatMessage) -> str:
    """Concatenate all TextContent parts of an incoming chat message."""
    out = ""
    for item in msg.content:
        if isinstance(item, TextContent):
            out += item.text
    return out.strip()


async def acknowledge(ctx: Context, sender: str, msg: ChatMessage) -> None:
    """Immediately ack receipt, as required by the chat protocol."""
    await ctx.send(
        sender,
        ChatAcknowledgement(timestamp=datetime.now(), acknowledged_msg_id=msg.msg_id),
    )


def build_chat_message(text: str, *, end_session: bool = True) -> ChatMessage:
    """Build a ChatMessage carrying text, optionally ending the session."""
    content: list = [TextContent(type="text", text=text)]
    if end_session:
        content.append(EndSessionContent(type="end-session"))
    return ChatMessage(timestamp=datetime.utcnow(), msg_id=uuid4(), content=content)


def session_id_of(ctx: Context, sender: str) -> str:
    """Best-effort stable session id. Falls back to the sender address."""
    return getattr(ctx, "session", None) and str(ctx.session) or sender
