from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.customer_ai import llm
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
UPLOAD_REQUIRED_COLUMNS = {
    "customer_id",
    "segment",
    "monetary",
    "frequency",
    "recency_days",
    "repeat_purchase_probability",
    "recommended_action",
}


st.set_page_config(
    page_title="Customer Intelligence & Campaign ROI",
    page_icon=":bar_chart:",
    layout="wide",
)


# --- Charts ----------------------------------------------------------------
# A small Altair toolkit so every chart shares one palette and a clean look.

TEAL = "#0f766e"
BLUE = "#2563eb"
AMBER = "#d97706"
GREEN = "#059669"
SLATE = "#64748b"
GRID = "#e4ecec"
SEGMENT_RANGE = [TEAL, BLUE, AMBER, "#7c3aed"]


def _style(chart: alt.Chart | alt.LayerChart, height: int = 300) -> alt.Chart:
    """Apply the shared theme and stretch to the container width."""
    return (
        chart.properties(height=height, width="container")
        .configure(background="transparent")
        .configure_view(strokeWidth=0)
        .configure_axis(
            grid=True,
            gridColor=GRID,
            gridDash=[2, 3],
            domain=False,
            tickSize=0,
            labelColor=SLATE,
            labelFontSize=11,
            titleColor="#334155",
            titleFontSize=12,
            titleFontWeight=600,
            labelPadding=6,
            titlePadding=10,
        )
        .configure_axisX(grid=False)
        .configure_legend(
            orient="top",
            labelColor="#334155",
            titleColor=SLATE,
            labelFontSize=11,
            symbolType="circle",
            symbolSize=90,
        )
    )


def _labeled_hbar(
    data: pd.DataFrame, value: str, label: str, color: str, value_format: str, tooltips: list
) -> alt.Chart:
    base = alt.Chart(data).encode(
        y=alt.Y(f"{label}:N", sort="-x", title=None),
        x=alt.X(f"{value}:Q", title=None),
    )
    bars = base.mark_bar(cornerRadiusEnd=4, color=color).encode(tooltip=tooltips)
    text = base.mark_text(align="left", dx=4, color=SLATE, fontSize=11).encode(
        text=alt.Text(f"{value}:Q", format=value_format)
    )
    return _style(bars + text, height=max(220, 34 * len(data)))


def revenue_by_segment_chart(customers: pd.DataFrame) -> alt.Chart:
    data = customers.groupby("segment", as_index=False)["monetary"].sum().rename(columns={"monetary": "revenue"})
    return _labeled_hbar(
        data,
        value="revenue",
        label="segment",
        color=TEAL,
        value_format="$,.0f",
        tooltips=[
            alt.Tooltip("segment:N", title="Segment"),
            alt.Tooltip("revenue:Q", title="Revenue", format="$,.0f"),
        ],
    )


def actions_chart(customers: pd.DataFrame) -> alt.Chart:
    data = customers["recommended_action"].value_counts().rename_axis("action").reset_index(name="customers")
    return _labeled_hbar(
        data,
        value="customers",
        label="action",
        color=BLUE,
        value_format=",.0f",
        tooltips=[
            alt.Tooltip("action:N", title="Action"),
            alt.Tooltip("customers:Q", title="Customers", format=",.0f"),
        ],
    )


def rfm_scatter_chart(customers: pd.DataFrame) -> alt.Chart:
    sample = customers.sample(min(900, len(customers)), random_state=42)
    chart = (
        alt.Chart(sample)
        .mark_circle(opacity=0.6)
        .encode(
            x=alt.X("recency_days:Q", title="Recency (days since last order)"),
            y=alt.Y("monetary:Q", title="Monetary value ($)"),
            color=alt.Color("segment:N", title=None, scale=alt.Scale(range=SEGMENT_RANGE)),
            size=alt.Size("frequency:Q", title="Orders", scale=alt.Scale(range=[20, 320]), legend=None),
            tooltip=[
                alt.Tooltip("segment:N", title="Segment"),
                alt.Tooltip("recency_days:Q", title="Recency"),
                alt.Tooltip("monetary:Q", title="Monetary", format="$,.0f"),
                alt.Tooltip("frequency:Q", title="Orders"),
            ],
        )
    )
    return _style(chart, height=360)


