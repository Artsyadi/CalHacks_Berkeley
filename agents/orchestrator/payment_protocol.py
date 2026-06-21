"""Sandboxed Payment Protocol (seller role) for the Orchestrator.

Demonstrates a credible monetization model — "$1 for a premium, deeply
detailed roadmap" — using Fetch.ai's Payment Protocol message flow, WITHOUT
ever collecting card details or moving real money. With PAYMENT_SANDBOX=true
the seller auto-acknowledges the commit, so the full
RequestPayment -> CommitPayment -> CompletePayment handshake is observable in
a demo while remaining completely safe.

Written defensively: if the installed uagents-core doesn't expose the payment
spec, `build_payment_proto()` returns None and the Orchestrator runs without it.
"""
from __future__ import annotations

from agents import config

try:  # payment spec availability varies by uagents-core version
    from uagents import Context, Protocol
    from uagents_core.contrib.protocols.payment import (  # type: ignore
        CommitPayment,
        CompletePayment,
        RejectPayment,
        payment_protocol_spec,
    )

    _PAYMENT_AVAILABLE = True
except Exception:  # pragma: no cover - depends on installed version
    _PAYMENT_AVAILABLE = False


def build_payment_proto():
    """Return a configured seller payment Protocol, or None if unavailable."""
    if not _PAYMENT_AVAILABLE:
        return None

    proto = Protocol(spec=payment_protocol_spec, role="seller")

    @proto.on_message(CommitPayment)
    async def _on_commit(ctx: Context, sender: str, msg: CommitPayment):
        # SANDBOX: never verify a real charge; acknowledge to complete the flow.
        if config.PAYMENT_SANDBOX:
            ctx.logger.info("[sandbox] Auto-completing payment (no real charge).")
            tx = getattr(msg, "transaction_id", "sandbox-tx")
            await ctx.send(sender, CompletePayment(transaction_id=tx))
        else:
            # Real verification would go here (Stripe checkout session lookup).
            await ctx.send(sender, RejectPayment(
                reason="Live payments are disabled in this deployment."
            ))

    @proto.on_message(RejectPayment)
    async def _on_reject(ctx: Context, sender: str, msg: RejectPayment):
        ctx.logger.info(f"Payment rejected: {getattr(msg, 'reason', '')}")

    return proto
