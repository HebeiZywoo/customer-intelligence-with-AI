from __future__ import annotations

import pandas as pd


def build_insight_context(customers: pd.DataFrame, segment_summary: pd.DataFrame, metrics: dict) -> dict:
    top_segment = segment_summary.sort_values("avg_monetary", ascending=False).iloc[0]
    best_conversion = segment_summary.sort_values("campaign_conversion_rate", ascending=False).iloc[0]
    at_risk = segment_summary.sort_values("avg_recency_days", ascending=False).iloc[0]

    high_intent = customers[customers["repeat_purchase_probability"] >= 0.55]
    offer_candidates = customers[
        (customers["repeat_purchase_probability"] >= 0.30)
        & (customers["repeat_purchase_probability"] < 0.55)
    ]

    return {
        "total_customers": int(len(customers)),
        "top_segment": top_segment.to_dict(),
        "best_conversion_segment": best_conversion.to_dict(),
        "at_risk_segment": at_risk.to_dict(),
        "high_intent_count": int(len(high_intent)),
        "offer_candidate_count": int(len(offer_candidates)),
        "model_metrics": metrics,
    }


def answer_question(question: str, context: dict) -> str:
    """Return a grounded recommendation using project metrics as evidence."""
    normalized = question.lower().strip()

    if any(term in normalized for term in ["target", "campaign", "offer", "marketing", "coupon"]):
        segment = context["best_conversion_segment"]
        return (
            f"Target the {segment['segment']} segment first. It has the strongest campaign conversion "
            f"rate at {segment['campaign_conversion_rate']:.1%}, with average monetary value of "
            f"${segment['avg_monetary']:.0f}. Use a holdout group so the team can measure incremental lift."
        )

    if any(term in normalized for term in ["churn", "risk", "dormant", "win-back", "winback"]):
        segment = context["at_risk_segment"]
        return (
            f"The riskiest group is {segment['segment']}. Their average recency is "
            f"{segment['avg_recency_days']:.0f} days, so I would use a win-back campaign with a clear "
            f"deadline and track repeat purchase within 60 days."
        )

    if any(term in normalized for term in ["model", "performance", "auc", "accuracy", "predict"]):
        metrics = context["model_metrics"]
        return (
            f"The best repeat-purchase model is {metrics.get('best_model', 'the selected model')} with "
            f"ROC AUC {metrics['roc_auc']:.3f}, precision "
            f"{metrics['precision']:.3f}, and recall {metrics['recall']:.3f}. I would discuss ROC AUC "
            f"as the main ranking metric because marketing teams usually care about prioritizing customers."
        )

    if any(term in normalized for term in ["segment", "valuable", "revenue", "rfm"]):
        segment = context["top_segment"]
        return (
            f"The most valuable segment is {segment['segment']}, with average monetary value of "
            f"${segment['avg_monetary']:.0f} and average frequency of {segment['avg_frequency']:.1f}. "
            f"This is the group to protect with loyalty benefits rather than heavy discounts."
        )

    return (
        f"There are {context['total_customers']:,} customers in the analysis. A strong next step is to "
        f"compare the {context['offer_candidate_count']:,} targeted-offer candidates against a holdout "
        f"group, then monitor 60-day repeat purchase and campaign lift."
    )
