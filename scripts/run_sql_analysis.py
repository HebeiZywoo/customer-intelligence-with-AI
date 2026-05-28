import sys
from pathlib import Path

import duckdb
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.customer_ai.experiments import build_campaign_experiment_outputs

RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"
ANALYTICS_DIR = ROOT / "analytics"
DB_PATH = ANALYTICS_DIR / "customer_intelligence.duckdb"


QUERIES = {
    "sql_segment_performance.csv": """
        SELECT
            segment,
            COUNT(*) AS customers,
            ROUND(SUM(monetary), 2) AS revenue,
            ROUND(AVG(monetary), 2) AS avg_customer_value,
            ROUND(AVG(frequency), 2) AS avg_orders,
            ROUND(AVG(repeat_purchase_probability), 4) AS avg_predicted_repeat,
            ROUND(AVG(repeat_purchase_60d), 4) AS actual_repeat_rate
        FROM customer_features
        GROUP BY segment
        ORDER BY revenue DESC
    """,
    "sql_campaign_lift.csv": """
        WITH rates AS (
            SELECT
                treatment_group,
                COUNT(*) AS customers,
                AVG(converted_30d) AS conversion_rate
            FROM campaign_events
            GROUP BY treatment_group
        ),
        pivoted AS (
            SELECT
                MAX(CASE WHEN treatment_group = 'Targeted' THEN conversion_rate END) AS targeted_rate,
                MAX(CASE WHEN treatment_group = 'Holdout' THEN conversion_rate END) AS holdout_rate,
                MAX(CASE WHEN treatment_group = 'Targeted' THEN customers END) AS targeted_customers,
                MAX(CASE WHEN treatment_group = 'Holdout' THEN customers END) AS holdout_customers
            FROM rates
        )
        SELECT
            targeted_customers,
            holdout_customers,
            ROUND(targeted_rate, 4) AS targeted_conversion_rate,
            ROUND(holdout_rate, 4) AS holdout_conversion_rate,
            ROUND(targeted_rate - holdout_rate, 4) AS absolute_lift,
            ROUND((targeted_rate - holdout_rate) / NULLIF(holdout_rate, 0), 4) AS relative_lift
        FROM pivoted
    """,
    "sql_channel_cohorts.csv": """
        SELECT
            acquisition_channel,
            COUNT(*) AS customers,
            ROUND(AVG(monetary), 2) AS avg_customer_value,
            ROUND(AVG(frequency), 2) AS avg_orders,
            ROUND(AVG(repeat_purchase_probability), 4) AS avg_predicted_repeat,
            ROUND(AVG(email_engagement_score), 3) AS avg_email_engagement
        FROM customer_features
        GROUP BY acquisition_channel
        ORDER BY avg_customer_value DESC
    """,
    "sql_lifecycle_stages.csv": """
        SELECT
            CASE
                WHEN recency_days <= 60 AND frequency >= 4 THEN 'Active repeat buyers'
                WHEN recency_days <= 60 THEN 'Recently active'
                WHEN recency_days BETWEEN 61 AND 180 THEN 'Cooling down'
                ELSE 'Dormant'
            END AS lifecycle_stage,
            COUNT(*) AS customers,
            ROUND(AVG(monetary), 2) AS avg_customer_value,
            ROUND(AVG(repeat_purchase_probability), 4) AS avg_predicted_repeat
        FROM customer_features
        GROUP BY lifecycle_stage
        ORDER BY customers DESC
    """,
}


def register_tables(con: duckdb.DuckDBPyConnection) -> None:
    tables = {
        "customers": RAW_DIR / "customers.csv",
        "products": RAW_DIR / "products.csv",
        "transactions": RAW_DIR / "transactions.csv",
        "campaign_events": RAW_DIR / "campaign_events.csv",
        "customer_features": PROCESSED_DIR / "customer_features.csv",
        "segment_summary": PROCESSED_DIR / "segment_summary.csv",
    }
    for table, path in tables.items():
        con.execute(f"CREATE OR REPLACE TABLE {table} AS SELECT * FROM read_csv_auto(?)", [str(path)])


def main() -> None:
    ANALYTICS_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    with duckdb.connect(DB_PATH) as con:
        register_tables(con)
        for filename, query in QUERIES.items():
            output_path = PROCESSED_DIR / filename
            con.execute(f"COPY ({query}) TO ? (HEADER, DELIMITER ',')", [str(output_path)])

    campaign_events = pd.read_csv(RAW_DIR / "campaign_events.csv")
    customer_features = pd.read_csv(PROCESSED_DIR / "customer_features.csv")
    experiment_summary, segment_lift = build_campaign_experiment_outputs(
        campaign_events, customer_features
    )
    experiment_summary.to_csv(PROCESSED_DIR / "campaign_experiment_summary.csv", index=False)
    segment_lift.to_csv(PROCESSED_DIR / "campaign_segment_lift.csv", index=False)

    print(f"Built DuckDB database: {DB_PATH}")
    for filename in QUERIES:
        print(f"Wrote {PROCESSED_DIR / filename}")
    print(f"Wrote {PROCESSED_DIR / 'campaign_experiment_summary.csv'}")
    print(f"Wrote {PROCESSED_DIR / 'campaign_segment_lift.csv'}")


if __name__ == "__main__":
    main()
