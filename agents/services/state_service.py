"""In-memory store for SharedAgentState keyed by chat_session_id.

Demonstrates the persistence pattern from the Fetch.ai quickstarter — swap
this for Redis or a database and nothing else in the pipeline changes.
"""
from __future__ import annotations

from agents.models.models import SharedAgentState


class InMemoryStateService:
    def __init__(self) -> None:
        self._store: dict[str, SharedAgentState] = {}

    def set_state(self, chat_session_id: str, state: SharedAgentState) -> None:
        self._store[chat_session_id] = state

    def get_state(self, chat_session_id: str) -> SharedAgentState | None:
        return self._store.get(chat_session_id)

    def clear(self, chat_session_id: str) -> None:
        self._store.pop(chat_session_id, None)


state_service = InMemoryStateService()
