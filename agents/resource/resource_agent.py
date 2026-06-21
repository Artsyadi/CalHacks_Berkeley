"""Resource agent — attaches real, validated links to each roadmap topic.

Resource enrichment is best-effort: if a search API is missing or fails, the
roadmap simply carries fewer links and the pipeline continues to the Graph
agent. It never blocks the workflow.

Run:  python -m agents.resource.resource_agent
"""
from __future__ import annotations

from uagents import Agent, Context

from agents import config
from agents.models.models import SharedAgentState
from agents.services import resource_service

agent = Agent(
    name="prompttopath-resource",
    seed=config.RESOURCE_SEED,
    port=config.RESOURCE_PORT,
    # Internal worker: reached by peers over fast local HTTP (no mailbox).
    endpoint=[f"http://127.0.0.1:{config.RESOURCE_PORT}/submit"],
    publish_agent_details=True,
)


@agent.on_event("startup")
async def _startup(ctx: Context):
    ctx.logger.info(f"Resource agent address: {agent.address}")


@agent.on_message(SharedAgentState)
async def handle(ctx: Context, sender: str, state: SharedAgentState):
    if state.roadmap is not None:
        try:
            state.roadmap = resource_service.enrich(state.roadmap)
            state.stage = "resourced"
        except Exception as exc:  # non-fatal — continue with fewer links
            ctx.logger.exception("Resource enrichment failed (continuing)")
            state.error = (state.error or "") + f" resource: {exc}"

    next_addr = config.GRAPH_ADDRESS or config.ORCHESTRATOR_ADDRESS
    if not next_addr:
        ctx.logger.error("No downstream address configured; dropping state.")
        return
    await ctx.send(next_addr, state)


if __name__ == "__main__":
    agent.run()
