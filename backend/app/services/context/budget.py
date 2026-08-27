"""Context-window budgeting (spec §7).

Estimates token counts without external tokenizer dependencies and fits
message lists into a model's context window using sliding-window truncation:

- leading system messages are always preserved
- newest history is kept; oldest messages are dropped first
- the newest (user) message is never dropped — it is hard-truncated if it
  alone cannot fit
- a per-message hard cap guarantees no single message exceeds the budget

The spec does not mandate a specific output-token reservation, so a
conservative default is used here.
"""

from typing import List

# Reserved headroom for the model's reply (not mandated by spec §7).
RESERVE_OUTPUT_TOKENS = 1024
PER_MESSAGE_OVERHEAD_TOKENS = 4

# ~4 characters per token is a reasonable heuristic across providers.
CHARS_PER_TOKEN = 4


def estimate_tokens(text: str) -> int:
    if not text:
        return 0
    return max(1, (len(text) + CHARS_PER_TOKEN - 1) // CHARS_PER_TOKEN)


def _message_tokens(message: dict) -> int:
    return estimate_tokens(message.get("content", "")) + PER_MESSAGE_OVERHEAD_TOKENS


def _truncate_content(content: str, token_budget: int) -> str:
    max_chars = max(0, token_budget * CHARS_PER_TOKEN)
    if len(content) <= max_chars:
        return content
    return content[-max_chars:]


def fit_messages_to_budget(
    messages: List[dict],
    context_window: int,
    reserve_output: int = RESERVE_OUTPUT_TOKENS,
) -> List[dict]:
    """Return a new message list fitting within ``context_window`` tokens.

    Never mutates the input messages.
    """
    budget = max(0, context_window - reserve_output)
    if not messages:
        return []

    system = [dict(m) for m in messages if m.get("role") == "system"]
    rest = [m for m in messages if m.get("role") != "system"]

    if not rest:
        return _fit_system_only(system, budget)

    system_tokens = sum(_message_tokens(m) for m in system)
    remaining = budget - system_tokens
    if remaining <= 0:
        # System prompt alone exceeds the budget: shrink it proportionally.
        per = max(1, budget // len(system)) - PER_MESSAGE_OVERHEAD_TOKENS if system else 0
        system = [
            {**m, "content": _truncate_content(m["content"], max(1, per))}
            for m in system
        ]
        remaining = budget - sum(_message_tokens(m) for m in system)

    newest = dict(rest[-1])
    newest_tokens = _message_tokens(newest)
    if newest_tokens > remaining:
        # The newest message must be sent; hard-truncate it to what remains.
        newest["content"] = _truncate_content(
            newest["content"], max(1, remaining - PER_MESSAGE_OVERHEAD_TOKENS)
        )
        kept = [newest]
    else:
        used = newest_tokens
        kept = [newest]
        for m in reversed(rest[:-1]):
            t = _message_tokens(m)
            if used + t > remaining:
                break
            kept.append(dict(m))
            used += t
        kept.reverse()

    return system + kept


def _fit_system_only(system: List[dict], budget: int) -> List[dict]:
    total = sum(_message_tokens(m) for m in system)
    if total <= budget or not system:
        return system
    per = max(1, budget // len(system)) - PER_MESSAGE_OVERHEAD_TOKENS
    return [
        {**m, "content": _truncate_content(m["content"], max(1, per))}
        for m in system
    ]