def model_comparison_chart(candidates: pd.DataFrame) -> alt.Chart:
    data = candidates.copy()
    data["model_name"] = data["model_name"].str.replace("_", " ").str.title()
    upper = max(0.8, float(data["roc_auc"].max()) + 0.02)
    base = alt.Chart(data).encode(
        y=alt.Y("model_name:N", sort="-x", title=None),
        x=alt.X("roc_auc:Q", title="ROC AUC", scale=alt.Scale(domain=[0.5, upper])),
    )
    bars = base.mark_bar(cornerRadiusEnd=4, color=TEAL).encode(
        tooltip=[alt.Tooltip("model_name:N", title="Model"), alt.Tooltip("roc_auc:Q", title="ROC AUC", format=".3f")]
    )
    text = base.mark_text(align="left", dx=4, color=SLATE, fontSize=11).encode(text=alt.Text("roc_auc:Q", format=".3f"))
    return _style(bars + text, height=200)


def importance_chart(feature_importance: pd.DataFrame) -> alt.Chart:
    data = feature_importance.head(12)
    chart = (
        alt.Chart(data)
        .mark_bar(cornerRadiusEnd=4, color=TEAL)
        .encode(
            y=alt.Y("feature:N", sort="-x", title=None),
            x=alt.X("importance:Q", title="Importance"),
            tooltip=[
                alt.Tooltip("feature:N", title="Feature"),
                alt.Tooltip("importance:Q", title="Importance", format=".3f"),
            ],
        )
    )
    return _style(chart, height=360)


def conversion_chart(experiment: pd.Series) -> alt.Chart:
    data = pd.DataFrame(
        {
            "group": ["Targeted", "Holdout"],
            "rate": [experiment["targeted_conversion_rate"], experiment["holdout_conversion_rate"]],
        }
    )
    base = alt.Chart(data).encode(
        x=alt.X("group:N", title=None, axis=alt.Axis(labelAngle=0)),
        y=alt.Y("rate:Q", title="30-day conversion", axis=alt.Axis(format="%")),
    )
    bars = base.mark_bar(cornerRadiusTopLeft=5, cornerRadiusTopRight=5, width=70).encode(
        color=alt.Color("group:N", scale=alt.Scale(domain=["Targeted", "Holdout"], range=[TEAL, SLATE]), legend=None),
        tooltip=[alt.Tooltip("group:N", title="Group"), alt.Tooltip("rate:Q", title="Conversion", format=".1%")],
    )
    text = base.mark_text(dy=-8, color="#334155", fontSize=12, fontWeight=600).encode(
        text=alt.Text("rate:Q", format=".1%")
    )
    return _style(bars + text, height=300)


def segment_lift_chart(segment_lift: pd.DataFrame) -> alt.Chart:
    data = segment_lift.dropna(subset=["segment"]).copy()
    chart = (
        alt.Chart(data)
        .mark_bar(cornerRadiusEnd=4)
        .encode(
            y=alt.Y("segment:N", sort="-x", title=None),
            x=alt.X("absolute_lift:Q", title="Absolute lift", axis=alt.Axis(format="%")),
            color=alt.condition(alt.datum.absolute_lift >= 0, alt.value(GREEN), alt.value(AMBER)),
            tooltip=[
                alt.Tooltip("segment:N", title="Segment"),
                alt.Tooltip("absolute_lift:Q", title="Lift", format=".1%"),
            ],
        )
    )
    return _style(chart, height=max(220, 36 * len(data)))


# --- HTML components -------------------------------------------------------


