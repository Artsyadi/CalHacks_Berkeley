"""Central config + .env loading for all PromptToPath agents.

Importing this module loads the .env file once and exposes typed getters.
Both ``ASI_ONE_API_KEY`` (preferred) and the colon form ``ASI:ONE_API_KEY``
are accepted so the user's original .env keeps working.
"""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

# Load the .env that sits at the repo root (parent of the agents/ package).
_ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_ENV_PATH)


def _get(name: str, default: str | None = None) -> str | None:
    val = os.getenv(name)
    return val if val not in (None, "") else default


# ── LLM keys ───────────────────────────────────────────────────────────────
ASI_ONE_API_KEY = _get("ASI_ONE_API_KEY") or _get("ASI:ONE_API_KEY")
ANTHROPIC_API_KEY = _get("ANTHROPIC_API_KEY")
ASI_ONE_BASE_URL = _get("ASI_ONE_BASE_URL", "https://api.asi1.ai/v1")
ASI_ONE_MODEL = _get("ASI_ONE_MODEL", "asi1")

# ── Resource agent keys ──────────────────────────────────────────────────────
YOUTUBE_API_KEY = _get("YOUTUBE_API_KEY")
TAVILY_API_KEY = _get("TAVILY_API_KEY")

# ── Agent seeds ──────────────────────────────────────────────────────────────
ORCHESTRATOR_SEED = _get("ORCHESTRATOR_SEED", "prompttopath-orchestrator-dev-seed")
PLANNER_SEED = _get("PLANNER_SEED", "prompttopath-planner-dev-seed")
RESOURCE_SEED = _get("RESOURCE_SEED", "prompttopath-resource-dev-seed")
GRAPH_SEED = _get("GRAPH_SEED", "prompttopath-graph-dev-seed")

# ── Inter-agent addresses (filled in after first run) ────────────────────────
PLANNER_ADDRESS = _get("PLANNER_ADDRESS")
RESOURCE_ADDRESS = _get("RESOURCE_ADDRESS")
GRAPH_ADDRESS = _get("GRAPH_ADDRESS")
ORCHESTRATOR_ADDRESS = _get("ORCHESTRATOR_ADDRESS")

# ── Ports ────────────────────────────────────────────────────────────────────
ORCHESTRATOR_PORT = int(_get("ORCHESTRATOR_PORT", "8001"))
PLANNER_PORT = int(_get("PLANNER_PORT", "8002"))
RESOURCE_PORT = int(_get("RESOURCE_PORT", "8003"))
GRAPH_PORT = int(_get("GRAPH_PORT", "8004"))

# ── Payment (sandboxed) ──────────────────────────────────────────────────────
PAYMENT_SANDBOX = _get("PAYMENT_SANDBOX", "true").lower() == "true"
STRIPE_SECRET_KEY = _get("STRIPE_SECRET_KEY")
STRIPE_PUBLISHABLE_KEY = _get("STRIPE_PUBLISHABLE_KEY")


def require(name: str) -> str:
    """Fetch a config value by attribute name or raise a clear error."""
    val = globals().get(name)
    if not val:
        raise RuntimeError(
            f"Missing required config '{name}'. Add it to your .env "
            f"(see .env.example)."
        )
    return val
