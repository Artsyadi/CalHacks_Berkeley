"""Local end-to-end test that mimics ASI:One over local transport.

Starts a tiny client agent that sends a ChatMessage to the Orchestrator and
prints every ChatMessage it gets back (ack/heartbeats/final roadmap). This
exercises the full Orchestrator -> Planner -> Resource -> Graph -> Orchestrator
chain via local HTTP endpoints — no ASI:One / mailbox needed.

Run (with all 4 agents already running):  python -m scripts.test_local_pipeline
"""
from __future__ import annotations

import sys
from datetime import datetime
from uuid import uuid4

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from uagents import Agent, Context, Protocol
from uagents_core.contrib.protocols.chat import (
    ChatAcknowledgement,
    ChatMessage,
    TextContent,
    chat_protocol_spec,
)

from agents import config

QUERY = "Give me a roadmap to become an ML engineer in 6 months"

client = Agent(
    name="test-client",
    seed="prompttopath-test-client-seed-001",
    port=8009,
    endpoint=["http://127.0.0.1:8009/submit"],
)

proto = Protocol(spec=chat_protocol_spec)


@client.on_event("startup")
async def _go(ctx: Context):
    ctx.logger.info(f"client={client.address}")
    ctx.logger.info(f"sending to orchestrator={config.ORCHESTRATOR_ADDRESS}")
    await ctx.send(
        config.ORCHESTRATOR_ADDRESS,
        ChatMessage(
            timestamp=datetime.utcnow(),
            msg_id=uuid4(),
            content=[TextContent(type="text", text=QUERY)],
        ),
    )


@proto.on_message(ChatMessage)
async def _on_msg(ctx: Context, sender: str, msg: ChatMessage):
    text = "".join(c.text for c in msg.content if isinstance(c, TextContent))
    ctx.logger.info(f"##### CLIENT RECEIVED ({len(text)} chars) #####")
    print(text)
    print("##### END MESSAGE #####", flush=True)
    # ack back so the protocol is happy
    await ctx.send(
        sender,
        ChatAcknowledgement(timestamp=datetime.now(), acknowledged_msg_id=msg.msg_id),
    )


@proto.on_message(ChatAcknowledgement)
async def _on_ack(ctx: Context, sender: str, msg: ChatAcknowledgement):
    pass


client.include(proto)

if __name__ == "__main__":
    client.run()
