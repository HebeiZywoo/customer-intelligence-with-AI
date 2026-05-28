from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.customer_ai.assistant import answer_question, build_insight_context


PROCESSED_DIR = ROOT / "data" / "processed"
REQUIRED_OUTPUTS = [
    PROCESSED_DIR / "customer_features.csv",
    PROCESSED_DIR / "segment_summary.csv",
    PROCESSED_DIR / "model_metrics.json",
    PROCESSED_DIR / "feature_importance.csv",
    PROCESSED_DIR / "campaign_experiment_summary.csv",
    PROCESSED_DIR / "campaign_segment_lift.csv",
]


st.set_page_config(
    page_title="Customer Intelligence AI",
    page_icon=":bar_chart:",
    layout="wide",
)


@st.cache_data
def load_outputs() -> tuple[
    pd.DataFrame,
    pd.DataFrame,
    dict,
    dict[str, pd.DataFrame],
    pd.DataFrame,
    pd.DataFrame,
    pd.DataFrame,
]:
    customers_path = PROCESSED_DIR / "customer_features.csv"
    summary_path = PROCESSED_DIR / "segment_summary.csv"
    metrics_path = PROCESSED_DIR / "model_metrics.json"

    if not customers_path.exists() or not summary_path.exists() or not metrics_path.exists():
        return (
            pd.DataFrame(),
            pd.DataFrame(),
            {},
            {},
            pd.DataFrame(),
            pd.DataFrame(),
            pd.DataFrame(),
        )

    customers = pd.read_csv(customers_path)
    segment_summary = pd.read_csv(summary_path)
    metrics = json.loads(metrics_path.read_text())
    sql_outputs = {}
    for path in PROCESSED_DIR.glob("sql_*.csv"):
        sql_outputs[path.stem] = pd.read_csv(path)
    feature_importance = _read_optional_csv("feature_importance.csv")
    experiment_summary = _read_optional_csv("campaign_experiment_summary.csv")
    segment_lift = _read_optional_csv("campaign_segment_lift.csv")
    return customers, segment_summary, metrics, sql_outputs, feature_importance, experiment_summary, segment_lift


def ensure_pipeline_outputs() -> None:
    if all(path.exists() for path in REQUIRED_OUTPUTS):
        return

    steps = [
        [sys.executable, "scripts/generate_data.py"],
        [sys.executable, "scripts/train_models.py"],
        [sys.executable, "scripts/run_sql_analysis.py"],
    ]
    for step in steps:
        subprocess.run(step, cwd=ROOT, check=True)


def _read_optional_csv(filename: str) -> pd.DataFrame:
    path = PROCESSED_DIR / filename
    if path.exists():
        return pd.read_csv(path)
    return pd.DataFrame()


with st.spinner("Preparing customer intelligence outputs..."):
    ensure_pipeline_outputs()

customers, segment_summary, metrics, sql_outputs, feature_importance, experiment_summary, segment_lift = load_outputs()

st.title("AI-Powered Customer Intelligence Platform")

if customers.empty:
    st.info("Run `python scripts/generate_data.py` and `python scripts/train_models.py` first.")
    st.stop()

top_segment = segment_summary.sort_values("avg_monetary", ascending=False).iloc[0]
top_segment_display = str(top_segment["segment"]).replace("High-value loyalists", "High-value")
offer_candidates = customers[customers["recommended_action"] == "Send targeted offer"]
experiment = experiment_summary.iloc[0] if not experiment_summary.empty else None
lift = experiment["absolute_lift"] if experiment is not None else 0
roi = experiment["roi"] if experiment is not None else 0

st.subheader("Executive Brief")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Recommended Segment", top_segment_display)
c2.metric("Offer Candidates", f"{len(offer_candidates):,}")
c3.metric("Campaign Lift", f"{lift:.1%}")
c4.metric("Projected ROI", f"{roi:.1%}")

st.write(
    f"Prioritize {top_segment['segment']} for retention and use targeted offers for "
    f"{len(offer_candidates):,} mid-probability customers. The experiment estimates "
    f"{lift:.1%} absolute lift, so the recommended plan is to launch with a holdout group "
    f"and monitor 60-day repeat purchase."
)

