"""Smoke test for the DuckDB SQL reporting layer.

Registers the in-memory fixtures as tables and runs the project queries, so a
broken query or a renamed column surfaces as a test failure.
"""

from __future__ import annotations

import duckdb
import pandas as pd

from scripts.run_sql_analysis import QUERIES


def test_sql_queries_run(trained: dict, raw_data: dict[str, pd.DataFrame]) -> None:
    customer_features = trained["scored"]
    campaign_events = raw_data["campaign_events"]
    con = duckdb.connect()
    try:
        con.register("customer_features", customer_features)
        con.register("campaign_events", campaign_events)
        for filename, query in QUERIES.items():
            rows = con.execute(query).fetchdf()
            assert not rows.empty, f"{filename} returned no rows"
    finally:
        con.close()
