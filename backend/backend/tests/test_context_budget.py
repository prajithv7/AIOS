"""Tests for context-window budgeting (spec §7)."""

import pytest

from app.services.context.budget import (
    CHARS_PER_TOKEN,
    PER_MESSAGE_OVERHEAD_TOKENS,
    RESERVE_OUTPUT_TOKENS,
    estimate_tokens,
    fit_messages_to_budget,
)


def total_tokens(messages):
    return sum(estimate_tokens(m["content"]) + PER_MESSAGE_OVERHEAD_TOKENS for m in messages)


def msg(role, chars):
    return {"role": role, "content": "a" * chars}


class TestEstimateTokens:
    def test_empty(self):
        assert estimate_tokens("") == 0

    def test_rounds_up(self):
        assert estimate_tokens("a" * 5) == 2
        assert estimate_tokens("a" * 4) == 1


class TestFitMessages:
    def test_normal_context_unchanged(self):
        messages = [
            {"role": "system", "content": "You are helpful."},
            msg("user", 100),
            msg("assistant", 100),
        ]
        result = fit_messages_to_budget(messages, context_window=100_000)
        assert result == messages

    def test_overflow_drops_oldest_first(self):
        # 30 history messages of ~100 tokens each, window only fits a few.
        history = [
            {"role": "user" if i % 2 == 0 else "assistant", "content": f"{i:04d}" + "a" * 400}
            for i in range(30)
        ]
        newest = {"role": "user", "content": "newest"}
        messages = history + [newest]
        result = fit_messages_to_budget(messages, context_window=4000)

        contents = [m["content"] for m in result if m["role"] != "system"]
        assert contents[-1] == "newest"
        # Newest history retained, oldest dropped.
        assert history[-1]["content"] in contents
        assert history[0]["content"] not in contents
        # Fits within budget.
        assert total_tokens(result) <= 4000 - RESERVE_OUTPUT_TOKENS

    def test_system_messages_preserved(self):
        system = {"role": "system", "content": "Project context:\n- keep me"}
        history = [msg("user", 2000), msg("assistant", 2000)]
        result = fit_messages_to_budget([system] + history, context_window=2000)
        assert result[0]["role"] == "system"
        assert result[0]["content"] == system["content"]

    def test_oversized_single_message_truncated(self):
        huge = msg("user", 100_000)
        result = fit_messages_to_budget([huge], context_window=2000)
        assert len(result) == 1
        assert total_tokens(result) <= 2000 - RESERVE_OUTPUT_TOKENS
        # Truncation keeps the tail (most recent content).
        assert result[0]["content"].endswith("a" * CHARS_PER_TOKEN)

    def test_very_small_context_window(self):
        # Budget is 0 after reservation; must not raise and must stay tiny.
        messages = [msg("user", 10_000)]
        result = fit_messages_to_budget(messages, context_window=64)
        assert total_tokens(result) <= max(1, 64 - RESERVE_OUTPUT_TOKENS) + PER_MESSAGE_OVERHEAD_TOKENS + CHARS_PER_TOKEN

    def test_newest_user_message_never_dropped(self):
        history = [msg("user", 500), msg("assistant", 500)]
        newest = {"role": "user", "content": "answer this"}
        result = fit_messages_to_budget(history + [newest], context_window=1100)
        assert any(m["content"] == "answer this" for m in result)

    def test_output_reservation_applied(self):
        # Content sized to fit only if reservation were ignored.
        budget_chars = (4000 - RESERVE_OUTPUT_TOKENS) * CHARS_PER_TOKEN
        messages = [{"role": "user", "content": "a" * (budget_chars + 100)}]
        result = fit_messages_to_budget(messages, context_window=4000)
        assert total_tokens(result) <= 4000 - RESERVE_OUTPUT_TOKENS

    def test_input_not_mutated(self):
        messages = [msg("user", 50_000)]
        original = messages[0]["content"]
        fit_messages_to_budget(messages, context_window=1000)
        assert messages[0]["content"] == original

    def test_empty_messages(self):
        assert fit_messages_to_budget([], context_window=4096) == []

    def test_system_only_overflow(self):
        system = {"role": "system", "content": "s" * 50_000}
        result = fit_messages_to_budget([system], context_window=2000)
        assert len(result) == 1
        assert result[0]["role"] == "system"
        assert total_tokens(result) <= 2000 - RESERVE_OUTPUT_TOKENS
