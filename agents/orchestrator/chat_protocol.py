"""Agent Chat Protocol for the Orchestrator.

This is the surface ASI:One talks to. On each user message it:
  1. Acknowledges receipt.
  2. Creates a SharedAgentState and kicks off the pipeline (-> Planner).
  3. Registers the request as pending so a timeout can trigger a fallback.

If the pipeline isn't wired yet (no PLANNER_ADDRESS), it answers directly
via the single-call fallback so the agent is always useful.
"""
from __future__ import annotations

from uuid import uuid4

from uagents import Context, Protocol
from uagents.communication import DeliveryStatus
from uagents_core.contrib.protocols.chat import (
    ChatAcknowledgement,
    ChatMessage,
    chat_protocol_spec,
)

from agents import config
from agents.chat_common import acknowledge, build_chat_message, extract_text
from agents.models.models import SharedAgentState
from agents.orchestrator import sessions
from agents.services import fallback_service

chat_proto = Protocol(spec=chat_protocol_spec)


@chat_proto.on_message(ChatMessage)
async def handle_chat(ctx: Context, sender: str, msg: ChatMessage):
    await acknowledge(ctx, sender, msg)
    query = extract_text(msg)
    ctx.logger.info(f"Orchestrator received from {sender}: {query!r}")

    if not query:
        await ctx.send(sender, build_chat_message(
            "Tell me what you'd like to learn and I'll build you a roadmap — "
            "e.g. 'Give me a roadmap to become an ML engineer in 6 months'."
        ))
        return

    # If the pipeline isn't configured, answer directly (always-useful agent).
    if not config.PLANNER_ADDRESS:
        ctx.logger.warning("PLANNER_ADDRESS unset — using direct fallback.")
        try:
            text = fallback_service.generate(query)
        except Exception as exc:
            ctx.logger.exception("Fallback generation failed")
            text = f"Sorry, I couldn't build a roadmap right now ({exc})."
        await ctx.send(sender, build_chat_message(text))
        return

    session_id = uuid4().hex
    state = SharedAgentState(
        chat_session_id=session_id,
        user_sender_address=sender,
        query=query,
        stage="new",
    )
    sessions.start(session_id, sender, query)

    # Hand off to the pipeline. If the Planner is unreachable, the send fails
    # immediately — don't wait for the watchdog; fall back right now.
    status = await ctx.send(config.PLANNER_ADDRESS, state)
    if status is None or status.status == DeliveryStatus.FAILED:
        ctx.logger.warning(
            "Planner hand-off failed (%s) — immediate fallback.",
            getattr(status, "detail", "no status"),
        )
        sessions.finish(session_id)
        try:
            text = fallback_service.generate(query)
        except Exception as exc:
            ctx.logger.exception("Fallback generation failed")
            text = f"Sorry, I couldn't build a roadmap right now ({exc})."
        await ctx.send(sender, build_chat_message(text))
        return

    # Pipeline is running — let the user know work is underway.
    await ctx.send(sender, build_chat_message(
        "🧠 Spinning up the agent team — planning your roadmap, finding "
        "verified resources, and drawing the map. One moment…",
        end_session=False,
    ))


@chat_proto.on_message(ChatAcknowledgement)
async def handle_ack(ctx: Context, sender: str, msg: ChatAcknowledgement):
    pass