def metric_card(label: str, value: str, detail: str, tone: str = "neutral") -> None:
    st.markdown(
        f"""
        <div class="metric-card {tone}">
          <div class="metric-label">{label}</div>
          <div class="metric-value">{value}</div>
          <div class="metric-detail">{detail}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def decision_panel(title: str, body: str, chips: list[str]) -> None:
    chip_html = "".join([f"<span>{chip}</span>" for chip in chips])
    st.markdown(
        f"""
        <div class="decision-panel">
          <div class="decision-kicker">Recommendation</div>
          <div class="decision-title">{title}</div>
          <div class="decision-body">{body}</div>
          <div class="decision-chips">{chip_html}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# --- Data loading ----------------------------------------------------------


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
        return (pd.DataFrame(), pd.DataFrame(), {}, {}, pd.DataFrame(), pd.DataFrame(), pd.DataFrame())

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


def get_anthropic_key() -> str | None:
    """Read the Anthropic key from Streamlit secrets or the environment."""
    try:
        if "ANTHROPIC_API_KEY" in st.secrets:
            return str(st.secrets["ANTHROPIC_API_KEY"])
    except Exception:  # noqa: BLE001 - no secrets.toml configured
        pass
    return os.environ.get("ANTHROPIC_API_KEY")


def prepare_uploaded_customers(uploaded: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    uploaded = uploaded.copy()
    missing = sorted(UPLOAD_REQUIRED_COLUMNS - set(uploaded.columns))
    if missing:
        return uploaded, missing

    numeric_defaults = {
        "monetary": 0,
        "frequency": 0,
        "recency_days": 999,
        "repeat_purchase_probability": 0,
        "repeat_purchase_60d": 0,
        "campaign_converted_30d": 0,
        "avg_order_value": 0,
    }
    text_defaults = {
        "region": "Unknown",
        "acquisition_channel": "Unknown",
    }
    for column, default in numeric_defaults.items():
        if column not in uploaded.columns:
            uploaded[column] = default
        uploaded[column] = pd.to_numeric(uploaded[column], errors="coerce").fillna(default)
    for column, default in text_defaults.items():
        if column not in uploaded.columns:
            uploaded[column] = default
        uploaded[column] = uploaded[column].fillna(default)

    needs_aov = uploaded["avg_order_value"].eq(0) & uploaded["frequency"].gt(0)
    uploaded.loc[needs_aov, "avg_order_value"] = (
        uploaded.loc[needs_aov, "monetary"] / uploaded.loc[needs_aov, "frequency"]
    )
    return uploaded, []


def summarize_dashboard_segments(customers: pd.DataFrame) -> pd.DataFrame:
    summary = (
        customers.groupby("segment")
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


# --- Styling ---------------------------------------------------------------

st.markdown(
    """
    <style>
      @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

      html, body, [class*="css"], .stMarkdown, .stApp {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
      }

      /* Entrance animation */
      @keyframes fadeUp { from { opacity: 0; transform: translateY(14px); } to { opacity: 1; transform: none; } }
      @keyframes fade { from { opacity: 0; } to { opacity: 1; } }
      @keyframes sweepIn { from { transform: scaleX(0); } to { transform: scaleX(1); } }
      @media (prefers-reduced-motion: reduce) {
        .block-container, .app-header, .decision-panel, .metric-card, .stApp::before { animation: none !important; }
      }

      .block-container {
        padding-top: 1.6rem; padding-bottom: 2.5rem; max-width: 1260px;
        animation: fadeUp 0.55s cubic-bezier(0.22, 0.61, 0.36, 1) both;
      }

      [data-testid="stMetric"] {
        border: 1px solid #e2e8f0; background: #ffffff; padding: 12px 14px;
        border-radius: 10px; box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
      }

      div[data-testid="stTabs"] [data-baseweb="tab-list"] { gap: 2px; border-bottom: 1px solid #e2e8f0; }
      div[data-testid="stTabs"] button { font-size: 0.9rem; font-weight: 600; color: #64748b; padding: 8px 14px; }
      div[data-testid="stTabs"] button[aria-selected="true"] { color: #0f766e; }
      div[data-testid="stTabs"] [data-baseweb="tab-highlight"] { background-color: #0f766e; }
      div[data-testid="stTabs"] [data-baseweb="tab-panel"] { padding-top: 14px; }

      .stApp::before {
        content: ""; position: fixed; top: 0; left: 0; right: 0; height: 3px;
        background: linear-gradient(90deg, #0f766e 0%, #14b8a6 50%, #2563eb 100%); z-index: 1000;
        transform-origin: left; animation: sweepIn 0.85s cubic-bezier(0.22, 0.61, 0.36, 1) both;
      }

      [data-testid="stMarkdownContainer"] h4 {
        font-size: 0.96rem; font-weight: 700; color: #0f172a; margin: 8px 0 10px 0;
        padding-left: 11px; border-left: 3px solid #0f766e; line-height: 1.2;
      }

      .app-header {
        position: relative; padding: 4px 0 18px 0; margin-bottom: 18px; border-bottom: 1px solid #e2e8f0;
        animation: fade 0.8s ease both;
      }
      .app-header-row { display: flex; align-items: center; gap: 16px; }
      .brand-mark {
        flex: 0 0 auto; width: 46px; height: 46px; border-radius: 12px;
        background: linear-gradient(135deg, #0f766e 0%, #14b8a6 100%);
        box-shadow: 0 6px 16px rgba(15, 118, 110, 0.28);
        display: flex; align-items: center; justify-content: center;
        color: #ffffff; font-size: 1.35rem; font-weight: 800;
      }
      .eyebrow {
        display: inline-block; color: #0f766e; background: #e6f4f1; font-size: 0.72rem;
        text-transform: uppercase; letter-spacing: 0.04em; font-weight: 700;
        padding: 3px 10px; border-radius: 999px; margin-bottom: 8px;
      }
      .app-title {
        color: #0f172a; font-size: 1.95rem; line-height: 1.12; font-weight: 800;
        letter-spacing: -0.02em; margin: 0;
      }
      .header-meta { margin-left: auto; display: flex; gap: 8px; align-items: center; }
      .meta-pill {
        display: inline-flex; align-items: center; gap: 6px; font-size: 0.78rem; font-weight: 600;
        color: #334155; background: #ffffff; border: 1px solid #e2e8f0; border-radius: 999px;
        padding: 5px 12px; box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04); white-space: nowrap;
      }
      .meta-dot { width: 8px; height: 8px; border-radius: 50%; background: #059669; box-shadow: 0 0 0 3px rgba(5,150,105,0.15); }
      .app-subtitle { color: #475569; font-size: 0.98rem; line-height: 1.5; margin-top: 12px; max-width: 940px; }
      .app-footer {
        margin-top: 28px; padding-top: 14px; border-top: 1px solid #e7ebf2;
        color: #94a3b8; font-size: 0.8rem; display: flex; justify-content: space-between; flex-wrap: wrap; gap: 8px;
      }

      .decision-panel {
        border: 1px solid #e2e8f0; background: linear-gradient(135deg, #f0faf8 0%, #ffffff 60%);
        border-left: 5px solid #0f766e; border-radius: 12px; padding: 18px 20px; margin: 8px 0 18px 0;
        box-shadow: 0 4px 14px rgba(15, 118, 110, 0.06);
        animation: fadeUp 0.6s cubic-bezier(0.22, 0.61, 0.36, 1) both; animation-delay: 0.08s;
      }
      .decision-kicker {
        color: #0f766e; text-transform: uppercase; font-size: 0.74rem; letter-spacing: 0.04em;
        font-weight: 800; margin-bottom: 4px;
      }
      .decision-title { color: #0f172a; font-size: 1.24rem; font-weight: 800; line-height: 1.25; }
      .decision-body { color: #334155; margin-top: 8px; line-height: 1.5; }
      .decision-chips { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 14px; }
      .decision-chips span {
        border: 1px solid #dfe7e6; background: #ffffff; color: #334155; padding: 5px 11px;
        border-radius: 999px; font-size: 0.82rem; font-weight: 600; box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
      }

      .metric-card {
        border: 1px solid #e7ebf2; background: #ffffff; border-radius: 12px; padding: 15px 16px 14px 16px;
        min-height: 112px; box-shadow: 0 1px 3px rgba(15, 23, 42, 0.05);
        transition: transform 0.12s ease, box-shadow 0.12s ease;
        animation: fadeUp 0.55s cubic-bezier(0.22, 0.61, 0.36, 1) both; animation-delay: 0.12s;
      }
      .metric-card:hover { transform: translateY(-2px); box-shadow: 0 8px 20px rgba(15, 23, 42, 0.08); }
      .metric-card.positive { border-top: 3px solid #059669; }
      .metric-card.caution  { border-top: 3px solid #d97706; }
      .metric-card.neutral  { border-top: 3px solid #0f766e; }
      .metric-label { color: #64748b; font-size: 0.74rem; font-weight: 700; letter-spacing: 0.03em; text-transform: uppercase; }
      .metric-value { color: #0f172a; font-size: 1.6rem; font-weight: 800; line-height: 1.15; letter-spacing: -0.01em; margin-top: 6px; }
      .metric-detail { color: #64748b; font-size: 0.83rem; line-height: 1.35; margin-top: 8px; }

      section[data-testid="stSidebar"] { border-right: 1px solid #e7ebf2; }
      .sidebar-brand { padding: 2px 0 12px 0; margin-bottom: 8px; border-bottom: 1px solid #e7ebf2; }
      .sidebar-brand-title { font-size: 1.05rem; font-weight: 800; color: #0f172a; line-height: 1.2; }
      .sidebar-brand-sub { font-size: 0.8rem; color: #64748b; margin-top: 2px; }
      .sidebar-section {
        font-size: 0.72rem; font-weight: 700; letter-spacing: 0.06em; text-transform: uppercase;
        color: #94a3b8; margin: 16px 0 8px 0;
      }
      .stat-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
      .stat-cell {
        display: flex; flex-direction: column; border: 1px solid #e7ebf2; border-radius: 10px;
        padding: 9px 11px; background: #fbfdfd;
      }
      .stat-num { font-size: 1.1rem; font-weight: 800; color: #0f172a; line-height: 1.1; }
      .stat-cap { font-size: 0.72rem; color: #64748b; margin-top: 3px; }

      .method-chip {
        border: 1px solid #e2e8f0; border-radius: 8px; padding: 8px 11px; background: #ffffff;
        color: #334155; font-size: 0.85rem; font-weight: 500; margin-bottom: 8px;
        box-shadow: 0 1px 2px rgba(15, 23, 42, 0.03);
      }

      [data-testid="stDataFrame"] {
        border: 1px solid #e7ebf2; border-radius: 10px; overflow: hidden; box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
      }
    </style>
    """,
    unsafe_allow_html=True,
)


# --- Personal flair: paintbrush cursor + ink-wash (水墨) splash on click -------
# Injected via a 0-height component whose script reaches into the parent page
# (same origin) to set a custom cursor and spawn ink blots on every click.
BRUSH_FLAIR = """
<script>
(function () {
  let win, doc;
  try { win = window.parent; doc = win.document; } catch (e) { return; }
  if (win.__brushFlair) return;          // guard against re-injection on rerun
  win.__brushFlair = true;

  const brush =
    '<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 32 32">'
    + '<rect x="13" y="2" width="6" height="15" rx="3" fill="#a9743f"/>'
    + '<rect x="12.4" y="15.4" width="7.2" height="3.6" rx="1.4" fill="#cbd5e1"/>'
    + '<path d="M12.5 19 H19.5 L17.8 29 Q16 31.6 14.2 29 Z" fill="#1f2937"/>'
    + '</svg>';
  const cur = 'url("data:image/svg+xml;base64,' + win.btoa(brush) + '") 16 30, auto';

  // A global cursor rule. Streamlit re-injects Emotion styles on every rerun,
  // so we keep this <style> last in <head> (MutationObserver) and also set the
  // cursor inline on the root element, to win the cascade everywhere.
  const style = doc.createElement('style');
  style.id = '__brushFlairStyle';
  style.textContent =
    'html, body, *, *::before, *::after { cursor: ' + cur + ' !important; }' +
    'input, textarea, [contenteditable="true"], [role="textbox"] { cursor: text !important; }' +
    '@keyframes inkSplash{0%{transform:scale(.15);opacity:0}15%{opacity:.65}100%{transform:scale(1.6);opacity:0}}';
  doc.head.appendChild(style);
  doc.documentElement.style.setProperty('cursor', cur, 'important');

  const keepLast = () => {
    if (doc.head.lastElementChild !== style) doc.head.appendChild(style);
  };
  try { new win.MutationObserver(keepLast).observe(doc.head, { childList: true }); } catch (e) {}

  const rr = () => (40 + Math.random() * 20).toFixed(0);
  const shape = () =>
    rr()+'% '+rr()+'% '+rr()+'% '+rr()+'% / '+rr()+'% '+rr()+'% '+rr()+'% '+rr()+'%';

  doc.addEventListener('click', function (e) {
    const n = 5 + Math.floor(Math.random() * 3);
    for (let i = 0; i < n; i++) {
      const main = i === 0;
      const size = main ? 44 : 8 + Math.random() * 16;
      const ang = Math.random() * Math.PI * 2;
      const dist = main ? 0 : 8 + Math.random() * 26;
      const dx = Math.cos(ang) * dist, dy = Math.sin(ang) * dist;
      const blot = doc.createElement('div');
      blot.style.cssText =
        'position:fixed;z-index:99999;pointer-events:none;left:' + e.clientX + 'px;top:' + e.clientY + 'px;' +
        'width:' + size + 'px;height:' + size + 'px;margin-left:' + (-size/2+dx) + 'px;margin-top:' + (-size/2+dy) + 'px;' +
        'border-radius:' + shape() + ';filter:blur(1.4px);' +
        'background:radial-gradient(circle at 42% 38%, rgba(17,24,39,.62), rgba(31,41,55,.28) 55%, rgba(31,41,55,0) 72%);' +
        'animation:inkSplash ' + (700 + Math.random() * 350).toFixed(0) + 'ms cubic-bezier(.22,.61,.36,1) forwards;';
      doc.body.appendChild(blot);
      setTimeout(function () { blot.remove(); }, 1150);
    }
  }, true);
})();
</script>
"""
components.html(BRUSH_FLAIR, height=0)


with st.spinner("Preparing customer intelligence outputs..."):
    ensure_pipeline_outputs()

customers, segment_summary, metrics, sql_outputs, feature_importance, experiment_summary, segment_lift = load_outputs()

_auc_display = f"{metrics.get('roc_auc', 0):.3f}" if metrics else "—"
st.markdown(
    f"""
    <div class="app-header">
      <div class="app-header-row">
        <div class="brand-mark">CI</div>
        <div>
          <div class="eyebrow">Customer Analytics Workspace</div>
          <h1 class="app-title">Customer Intelligence &amp; Campaign ROI Platform</h1>
        </div>
        <div class="header-meta">
          <span class="meta-pill"><span class="meta-dot"></span>Live demo</span>
          <span class="meta-pill">Model AUC {_auc_display}</span>
        </div>
      </div>
      <div class="app-subtitle">
        Segment customers, predict 60-day repeat purchase, and size campaign lift and ROI against a holdout group.
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

if customers.empty:
    st.info("Run `python scripts/generate_data.py` and `python scripts/train_models.py` first.")
    st.stop()

with st.sidebar:
    st.markdown(
        """
        <div class="sidebar-brand">
          <div class="sidebar-brand-title">Customer Intelligence</div>
          <div class="sidebar-brand-sub">Retention & campaign ROI workspace</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown('<div class="sidebar-section">Dataset</div>', unsafe_allow_html=True)
    total_revenue_side = customers["monetary"].sum()
    st.markdown(
        f"""
        <div class="stat-grid">
          <div class="stat-cell"><span class="stat-num">{len(customers):,}</span><span class="stat-cap">Customers</span></div>
          <div class="stat-cell"><span class="stat-num">${total_revenue_side / 1000:,.0f}K</span><span class="stat-cap">Revenue</span></div>
          <div class="stat-cell"><span class="stat-num">{customers["repeat_purchase_60d"].mean():.0%}</span><span class="stat-cap">Repeat rate</span></div>
          <div class="stat-cell"><span class="stat-num">{metrics.get("roc_auc", 0):.3f}</span><span class="stat-cap">Model AUC</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown('<div class="sidebar-section">Methods</div>', unsafe_allow_html=True)
    for method in ["RFM segmentation (K-means)", "Repeat-purchase models", "Holdout campaign lift", "ROI estimation"]:
        st.markdown(f'<div class="method-chip">{method}</div>', unsafe_allow_html=True)

with st.expander("Import customer CSV"):
    st.caption(
        "Upload a customer-level CSV with columns such as customer_id, segment, monetary, "
        "frequency, recency_days, repeat_purchase_probability, and recommended_action."
    )
    uploaded_file = st.file_uploader("Upload CSV", type=["csv"])
    if uploaded_file is not None:
        try:
            uploaded_customers = pd.read_csv(uploaded_file)
            uploaded_customers, missing_columns = prepare_uploaded_customers(uploaded_customers)
            if missing_columns:
                st.error("Missing columns: " + ", ".join(missing_columns))
                st.caption("Using the generated demo dataset until the uploaded CSV matches the required schema.")
            else:
                customers = uploaded_customers
                segment_summary = summarize_dashboard_segments(customers)
                st.success(f"Using uploaded dataset: {len(customers):,} customers")
        except Exception as exc:
            st.error(f"Could not read CSV: {exc}")
    else:
        st.caption("Currently using the generated demo dataset.")

top_segment = segment_summary.sort_values("avg_monetary", ascending=False).iloc[0]
top_segment_display = str(top_segment["segment"]).replace("High-value loyalists", "High-value")
offer_candidates = customers[customers["recommended_action"] == "Send targeted offer"]
experiment = experiment_summary.iloc[0] if not experiment_summary.empty else None
lift = experiment["absolute_lift"] if experiment is not None else 0
roi = experiment["roi"] if experiment is not None else 0

decision_panel(
    f"Prioritize {top_segment['segment']} for retention; send targeted offers to mid-probability customers.",
    (
        f"The campaign experiment estimates {lift:.1%} absolute lift over the holdout group, so the recommended "
        f"plan is to launch with a holdout and monitor 60-day repeat purchase. Reserve discounts for the "
        f"{len(offer_candidates):,} mid-probability customers rather than likely repeat buyers."
    ),
    [
        f"Top segment {top_segment_display}",
        f"{len(offer_candidates):,} offer candidates",
        f"Lift {lift:.1%}",
        f"ROI {roi:.1%}",
    ],
)

k1, k2, k3, k4 = st.columns(4)
with k1:
    metric_card("Recommended Segment", top_segment_display, "Highest average value", "neutral")
with k2:
    metric_card("Offer Candidates", f"{len(offer_candidates):,}", "Mid-probability customers", "neutral")
with k3:
    metric_card("Campaign Lift", f"{lift:.1%}", "Targeted vs holdout", "positive")
with k4:
    metric_card("Projected ROI", f"{roi:.1%}", "Net profit over cost", "positive")

if experiment is not None:
    left, right = st.columns([1, 1])
    with left:
        st.markdown("#### Expected Business Impact")
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
        st.markdown("#### Decision Guardrails")
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

tabs = st.tabs(["Overview", "Segments", "Prediction", "Experiment", "SQL Insights", "Analyst Assistant"])

with tabs[0]:
    total_revenue = customers["monetary"].sum()
    repeat_rate = customers["repeat_purchase_60d"].mean()
    avg_probability = customers["repeat_purchase_probability"].mean()

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        metric_card("Customers", f"{len(customers):,}", "In the analysis", "neutral")
    with c2:
        metric_card("Historical Revenue", f"${total_revenue:,.0f}", "Pre-cutoff orders", "neutral")
    with c3:
        metric_card("60-Day Repeat Rate", f"{repeat_rate:.1%}", "Observed label", "positive")
    with c4:
        metric_card("Avg Predicted Repeat", f"{avg_probability:.1%}", "Model score", "neutral")

    left, right = st.columns([1.1, 1])
    with left:
        st.markdown("#### Revenue by Segment")
        st.altair_chart(revenue_by_segment_chart(customers))
    with right:
        st.markdown("#### Recommended Marketing Actions")
        st.altair_chart(actions_chart(customers))

with tabs[1]:
    st.markdown("#### Segment Performance")
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

    st.markdown("#### RFM Segment Map")
    st.altair_chart(rfm_scatter_chart(customers))

with tabs[2]:
    st.caption(f"Best model: {metrics.get('best_model', 'selected model')}")
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        metric_card("ROC AUC", f"{metrics['roc_auc']:.3f}", "Ranking quality", "neutral")
    with c2:
        metric_card("Precision", f"{metrics['precision']:.3f}", "Positive predictive value", "neutral")
    with c3:
        metric_card("Recall", f"{metrics['recall']:.3f}", "Coverage of repeaters", "neutral")
    with c4:
        metric_card("F1", f"{metrics['f1']:.3f}", "Balance of the two", "neutral")
    with c5:
        metric_card("Positive Rate", f"{metrics['positive_rate']:.1%}", "Base repeat rate", "caution")

    if "candidate_models" in metrics:
        st.markdown("#### Model Comparison")
        st.altair_chart(model_comparison_chart(pd.DataFrame(metrics["candidate_models"])))

    if not feature_importance.empty:
        st.markdown("#### Top Model Drivers")
        st.altair_chart(importance_chart(feature_importance))

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
        customers["segment"].isin(segment_filter) & customers["recommended_action"].isin(action_filter)
    ].sort_values("repeat_purchase_probability", ascending=False)

    st.markdown("#### Customer Scores")
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
    if experiment_summary.empty:
        st.info("Run `python scripts/run_sql_analysis.py` to build experiment outputs.")
    else:
        experiment = experiment_summary.iloc[0]
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            metric_card(
                "Targeted Conversion", f"{experiment['targeted_conversion_rate']:.1%}", "Treatment group", "neutral"
            )
        with c2:
            metric_card(
                "Holdout Conversion", f"{experiment['holdout_conversion_rate']:.1%}", "Control group", "neutral"
            )
        with c3:
            metric_card("Absolute Lift", f"{experiment['absolute_lift']:.1%}", "Treatment minus control", "positive")
        with c4:
            metric_card("P-value", f"{experiment['p_value']:.4f}", "Two-proportion test", "neutral")

        st.caption(
            f"95% confidence interval for lift: {experiment['lift_ci_low']:.1%} to "
            f"{experiment['lift_ci_high']:.1%}. ROI uses a {experiment['assumed_margin_rate']:.0%} gross margin "
            f"assumption and ${experiment['offer_cost_per_customer']:.0f} cost per targeted customer."
        )

        left, right = st.columns([1, 1])
        with left:
            st.markdown("#### Conversion by Group")
            st.altair_chart(conversion_chart(experiment))
        with right:
            st.markdown("#### ROI Breakdown")
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
            st.markdown("#### Lift by Segment")
            st.altair_chart(segment_lift_chart(segment_lift))

with tabs[4]:
    if not sql_outputs:
        st.info("Run `python scripts/run_sql_analysis.py` to build SQL analysis outputs.")
    else:
        if "sql_campaign_lift" in sql_outputs:
            sql_lift = sql_outputs["sql_campaign_lift"].iloc[0]
            c1, c2, c3 = st.columns(3)
            with c1:
                metric_card(
                    "Targeted Conversion", f"{sql_lift['targeted_conversion_rate']:.1%}", "DuckDB query", "neutral"
                )
            with c2:
                metric_card(
                    "Holdout Conversion", f"{sql_lift['holdout_conversion_rate']:.1%}", "DuckDB query", "neutral"
                )
            with c3:
                metric_card("Relative Lift", f"{sql_lift['relative_lift']:.1%}", "Targeted vs holdout", "positive")

        for label, key in [
            ("Segment Performance", "sql_segment_performance"),
            ("Acquisition Channel Cohorts", "sql_channel_cohorts"),
            ("Lifecycle Stages", "sql_lifecycle_stages"),
            ("Campaign Lift", "sql_campaign_lift"),
        ]:
            if key in sql_outputs:
                st.markdown(f"#### {label}")
                st.dataframe(sql_outputs[key], use_container_width=True, hide_index=True)

with tabs[5]:
    context = build_insight_context(customers, segment_summary, metrics)
    examples = [
        "Which segment should marketing target next?",
        "Which customers are at churn risk?",
        "How good is the prediction model?",
        "Which segment is most valuable?",
    ]

    api_key = get_anthropic_key()
    use_llm = llm.llm_available(api_key)
    if use_llm:
        model_label = st.selectbox("Model", list(llm.MODELS))
        model_id = llm.MODELS[model_label]
        st.caption(f"Grounded answers generated by Claude ({model_id}) over this project's computed metrics.")
    else:
        st.caption(
            "Rule-based assistant. Set an `ANTHROPIC_API_KEY` (env var or Streamlit secret) "
            "to enable grounded answers from Claude."
        )

    question = st.selectbox("Ask a business question", examples)
    custom_question = st.text_input("Or type your own question")
    final_question = custom_question or question

    st.markdown("#### Answer")
    if use_llm:
        try:
            with st.spinner("Asking Claude..."):
                st.write(llm.answer_with_llm(final_question, context, api_key=api_key, model=model_id))
        except Exception as exc:  # noqa: BLE001 - fall back to the rule-based answer
            st.warning(f"Claude request failed ({exc}); showing the rule-based answer instead.")
            st.write(answer_question(final_question, context))
    else:
        st.write(answer_question(final_question, context))

st.markdown(
    """
    <div class="app-footer">
      <span>Synthetic demonstration data &middot; figures are illustrative.</span>
      <span>Built with Python &middot; DuckDB &middot; scikit-learn &middot; Streamlit &middot; Claude</span>
    </div>
    """,
    unsafe_allow_html=True,
)
