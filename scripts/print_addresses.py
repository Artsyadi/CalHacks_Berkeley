"""Print each agent's deterministic address (derived from its seed in .env).

Agent addresses are derived from the seed, so we can compute them without
running the agents — then paste them into .env for inter-agent routing.

Run:  python -m scripts.print_addresses
"""
from __future__ import annotations

from uagents import Agent

from agents import config

_AGENTS = [
    ("ORCHESTRATOR_ADDRESS", config.ORCHESTRATOR_SEED),
    ("PLANNER_ADDRESS", config.PLANNER_SEED),
    ("RESOURCE_ADDRESS", config.RESOURCE_SEED),
    ("GRAPH_ADDRESS", config.GRAPH_SEED),
]


def main() -> None:
    print("\n# Paste these into your .env:\n")
    for env_name, seed in _AGENTS:
        # Constructing an Agent derives the address from the seed (no network).
        addr = Agent(name=env_name, seed=seed).address
        print(f"{env_name}={addr}")
    print()


if __name__ == "__main__":
    main()
