# PromptToPath — run each agent in its own terminal.
# On Windows, prefer the PowerShell equivalents in the README if `make` is absent.

PY=python

.PHONY: addresses orchestrator planner resource graph

addresses:
	$(PY) -m scripts.print_addresses

orchestrator:
	$(PY) -m agents.orchestrator.orchestrator_agent

planner:
	$(PY) -m agents.planner.planner_agent

resource:
	$(PY) -m agents.resource.resource_agent

graph:
	$(PY) -m agents.graph.graph_agent
