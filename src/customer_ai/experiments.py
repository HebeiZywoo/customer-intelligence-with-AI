from __future__ import annotations

from math import erfc, sqrt

import pandas as pd

Z_95 = 1.96


def build_campaign_experiment_outputs(
    campaign_events: pd.DataFrame,
    customer_features: pd.DataFrame,
    margin_rate: float = 0.45,
    offer_cost_per_customer: float = 2.0,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    campaign = campaign_events.copy()
    campaign["is_treated"] = (campaign["treatment_group"] == "Targeted").astype(int)

    summary = _two_group_lift(campaign)
    target_candidates = customer_features[customer_features["recommended_action"] == "Send targeted offer"].copy()
    candidate_count = len(target_candidates)
    avg_order_value = target_candidates.loc[target_candidates["avg_order_value"] > 0, "avg_order_value"].mean()
    if pd.isna(avg_order_value):
        avg_order_value = customer_features.loc[customer_features["avg_order_value"] > 0, "avg_order_value"].mean()

    absolute_lift = max(float(summary["absolute_lift"].iloc[0]), 0)
    incremental_conversions = candidate_count * absolute_lift
    incremental_revenue = incremental_conversions * float(avg_order_value)
    incremental_margin = incremental_revenue * margin_rate
    campaign_cost = candidate_count * offer_cost_per_customer
    net_profit = incremental_margin - campaign_cost
    roi = net_profit / campaign_cost if campaign_cost else 0

    summary = summary.assign(
        target_candidate_count=candidate_count,
        avg_order_value=round(float(avg_order_value), 2),
        assumed_margin_rate=margin_rate,
        offer_cost_per_customer=offer_cost_per_customer,
        incremental_conversions=round(float(incremental_conversions), 2),
        incremental_revenue=round(float(incremental_revenue), 2),
        incremental_margin=round(float(incremental_margin), 2),
        campaign_cost=round(float(campaign_cost), 2),
        net_profit=round(float(net_profit), 2),
        roi=round(float(roi), 4),
    )

    segment_events = campaign.merge(
        customer_features[["customer_id", "segment"]],
        on="customer_id",
        how="left",
    )
    segment_lift = (
        segment_events.groupby("segment", dropna=False)
        .apply(_two_group_lift, include_groups=False)
        .reset_index(level=1, drop=True)
        .reset_index()
        .sort_values("absolute_lift", ascending=False)
    )
    return summary, segment_lift


def _two_group_lift(events: pd.DataFrame) -> pd.DataFrame:
    grouped = (
        events.groupby("treatment_group")["converted_30d"]
        .agg(["sum", "count"])
        .reindex(["Targeted", "Holdout"], fill_value=0)
    )
    treated_conversions = float(grouped.loc["Targeted", "sum"])
    treated_n = float(grouped.loc["Targeted", "count"])
    holdout_conversions = float(grouped.loc["Holdout", "sum"])
    holdout_n = float(grouped.loc["Holdout", "count"])

    treated_rate = treated_conversions / treated_n if treated_n else 0
    holdout_rate = holdout_conversions / holdout_n if holdout_n else 0
    lift = treated_rate - holdout_rate
    se = sqrt(treated_rate * (1 - treated_rate) / treated_n + holdout_rate * (1 - holdout_rate) / holdout_n)
    ci_low = lift - Z_95 * se
    ci_high = lift + Z_95 * se
    z_score = lift / se if se else 0
    p_value = erfc(abs(z_score) / sqrt(2)) if se else 1

    return pd.DataFrame(
        [
            {
                "targeted_customers": int(treated_n),
                "holdout_customers": int(holdout_n),
                "targeted_conversion_rate": round(treated_rate, 4),
                "holdout_conversion_rate": round(holdout_rate, 4),
                "absolute_lift": round(lift, 4),
                "relative_lift": round(lift / holdout_rate, 4) if holdout_rate else 0,
                "lift_ci_low": round(ci_low, 4),
                "lift_ci_high": round(ci_high, 4),
                "p_value": round(p_value, 4),
            }
        ]
    )
