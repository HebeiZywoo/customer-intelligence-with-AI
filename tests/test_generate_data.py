from __future__ import annotations

import numpy as np
import pandas as pd

from scripts.generate_data import (
    make_campaign_events,
    make_customers,
    make_products,
    make_transactions,
)


def test_customer_schema_and_count(raw_data: dict[str, pd.DataFrame]) -> None:
    customers = raw_data["customers"]
    assert len(customers) == 600
    assert customers["customer_id"].is_unique
    assert {"signup_date", "acquisition_channel", "region", "age", "preferred_category"}.issubset(customers.columns)


def test_transactions_are_well_formed(raw_data: dict[str, pd.DataFrame]) -> None:
    transactions = raw_data["transactions"]
    assert (transactions["revenue"] > 0).all()
    assert (transactions["quantity"] >= 1).all()
    assert transactions["customer_id"].isin(raw_data["customers"]["customer_id"]).all()


def test_campaign_groups(raw_data: dict[str, pd.DataFrame]) -> None:
    campaign = raw_data["campaign_events"]
    assert set(campaign["treatment_group"].unique()).issubset({"Targeted", "Holdout"})
    assert set(campaign["converted_30d"].unique()).issubset({0, 1})


def test_generation_is_deterministic() -> None:
    def build() -> dict[str, pd.DataFrame]:
        rng = np.random.default_rng(42)
        customers = make_customers(rng, n_customers=200)
        products = make_products(rng, n_products=20)
        transactions = make_transactions(rng, customers, products)
        campaign = make_campaign_events(rng, customers, transactions)
        return {"customers": customers, "transactions": transactions, "campaign": campaign}

    first, second = build(), build()
    for key in first:
        pd.testing.assert_frame_equal(first[key], second[key])
