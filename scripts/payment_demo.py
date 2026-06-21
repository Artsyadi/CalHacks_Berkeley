"""Sandboxed Payment Protocol demo — a standalone 'buyer' client.

Demonstrates PromptToPath's monetization model end-to-end WITHOUT real money:
a buyer commits a $1 (sandbox) payment for a premium roadmap to the running
Orchestrator (the seller); the Orchestrator's sandbox handler verifies and
replies with CompletePayment. No cards, no Stripe checkout, no charge.

This talks to the ALREADY-RUNNING orchestrator over its published Payment
Protocol — it does not modify or restart any of the four agents.

Run (with the orchestrator running):  python -m scripts.payment_demo
"""
from __future__ import annotations

import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from uagents import Agent, Context, Protocol
from uagents_core.contrib.protocols.payment import (
    CancelPayment,
    CommitPayment,
    CompletePayment,
    Funds,
    RequestPayment,
    payment_protocol_spec,
)

from agents import config

buyer = Agent(
    name="prompttopath-payment-buyer-demo",
    seed="prompttopath-payment-buyer-demo-seed-001",
    port=8010,
    endpoint=["http://127.0.0.1:8010/submit"],
)

proto = Protocol(spec=payment_protocol_spec, role="buyer")


@buyer.on_event("startup")
async def _buy(ctx: Context):
    ctx.logger.info("buyer=%s", buyer.address)
    ctx.logger.info("Purchasing PREMIUM roadmap for $1.00 (SANDBOX — no real charge)…")
    await ctx.send(
        config.ORCHESTRATOR_ADDRESS,
        CommitPayment(
            funds=Funds(amount="1.00", currency="USD", payment_method="stripe"),
            recipient=config.ORCHESTRATOR_ADDRESS,
            transaction_id="sandbox-demo-0001",
            description="PromptToPath premium deep-dive roadmap (sandbox)",
        ),
    )


@proto.on_message(CompletePayment)
async def _on_complete(ctx: Context, sender: str, msg: CompletePayment):
    ctx.logger.info("##### PAYMENT COMPLETE #####")
    ctx.logger.info("Seller confirmed transaction_id=%s", msg.transaction_id)
    ctx.logger.info("Sandbox payment settled — premium roadmap unlocked. ✅")


# Required by the buyer role even if unused in this demo flow.
@proto.on_message(RequestPayment)
async def _on_request(ctx: Context, sender: str, msg: RequestPayment):
    ctx.logger.info("Received payment request: %s", msg.description)


@proto.on_message(CancelPayment)
async def _on_cancel(ctx: Context, sender: str, msg: CancelPayment):
    ctx.logger.info("Payment cancelled by seller.")


buyer.include(proto)

if __name__ == "__main__":
    buyer.run()