if experiment is not None:
    left, right = st.columns([1, 1])
    with left:
        st.write("Expected business impact")
        impact = pd.DataFrame(
            [
                ["Incremental conversions", f"{experiment['incremental_conversions']:,.1f}"],
                ["Incremental revenue", f"${experiment['incremental_revenue']:,.0f}"],
                ["Incremental margin", f"${experiment['incremental_margin']:,.0f}"],
                ["Campaign cost", f"${experiment['campaign_cost']:,.0f}"],
                ["Net profit", f"${experiment['net_profit']:,.0f}"],
            ],
            columns=["Metric", "Value"],
        )
        st.dataframe(impact, use_container_width=True, hide_index=True)
    with right:
        st.write("Decision guardrails")
        guardrails = pd.DataFrame(
            [
                ["Use a holdout group", "Measure incremental impact, not just conversion."],
                ["Cap discount exposure", "Avoid sending coupons to likely repeat buyers."],
                ["Review CI before scaling", "Scale only if the lift interval remains positive."],
                ["Monitor segment drift", "Re-score customers before each campaign wave."],
            ],
            columns=["Guardrail", "Reason"],
        )
        st.dataframe(guardrails, use_container_width=True, hide_index=True)

tabs = st.tabs(["Overview", "Segments", "Prediction", "Experiment", "SQL Insights", "AI Assistant"])

with tabs[0]:
    total_revenue = customers["monetary"].sum()
    repeat_rate = customers["repeat_purchase_60d"].mean()
    avg_probability = customers["repeat_purchase_probability"].mean()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Customers", f"{len(customers):,}")
    c2.metric("Historical Revenue", f"${total_revenue:,.0f}")
    c3.metric("60-Day Repeat Rate", f"{repeat_rate:.1%}")
    c4.metric("Avg Predicted Repeat", f"{avg_probability:.1%}")

    left, right = st.columns([1.1, 1])
    with left:
        revenue_by_segment = customers.groupby("segment", as_index=False)["monetary"].sum()
        st.plotly_chart(
            px.bar(
                revenue_by_segment,
                x="segment",
                y="monetary",
                title="Revenue by Segment",
                labels={"segment": "", "monetary": "Revenue"},
            ),
            use_container_width=True,
        )
    with right:
        action_counts = customers["recommended_action"].value_counts().reset_index()
        action_counts.columns = ["recommended_action", "customers"]
        st.plotly_chart(
            px.pie(
                action_counts,
                names="recommended_action",
                values="customers",
                title="Recommended Marketing Actions",
                hole=0.45,
            ),
            use_container_width=True,
        )

with tabs[1]:
    st.dataframe(
        segment_summary.assign(
            repeat_purchase_rate=lambda df: df["repeat_purchase_rate"].map("{:.1%}".format),
            campaign_conversion_rate=lambda df: df["campaign_conversion_rate"].map("{:.1%}".format),
            share_of_customers=lambda df: df["share_of_customers"].map("{:.1%}".format),
            avg_monetary=lambda df: df["avg_monetary"].map("${:,.0f}".format),
        ),
        use_container_width=True,
        hide_index=True,
    )

    scatter = customers.sample(min(900, len(customers)), random_state=42)
    st.plotly_chart(
        px.scatter(
            scatter,
            x="recency_days",
            y="monetary",
            color="segment",
            size="frequency",
            hover_data=["customer_id", "recommended_action"],
            title="RFM Segment Map",
        ),
        use_container_width=True,
    )

with tabs[2]:
    st.caption(f"Best model: {metrics.get('best_model', 'selected model')}")
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("ROC AUC", f"{metrics['roc_auc']:.3f}")
    c2.metric("Precision", f"{metrics['precision']:.3f}")
    c3.metric("Recall", f"{metrics['recall']:.3f}")
    c4.metric("F1", f"{metrics['f1']:.3f}")
    c5.metric("Positive Rate", f"{metrics['positive_rate']:.1%}")

    if "candidate_models" in metrics:
        st.dataframe(
            pd.DataFrame(metrics["candidate_models"]).sort_values("roc_auc", ascending=False),
            use_container_width=True,
            hide_index=True,
        )

    if not feature_importance.empty:
        st.write("Top Model Drivers")
        top_features = feature_importance.head(15).sort_values("importance")
        st.plotly_chart(
            px.bar(
                top_features,
                x="importance",
                y="feature",
                orientation="h",
                title="Feature Importance",
                labels={"importance": "Importance", "feature": ""},
            ),
            use_container_width=True,
        )
        st.dataframe(
            feature_importance[
                ["feature", "importance", "normalized_importance", "importance_type"]
            ].head(20),
            use_container_width=True,
            hide_index=True,
        )

    segment_filter = st.multiselect(
        "Segment",
        sorted(customers["segment"].unique()),
        default=sorted(customers["segment"].unique()),
    )
    action_filter = st.multiselect(
        "Recommended action",
        sorted(customers["recommended_action"].unique()),
        default=sorted(customers["recommended_action"].unique()),
    )
    filtered = customers[
        customers["segment"].isin(segment_filter)
        & customers["recommended_action"].isin(action_filter)
    ].sort_values("repeat_purchase_probability", ascending=False)

    st.dataframe(
        filtered[
            [
                "customer_id",
                "segment",
                "region",
                "acquisition_channel",
                "monetary",
                "frequency",
                "recency_days",
                "repeat_purchase_probability",
                "recommended_action",
            ]
        ].head(200),
        use_container_width=True,
        hide_index=True,
    )

