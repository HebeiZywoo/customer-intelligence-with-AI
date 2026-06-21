"""Optional Claude-powered analyst assistant.

The dashboard ships with a deterministic rule-based assistant (``assistant.py``)
so it always runs without external services. When an Anthropic API key is
available, this module upgrades the assistant to a grounded LLM that answers
over the project's computed metrics via the Claude Messages API.

The model is instructed to answer *only* from the supplied context, which keeps
answers tied to the numbers the pipeline actually produced rather than the
model's parametric knowledge.
"""

from __future__ import annotations

import json
import os

# Friendly label -> Anthropic model ID. Opus 4.8 is the default (most capable).
MODELS: dict[str, str] = {
    "Claude Opus 4.8 (most capable)": "claude-opus-4-8",
    "Claude Sonnet 4.6 (balanced)": "claude-sonnet-4-6",
    "Claude Haiku 4.5 (fastest)": "claude-haiku-4-5",
}
DEFAULT_MODEL = "claude-opus-4-8"

SYSTEM_PROMPT = (
    "You are a senior customer-analytics partner embedded in a retention and "
    "campaign-ROI dashboard. Answer the user's business question using ONLY the "
    "facts in the provided context block. Cite the relevant numbers (segments, "
    "rates, lift, ROI, model metrics) so the recommendation is auditable. If the "
    "context does not contain what is needed to answer, say so plainly and name "
    "the analysis that would be required. Never invent segments, metrics, or "
    "figures that are not present in the context. Keep answers to 2-4 sentences "
    "in a clear, executive tone."
)


def resolve_api_key(explicit: str | None = None) -> str | None:
    """Return an API key from the explicit argument or the environment."""
    return explicit or os.environ.get("ANTHROPIC_API_KEY")


def llm_available(api_key: str | None = None) -> bool:
    """True when the Anthropic SDK is importable and a key is configured."""
    try:
        import anthropic  # noqa: F401
    except ImportError:
        return False
    return bool(resolve_api_key(api_key))


def format_context(context: dict) -> str:
    """Serialize the grounding context deterministically for the prompt."""
    return json.dumps(context, indent=2, sort_keys=True, default=str)


def answer_with_llm(
    question: str,
    context: dict,
    *,
    api_key: str | None = None,
    model: str = DEFAULT_MODEL,
    max_tokens: int = 1024,
) -> str:
    """Answer a grounded business question with Claude.

    Raises ``RuntimeError`` if the SDK is unavailable so callers can fall back
    to the rule-based assistant.
    """
    try:
        import anthropic
    except ImportError as exc:  # pragma: no cover - exercised via llm_available
        raise RuntimeError("The anthropic SDK is not installed.") from exc

    key = resolve_api_key(api_key)
    client = anthropic.Anthropic(api_key=key) if key else anthropic.Anthropic()
    facts = format_context(context)
    message = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": f"Context (JSON facts):\n{facts}\n\nQuestion: {question}",
            }
        ],
    )
    return "".join(block.text for block in message.content if block.type == "text").strip()
