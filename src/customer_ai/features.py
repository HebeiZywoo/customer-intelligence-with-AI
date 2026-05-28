from __future__ import annotations

import pandas as pd


def build_customer_features(
    customers: pd.DataFrame,
    transactions: pd.DataFrame,
    campaign_events: pd.DataFrame,
    cutoff_date: str = "2025-10-01",
    prediction_window_days: int = 60,
) -> pd.DataFrame:
    """Create customer-level features and a future repeat-purchase label."""
    cutoff = pd.Timestamp(cutoff_date)
    prediction_end = cutoff + pd.Timedelta(days=prediction_window_days)

    customers = customers.copy()
    transactions = transactions.copy()
    campaign_events = campaign_events.copy()
    customers["signup_date"] = pd.to_datetime(customers["signup_date"])
    transactions["order_date"] = pd.to_datetime(transactions["order_date"])
    campaign_events["campaign_date"] = pd.to_datetime(campaign_events["campaign_date"])

    history = transactions[transactions["order_date"] < cutoff]
    future = transactions[
        (transactions["order_date"] >= cutoff) & (transactions["order_date"] < prediction_end)
    ]

    orders = (
        history.groupby("customer_id")
        .agg(
            frequency=("transaction_id", "nunique"),
            monetary=("revenue", "sum"),
            avg_order_value=("revenue", "mean"),
            total_quantity=("quantity", "sum"),
            avg_discount=("discount_pct", "mean"),
            last_order_date=("order_date", "max"),
            unique_categories=("category", "nunique"),
        )
        .reset_index()
    )

    category_pref = (
        history.groupby(["customer_id", "category"])["revenue"]
        .sum()
        .reset_index()
        .sort_values(["customer_id", "revenue"], ascending=[True, False])
        .drop_duplicates("customer_id")
        .rename(columns={"category": "top_category"})
        [["customer_id", "top_category"]]
    )

    campaign = (
        campaign_events[campaign_events["campaign_date"] < cutoff]
        .assign(was_targeted=lambda df: (df["treatment_group"] == "Targeted").astype(int))
        .groupby("customer_id")
        .agg(
            campaign_targeted=("was_targeted", "max"),
            campaign_converted_30d=("converted_30d", "max"),
        )
        .reset_index()
    )

    future_label = (
        future.groupby("customer_id")["transaction_id"]
        .nunique()
        .gt(0)
        .astype(int)
        .rename("repeat_purchase_60d")
        .reset_index()
    )

    features = customers.merge(orders, on="customer_id", how="left")
    features = features.merge(category_pref, on="customer_id", how="left")
    features = features.merge(campaign, on="customer_id", how="left")
    features = features.merge(future_label, on="customer_id", how="left")

    numeric_defaults = {
        "frequency": 0,
        "monetary": 0,
        "avg_order_value": 0,
        "total_quantity": 0,
        "avg_discount": 0,
        "unique_categories": 0,
        "campaign_targeted": 0,
        "campaign_converted_30d": 0,
        "repeat_purchase_60d": 0,
    }
    features = features.fillna(value=numeric_defaults)
    features["top_category"] = features["top_category"].fillna("No purchase yet")
    features["recency_days"] = (cutoff - features["last_order_date"]).dt.days
    features["recency_days"] = features["recency_days"].fillna(999)
    features["days_since_signup"] = (cutoff - features["signup_date"]).dt.days.clip(lower=0)
    features["orders_per_100_days"] = features["frequency"] / (features["days_since_signup"] + 1) * 100
    features["monetary_per_100_days"] = features["monetary"] / (features["days_since_signup"] + 1) * 100
    features["discounted_revenue"] = features["monetary"] * features["avg_discount"]
    features["preference_match"] = (features["preferred_category"] == features["top_category"]).astype(int)
    features["is_new_customer"] = (features["days_since_signup"] <= 90).astype(int)
    features["repeat_purchase_60d"] = features["repeat_purchase_60d"].astype(int)

    return features.drop(columns=["last_order_date"])


def summarize_segments(features: pd.DataFrame) -> pd.DataFrame:
    summary = (
        features.groupby("segment")
        .agg(
            customers=("customer_id", "count"),
            avg_recency_days=("recency_days", "mean"),
            avg_frequency=("frequency", "mean"),
            avg_monetary=("monetary", "mean"),
            repeat_purchase_rate=("repeat_purchase_60d", "mean"),
            campaign_conversion_rate=("campaign_converted_30d", "mean"),
        )
        .reset_index()
    )
    summary["share_of_customers"] = summary["customers"] / summary["customers"].sum()
    return summary.sort_values("avg_monetary", ascending=False)
