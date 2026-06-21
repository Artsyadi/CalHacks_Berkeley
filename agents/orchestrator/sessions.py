"""Tracks in-flight roadmap requests so the Orchestrator can time out and
fall back if the pipeline doesn't return in time.
"""
from __future__ import annotations

import time
from dataclasses import dataclass


@dataclass
class Pending:
    chat_session_id: str
    user_sender_address: str
    query: str
    started_at: float
    last_heartbeat: float
    done: bool = False


_pending: dict[str, Pending] = {}


def start(chat_session_id: str, user_sender_address: str, query: str) -> None:
    now = time.monotonic()
    _pending[chat_session_id] = Pending(
        chat_session_id=chat_session_id,
        user_sender_address=user_sender_address,
        query=query,
        started_at=now,
        last_heartbeat=now,
    )


def due_for_heartbeat(interval_seconds: float) -> list[Pending]:
    """Active sessions whose last heartbeat is older than interval."""
    now = time.monotonic()
    out: list[Pending] = []
    for p in _pending.values():
        if not p.done and (now - p.last_heartbeat) >= interval_seconds:
            p.last_heartbeat = now
            out.append(p)
    return out


def finish(chat_session_id: str) -> None:
    _pending.pop(chat_session_id, None)


def is_active(chat_session_id: str) -> bool:
    p = _pending.get(chat_session_id)
    return p is not None and not p.done


def stale(timeout_seconds: float) -> list[Pending]:
    """Return active sessions older than timeout, marking them done."""
    now = time.monotonic()
    out: list[Pending] = []
    for p in _pending.values():
        if not p.done and (now - p.started_at) >= timeout_seconds:
            p.done = True
            out.append(p)
    return out
