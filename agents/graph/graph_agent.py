"""Graph agent — renders the enriched roadmap as Mermaid + markdown outline.

Final stage of the forward pipeline. Sends the completed state back to the
Orchestrator, which delivers it to the user.

Run:  python -m agents.graph.graph_agent
"""
from __future__ import annotations

from uagents import Agent, Context

from agents import config
from agents.models.models import SharedAgentState
from agents.services import graph_service

agent = Agent(
    name="prompttopath-graph",
    seed=config.GRAPH_SEED,
    port=config.GRAPH_PORT,
    # Internal worker: reached by peers over fast local HTTP (no mailbox).
    endpoint=[f"http://127.0.0.1:{config.GRAPH_PORT}/submit"],
    publish_agent_details=True,
)


@agent.on_event("startup")
async def _startup(ctx: Context):
    ctx.logger.info(f"Graph agent address: {agent.address}")


@agent.on_message(SharedAgentState)
async def handle(ctx: Context, sender: str, state: SharedAgentState):
    if state.roadmap is not None:
        try:
            mermaid, outline = graph_service.render(state.roadmap)
            state.mermaid = mermaid
            state.outline = outline
            state.stage = "graphed"
        except Exception as exc:
            ctx.logger.exception("Graph rendering failed")
            state.error = (state.error or "") + f" graph: {exc}"
            state.stage = "error"

    if not config.ORCHESTRATOR_ADDRESS:
        ctx.logger.error("ORCHESTRATOR_ADDRESS not configured; dropping state.")
        return
    await ctx.send(config.ORCHESTRATOR_ADDRESS, state)


if __name__ == "__main__":
    agent.run()
