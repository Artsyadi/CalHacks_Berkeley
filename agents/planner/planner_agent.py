"""Planner agent — runs the internal debate and produces a structured roadmap.

Receives a SharedAgentState from the Orchestrator, builds the roadmap, then
forwards the state to the Resource agent. On a fatal failure it returns the
state (with .error set) to the Orchestrator so the Orchestrator can fall back.

Run:  python -m agents.planner.planner_agent
"""
from __future__ import annotations

from uagents import Agent, Context

from agents import config
from agents.models.models import SharedAgentState
from agents.services import planner_service

agent = Agent(
    name="prompttopath-planner",
    seed=config.PLANNER_SEED,
    port=config.PLANNER_PORT,
    # Internal worker: reached by peers over fast local HTTP (no mailbox).
    endpoint=[f"http://127.0.0.1:{config.PLANNER_PORT}/submit"],
    publish_agent_details=True,
)


@agent.on_event("startup")
async def _startup(ctx: Context):
    ctx.logger.info(f"Planner agent address: {agent.address}")


@agent.on_message(SharedAgentState)
async def handle(ctx: Context, sender: str, state: SharedAgentState):
    ctx.logger.info(f"Planner received goal: {state.query!r}")
    try:
        state.roadmap = planner_service.build_roadmap(state.query)
        state.stage = "planned"
        next_addr = config.RESOURCE_ADDRESS
    except Exception as exc:  # fatal — let the Orchestrator fall back
        ctx.logger.exception("Planner failed")
        state.error = f"planner: {exc}"
        state.stage = "error"
        next_addr = config.ORCHESTRATOR_ADDRESS

    if not next_addr:
        ctx.logger.error("No downstream address configured; dropping state.")
        return
    await ctx.send(next_addr, state)


if __name__ == "__main__":
    agent.run()
