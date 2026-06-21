"""Full-scale regression test for the headline numbers quoted in the README.

Marked ``slow`` because it regenerates the production-sized dataset (1,800
customers) and trains the full model suite. Bands are wide enough to absorb
numpy / scikit-learn version drift while still guarding the documented claims:
ROC AUC ~0.709, campaign lift ~7.2pp, ROI ~115.7%.
"""

from __future__ import annotations

import numpy as np
import pytest

from scripts.generate_data import (
    make_campaign_events,
    make_customers,
    make_products,
    make_transactions,
)
from src.customer_ai.experiments import build_campaign_experiment_outputs
from src.customer_ai.features import build_customer_features
from src.customer_ai.modeling import add_segments, score_customers, train_repeat_purchase_model


@pytest.mark.slow
def test_full_scale_headline_metrics() -> None:
    rng = np.random.default_rng(42)
    customers = make_customers(rng)  # production default: 1,800
    products = make_products(rng)
    transactions = make_transactions(rng, customers, products)
    campaign_events = make_campaign_events(rng, customers, transactions)

    assert len(customers) == 1_800

    features = build_customer_features(customers, transactions, campaign_events)
    features, _ = add_segments(features)
    model, metrics = train_repeat_purchase_model(features)
    scored = score_customers(features, model)
    summary, _ = build_campaign_experiment_outputs(campaign_events, scored)
    row = summary.iloc[0]

    assert 0.66 <= metrics["roc_auc"] <= 0.75
    assert 0.05 <= row["absolute_lift"] <= 0.10
    assert 0.8 <= row["roi"] <= 1.5
    assert row["net_profit"] > 0
