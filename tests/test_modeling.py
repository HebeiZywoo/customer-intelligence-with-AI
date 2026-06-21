from __future__ import annotations

import pandas as pd

from src.customer_ai.modeling import add_segments, extract_feature_importance

KNOWN_SEGMENTS = {
    "High-value loyalists",
    "Frequent shoppers",
    "At-risk or dormant",
    "Emerging customers",
}
ACTIONS = {"Nurture loyalty", "Send targeted offer", "Win-back campaign"}


def test_add_segments_labels(features: pd.DataFrame) -> None:
    assert "segment" in features.columns
    assert "segment_id" in features.columns
    assert set(features["segment"].unique()).issubset(KNOWN_SEGMENTS)


def test_train_metrics_are_valid(trained: dict) -> None:
    metrics = trained["metrics"]
    assert 0.0 <= metrics["roc_auc"] <= 1.0
    assert metrics["best_model"] in {"logistic_regression", "random_forest", "gradient_boosting"}
    assert len(metrics["candidate_models"]) == 3


def test_score_customers_outputs(trained: dict) -> None:
    scored = trained["scored"]
    assert scored["repeat_purchase_probability"].between(0, 1).all()
    assert set(scored["recommended_action"].unique()).issubset(ACTIONS)


def test_feature_importance_ranked(trained: dict) -> None:
    importance = extract_feature_importance(trained["model"])
    assert not importance.empty
    assert importance["importance"].is_monotonic_decreasing
    assert (importance["importance"] >= 0).all()


def test_add_segments_is_reproducible(features: pd.DataFrame) -> None:
    # KMeans uses a fixed random_state, so re-running on the same input is stable.
    plain = features.drop(columns=["segment", "segment_id"])
    again, _ = add_segments(plain)
    assert (again["segment_id"].to_numpy() == features["segment_id"].to_numpy()).all()
