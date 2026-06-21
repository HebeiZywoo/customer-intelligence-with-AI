"""Tests for the optional Claude-powered assistant.

No real API calls are made — the Anthropic client is monkeypatched so the test
suite stays hermetic and free.
"""

from __future__ import annotations

import json
import sys
import types

import pytest

from src.customer_ai import llm


def test_models_include_default() -> None:
    assert llm.DEFAULT_MODEL in llm.MODELS.values()


def test_resolve_api_key_prefers_explicit(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "env-key")
    assert llm.resolve_api_key("explicit-key") == "explicit-key"
    assert llm.resolve_api_key() == "env-key"
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    assert llm.resolve_api_key() is None


def test_llm_available_requires_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    assert llm.llm_available() is False
    assert llm.llm_available("a-key") is True


def test_format_context_is_deterministic() -> None:
    context = {"b": 2, "a": 1, "nested": {"y": 1, "x": 2}}
    first = llm.format_context(context)
    second = llm.format_context(context)
    assert first == second
    # Sorted keys make the prompt stable regardless of dict insertion order.
    assert first.index('"a"') < first.index('"b"')
    assert json.loads(first) == context


def _install_fake_anthropic(monkeypatch: pytest.MonkeyPatch, captured: dict) -> None:
    """Register a fake `anthropic` module that records the create() call."""

    class _TextBlock:
        type = "text"
        text = "Target the High-value loyalists segment first."

    class _Message:
        content = [_TextBlock()]

    class _Messages:
        def create(self, **kwargs):
            captured.update(kwargs)
            return _Message()

    class _FakeClient:
        def __init__(self, api_key=None):
            captured["api_key"] = api_key
            self.messages = _Messages()

    fake_module = types.ModuleType("anthropic")
    fake_module.Anthropic = _FakeClient
    monkeypatch.setitem(sys.modules, "anthropic", fake_module)


def test_answer_with_llm_builds_grounded_request(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict = {}
    _install_fake_anthropic(monkeypatch, captured)

    context = {"top_segment": {"segment": "High-value loyalists", "avg_monetary": 312}}
    answer = llm.answer_with_llm("Who should we target?", context, api_key="k", model="claude-opus-4-8")

    assert answer == "Target the High-value loyalists segment first."
    assert captured["model"] == "claude-opus-4-8"
    assert captured["api_key"] == "k"
    # The grounding facts and the question both reach the model.
    user_content = captured["messages"][0]["content"]
    assert "High-value loyalists" in user_content
    assert "Who should we target?" in user_content
    assert "only" in captured["system"].lower()
