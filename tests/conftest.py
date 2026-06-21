"""Shared fixtures.

Tests run against a small, fast synthetic dataset built once per session. The
production pipeline uses 1,800 customers; here we use a few hundred so the full
feature/segmentation/modeling stack runs in a couple of seconds while still
exercising the same code paths.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from scripts.generate_data import (
    make_campaign_events,
    make_customers,
    make_products,
    make_transactions,
)
from src.customer_ai.features import build_customer_features, summarize_segments
from src.customer_ai.modeling import add_segments, score_customers, train_repeat_purchase_model

N_CUSTOMERS = 600


@pytest.fixture(scope="session")
def raw_data() -> dict[str, pd.DataFrame]:
    rng = np.random.default_rng(42)
    customers = make_customers(rng, n_customers=N_CUSTOMERS)
    products = make_products(rng, n_products=40)
    transactions = make_transactions(rng, customers, products)
    campaign_events = make_campaign_events(rng, customers, transactions)
    return {
        "customers": customers,
        "products": products,
        "transactions": transactions,
        "campaign_events": campaign_events,
    }


@pytest.fixture(scope="session")
def features(raw_data: dict[str, pd.DataFrame]) -> pd.DataFrame:
    frame = build_customer_features(raw_data["customers"], raw_data["transactions"], raw_data["campaign_events"])
    frame, _ = add_segments(frame)
    return frame


@pytest.fixture(scope="session")
def trained(features: pd.DataFrame) -> dict:
    model, metrics = train_repeat_purchase_model(features)
    scored = score_customers(features, model)
    segment_summary = summarize_segments(scored)
    return {"model": model, "metrics": metrics, "scored": scored, "segment_summary": segment_summary}
