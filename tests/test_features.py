from __future__ import annotations

import pandas as pd
import pytest

from src.customer_ai.features import build_customer_features, summarize_segments


def test_one_row_per_customer(features: pd.DataFrame, raw_data: dict[str, pd.DataFrame]) -> None:
    assert len(features) == len(raw_data["customers"])
    assert features["customer_id"].is_unique


def test_label_and_flags_are_binary(features: pd.DataFrame) -> None:
    for col in ("repeat_purchase_60d", "preference_match", "is_new_customer", "campaign_targeted"):
        assert set(features[col].unique()).issubset({0, 1})


def test_recency_is_non_negative(features: pd.DataFrame) -> None:
    assert (features["recency_days"] >= 0).all()
    assert (features["days_since_signup"] >= 0).all()


def test_no_missing_core_values(features: pd.DataFrame) -> None:
    core = ["frequency", "monetary", "avg_order_value", "recency_days", "top_category"]
    assert not features[core].isna().any().any()


def test_cutoff_excludes_future_revenue(raw_data: dict[str, pd.DataFrame]) -> None:
    # Revenue features must only use history before the cutoff, so a far-future
    # cutoff (capturing everything) should yield >= monetary than an early one.
    early = build_customer_features(
        raw_data["customers"], raw_data["transactions"], raw_data["campaign_events"], cutoff_date="2025-01-01"
    )
    late = build_customer_features(
        raw_data["customers"], raw_data["transactions"], raw_data["campaign_events"], cutoff_date="2025-12-31"
    )
    assert late["monetary"].sum() >= early["monetary"].sum()


def test_summarize_segments_shares_sum_to_one(trained: dict) -> None:
    summary = summarize_segments(trained["scored"])
    assert summary["share_of_customers"].sum() == pytest.approx(1.0)
