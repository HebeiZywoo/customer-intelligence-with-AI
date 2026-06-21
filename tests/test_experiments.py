from __future__ import annotations

import pandas as pd
import pytest

from src.customer_ai.experiments import _two_group_lift, build_campaign_experiment_outputs


def test_two_group_lift_known_values() -> None:
    events = pd.DataFrame(
        {
            "treatment_group": ["Targeted"] * 200 + ["Holdout"] * 200,
            "converted_30d": [1] * 60 + [0] * 140 + [1] * 40 + [0] * 160,  # 0.30 vs 0.20
        }
    )
    result = _two_group_lift(events).iloc[0]
    assert result["targeted_conversion_rate"] == 0.30
    assert result["holdout_conversion_rate"] == 0.20
    assert result["absolute_lift"] == 0.10
    assert result["targeted_customers"] == 200
    assert result["lift_ci_low"] <= result["absolute_lift"] <= result["lift_ci_high"]


def test_campaign_outputs_structure(raw_data: dict[str, pd.DataFrame], trained: dict) -> None:
    summary, segment_lift = build_campaign_experiment_outputs(raw_data["campaign_events"], trained["scored"])
    row = summary.iloc[0]
    assert {"absolute_lift", "net_profit", "roi", "incremental_revenue"}.issubset(summary.columns)
    assert row["campaign_cost"] >= 0
    assert not segment_lift.empty
    assert segment_lift["absolute_lift"].is_monotonic_decreasing


def test_roi_consistency(raw_data: dict[str, pd.DataFrame], trained: dict) -> None:
    summary, _ = build_campaign_experiment_outputs(raw_data["campaign_events"], trained["scored"])
    row = summary.iloc[0]
    # net_profit = incremental_margin - campaign_cost, by construction.
    assert row["net_profit"] == pytest.approx(row["incremental_margin"] - row["campaign_cost"], abs=0.01)
