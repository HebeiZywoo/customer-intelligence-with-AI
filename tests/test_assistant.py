from __future__ import annotations

from src.customer_ai.assistant import answer_question, build_insight_context


def _context(trained: dict) -> dict:
    return build_insight_context(trained["scored"], trained["segment_summary"], trained["metrics"])


def test_build_insight_context_keys(trained: dict) -> None:
    context = _context(trained)
    assert {"total_customers", "top_segment", "best_conversion_segment", "model_metrics"} <= set(context)
    assert context["total_customers"] == len(trained["scored"])


def test_answer_question_routes_to_topics(trained: dict) -> None:
    context = _context(trained)
    assert "Target" in answer_question("who should we target with a campaign?", context)
    assert "win-back" in answer_question("which customers are at churn risk?", context).lower()
    assert "ROC AUC" in answer_question("how good is the model?", context)
    assert "valuable" in answer_question("which segment is most valuable?", context).lower()
    # Unrecognized questions fall back to the overview.
    assert "customers in the analysis" in answer_question("hello there", context)
