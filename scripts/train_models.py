import json
import sys
from pathlib import Path

import joblib
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.customer_ai.features import build_customer_features, summarize_segments
from src.customer_ai.modeling import (
    add_segments,
    extract_feature_importance,
    score_customers,
    train_repeat_purchase_model,
)


RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"
MODEL_DIR = ROOT / "models"


def main() -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    customers = pd.read_csv(RAW_DIR / "customers.csv")
    transactions = pd.read_csv(RAW_DIR / "transactions.csv")
    campaign_events = pd.read_csv(RAW_DIR / "campaign_events.csv")

    features = build_customer_features(customers, transactions, campaign_events)
    features, segmentation_model = add_segments(features)
    repeat_purchase_model, metrics = train_repeat_purchase_model(features)
    scored = score_customers(features, repeat_purchase_model)
    segment_summary = summarize_segments(scored)
    feature_importance = extract_feature_importance(repeat_purchase_model)

    scored.to_csv(PROCESSED_DIR / "customer_features.csv", index=False)
    segment_summary.to_csv(PROCESSED_DIR / "segment_summary.csv", index=False)
    feature_importance.to_csv(PROCESSED_DIR / "feature_importance.csv", index=False)
    (PROCESSED_DIR / "model_metrics.json").write_text(json.dumps(metrics, indent=2))
    joblib.dump(segmentation_model, MODEL_DIR / "segmentation_model.joblib")
    joblib.dump(repeat_purchase_model, MODEL_DIR / "repeat_purchase_model.joblib")

    print("Training complete")
    print(json.dumps(metrics, indent=2))
    print(f"Saved {len(scored):,} customer rows")


if __name__ == "__main__":
    main()