with tabs[3]:
    st.subheader("Campaign Experiment")
    if experiment_summary.empty:
        st.info("Run `python scripts/run_sql_analysis.py` to build experiment outputs.")
    else:
        experiment = experiment_summary.iloc[0]
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Targeted Conversion", f"{experiment['targeted_conversion_rate']:.1%}")
        c2.metric("Holdout Conversion", f"{experiment['holdout_conversion_rate']:.1%}")
        c3.metric("Absolute Lift", f"{experiment['absolute_lift']:.1%}")
        c4.metric("P-value", f"{experiment['p_value']:.4f}")

        st.write(
            f"95% confidence interval for lift: {experiment['lift_ci_low']:.1%} to "
            f"{experiment['lift_ci_high']:.1%}. ROI estimate uses a "
            f"{experiment['assumed_margin_rate']:.0%} gross margin assumption and "
            f"${experiment['offer_cost_per_customer']:.0f} cost per targeted customer."
        )

        roi_frame = pd.DataFrame(
            [
                ["Target candidates", f"{experiment['target_candidate_count']:,.0f}"],
                ["Avg order value", f"${experiment['avg_order_value']:,.2f}"],
                ["Incremental conversions", f"{experiment['incremental_conversions']:,.1f}"],
                ["Incremental revenue", f"${experiment['incremental_revenue']:,.0f}"],
                ["Campaign cost", f"${experiment['campaign_cost']:,.0f}"],
                ["Net profit", f"${experiment['net_profit']:,.0f}"],
                ["ROI", f"{experiment['roi']:.1%}"],
            ],
            columns=["Metric", "Value"],
        )
        st.dataframe(roi_frame, use_container_width=True, hide_index=True)

        if not segment_lift.empty:
            st.write("Lift by Segment")
            st.dataframe(segment_lift, use_container_width=True, hide_index=True)

with tabs[4]:
    st.subheader("DuckDB SQL Outputs")
    if not sql_outputs:
        st.info("Run `python scripts/run_sql_analysis.py` to build SQL analysis outputs.")
    else:
        if "sql_campaign_lift" in sql_outputs:
            lift = sql_outputs["sql_campaign_lift"].iloc[0]
            c1, c2, c3 = st.columns(3)
            c1.metric("Targeted Conversion", f"{lift['targeted_conversion_rate']:.1%}")
            c2.metric("Holdout Conversion", f"{lift['holdout_conversion_rate']:.1%}")
            c3.metric("Relative Lift", f"{lift['relative_lift']:.1%}")

        for label, key in [
            ("Segment Performance", "sql_segment_performance"),
            ("Acquisition Channel Cohorts", "sql_channel_cohorts"),
            ("Lifecycle Stages", "sql_lifecycle_stages"),
            ("Campaign Lift", "sql_campaign_lift"),
        ]:
            if key in sql_outputs:
                st.write(label)
                st.dataframe(sql_outputs[key], use_container_width=True, hide_index=True)

with tabs[5]:
    context = build_insight_context(customers, segment_summary, metrics)
    examples = [
        "Which segment should marketing target next?",
        "Which customers are at churn risk?",
        "How good is the prediction model?",
        "Which segment is most valuable?",
    ]
    question = st.selectbox("Ask a business question", examples)
    custom_question = st.text_input("Or type your own question")
    final_question = custom_question or question
    st.write(answer_question(final_question, context))
