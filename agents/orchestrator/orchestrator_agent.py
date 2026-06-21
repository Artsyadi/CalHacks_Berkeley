"""Orchestrator — the only agent ASI:One talks to.

Responsibilities:
  - Implements the Agent Chat Protocol (via chat_protocol.chat_proto).
  - Kicks off the pipeline (Planner -> Resource -> Graph) per user request.
  - Receives the completed SharedAgentState back from the Graph agent and
    delivers the final roadmap to the user.
  - Times out stalled requests and falls back to a single-call roadmap so the
    demo never hard-fails.
  - Includes a sandboxed Payment Protocol (no real charges).

Run:  python -m agents.orchestrator.orchestrator_agent
"""
from __future__ import annotations

import time

from uagents import Agent, Context

from agents import config
from agents.chat_common import build_chat_message
from agents.models.models import SharedAgentState
from agents.orchestrator import sessions
from agents.orchestrator.chat_protocol import chat_proto
from agents.orchestrator.payment_protocol import build_payment_proto
from agents.services import fallback_service, graph_service

# Seconds to wait for the full pipeline before falling back. Kept well under
# ASI:One's response window so a fallback still lands inside the chat turn.
PIPELINE_TIMEOUT = 110.0
# Send a progress message at least this often to keep the ASI:One session alive.
HEARTBEAT_INTERVAL = 15.0

_HEARTBEATS = [
    "🧭 Planner agents are debating the best path for your goal…",
    "🔎 Resource agent is finding and validating real learning links…",
    "🗺️ Graph agent is drawing your roadmap…",
]

agent = Agent(
    name="prompttopath-orchestrator",
    seed=config.ORCHESTRATOR_SEED,
    port=config.ORCHESTRATOR_PORT,
    mailbox=True,  # public-facing: ASI:One reaches the orchestrator via mailbox
    publish_agent_details=True,
)


@agent.on_event("startup")
async def _startup(ctx: Context):
    ctx.logger.info(f"Orchestrator agent address: {agent.address}")
    if not config.PLANNER_ADDRESS:
        ctx.logger.warning(
            "PLANNER_ADDRESS not set — running in direct-fallback mode. "
            "Fill agent addresses in .env to enable the full pipeline."
        )


@agent.on_message(SharedAgentState)
async def on_pipeline_return(ctx: Context, sender: str, state: SharedAgentState):
    """Completed (or failed) state coming back from the pipeline."""
    if not sessions.is_active(state.chat_session_id):
        ctx.logger.info("Ignoring state for a finished/unknown session.")
        return
    sessions.finish(state.chat_session_id)

    if state.stage == "error" or state.roadmap is None:
        ctx.logger.warning(f"Pipeline error ({state.error}); using fallback.")
        try:
            text = fallback_service.generate(state.query)
        except Exception as exc:
            ctx.logger.exception("Fallback failed")
            text = f"Sorry, I couldn't complete your roadmap ({exc})."
    else:
        mermaid = state.mermaid or graph_service.to_mermaid(state.roadmap)
        outline = state.outline or graph_service.to_outline(state.roadmap)
        text = graph_service.compose_reply(mermaid, outline)

    await ctx.send(state.user_sender_address, build_chat_message(text))


@agent.on_interval(period=5.0)
async def _timeout_watchdog(ctx: Context):
    # Keep the chat session alive with progress updates while work is in flight.
    for p in sessions.due_for_heartbeat(HEARTBEAT_INTERVAL):
        elapsed = time.monotonic() - p.started_at
        idx = min(int(elapsed // HEARTBEAT_INTERVAL), len(_HEARTBEATS) - 1)
        await ctx.send(
            p.user_sender_address,
            build_chat_message(_HEARTBEATS[idx], end_session=False),
        )

    # Fall back for anything that exceeded the hard timeout.
    for p in sessions.stale(PIPELINE_TIMEOUT):
        ctx.logger.warning(f"Session {p.chat_session_id} timed out; falling back.")
        try:
            text = fallback_service.generate(p.query)
        except Exception as exc:
            ctx.logger.exception("Timeout fallback failed")
            text = f"Sorry, your roadmap took too long to build ({exc})."
        await ctx.send(p.user_sender_address, build_chat_message(text))


agent.include(chat_proto, publish_manifest=True)

_payment_proto = build_payment_proto()
if _payment_proto is not None:
    agent.include(_payment_proto, publish_manifest=True)


if __name__ == "__main__":
    agent.run()
