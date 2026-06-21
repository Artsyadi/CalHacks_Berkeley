"""Thin wrapper around the ASI:One agentic LLM (OpenAI-compatible API).

Also exposes an optional Anthropic (Claude) call used as a cross-model
"Critic" persona in the Planner's internal debate, for genuine model
diversity. Both are best-effort: callers should handle exceptions and fall
back gracefully (a core reliability requirement of the challenge).
"""
from __future__ import annotations

from openai import OpenAI

from agents import config

_asi_client: OpenAI | None = None


def _client() -> OpenAI:
    global _asi_client
    if _asi_client is None:
        if not config.ASI_ONE_API_KEY:
            raise RuntimeError("ASI_ONE_API_KEY missing — set it in .env")
        _asi_client = OpenAI(
            base_url=config.ASI_ONE_BASE_URL,
            api_key=config.ASI_ONE_API_KEY,
        )
    return _asi_client


def asi_chat(
    system: str,
    user: str,
    *,
    max_tokens: int = 2048,
    temperature: float = 0.4,
    json_mode: bool = False,
) -> str:
    """Single-turn ASI:One completion. Raises on failure (caller handles).

    When json_mode is set, requests strict JSON output via response_format.
    If the model/endpoint rejects response_format, it retries without it.
    """
    kwargs = dict(
        model=config.ASI_ONE_MODEL,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        max_tokens=max_tokens,
        temperature=temperature,
    )
    if json_mode:
        try:
            resp = _client().chat.completions.create(
                response_format={"type": "json_object"}, **kwargs
            )
            return str(resp.choices[0].message.content or "").strip()
        except Exception:
            pass  # endpoint may not support response_format; fall through
    resp = _client().chat.completions.create(**kwargs)
    return str(resp.choices[0].message.content or "").strip()


def claude_chat(system: str, user: str, *, max_tokens: int = 2048) -> str:
    """Optional Claude completion for cross-model debate. Raises on failure."""
    import anthropic  # imported lazily so the dep is optional at runtime

    if not config.ANTHROPIC_API_KEY:
        raise RuntimeError("ANTHROPIC_API_KEY missing")
    client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
    msg = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return "".join(
        block.text for block in msg.content if getattr(block, "type", "") == "text"
    ).strip()
