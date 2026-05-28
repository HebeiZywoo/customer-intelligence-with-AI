from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


SEGMENT_FEATURES = ["recency_days", "frequency", "monetary", "avg_order_value"]
PREDICTION_NUMERIC_FEATURES = [
    "age",
    "frequency",
    "monetary",
    "avg_order_value",
    "total_quantity",
    "avg_discount",
    "unique_categories",
    "campaign_targeted",
    "campaign_converted_30d",
    "recency_days",
    "days_since_signup",
    "orders_per_100_days",
    "monetary_per_100_days",
    "discounted_revenue",
    "email_engagement_score",
    "loyalty_score",
    "preference_match",
    "is_new_customer",
]
PREDICTION_CATEGORICAL_FEATURES = [
    "acquisition_channel",
    "region",
    "preferred_category",
    "top_category",
    "segment",
]


@dataclass
class TrainingResult:
    features: pd.DataFrame
    segmentation_model: Pipeline
    repeat_purchase_model: Pipeline
    metrics: dict


def add_segments(features: pd.DataFrame, n_segments: int = 4) -> tuple[pd.DataFrame, Pipeline]:
    model = Pipeline(
        steps=[
            ("scale", StandardScaler()),
            ("cluster", KMeans(n_clusters=n_segments, random_state=42, n_init=20)),
        ]
    )
    segment_input = features[SEGMENT_FEATURES].copy()
    labels = model.fit_predict(segment_input)

    output = features.copy()
    output["segment_id"] = labels
    output["segment"] = _name_segments(output)
    return output, model


def train_repeat_purchase_model(features: pd.DataFrame) -> tuple[Pipeline, dict]:
    x = features[PREDICTION_NUMERIC_FEATURES + PREDICTION_CATEGORICAL_FEATURES]
    y = features["repeat_purchase_60d"]

    x_train, x_test, y_train, y_test = train_test_split(
        x, y, test_size=0.25, random_state=42, stratify=y
    )

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), PREDICTION_NUMERIC_FEATURES),
            (
                "cat",
                OneHotEncoder(handle_unknown="ignore", sparse_output=False),
                PREDICTION_CATEGORICAL_FEATURES,
            ),
        ]
    )
    candidates = {
        "logistic_regression": LogisticRegression(max_iter=1200, class_weight="balanced", random_state=42),
        "random_forest": RandomForestClassifier(
            n_estimators=320,
            max_depth=9,
            min_samples_leaf=6,
            class_weight="balanced_subsample",
            random_state=42,
        ),
        "gradient_boosting": GradientBoostingClassifier(
            n_estimators=220,
            learning_rate=0.045,
            max_depth=3,
            random_state=42,
        ),
    }

    model_results = []
    fitted_models = {}
    for name, classifier in candidates.items():
        model = Pipeline(steps=[("preprocess", preprocessor), ("classifier", classifier)])
        model.fit(x_train, y_train)
        probabilities = model.predict_proba(x_test)[:, 1]
        predictions = (probabilities >= 0.5).astype(int)
        result = _classification_metrics(y_test, predictions, probabilities)
        result["model_name"] = name
        model_results.append(result)
        fitted_models[name] = model

    best_result = sorted(model_results, key=lambda item: item["roc_auc"], reverse=True)[0]
    best_model = fitted_models[best_result["model_name"]]
    metrics = {
        **best_result,
        "best_model": best_result["model_name"],
        "positive_rate": round(float(np.mean(y)), 4),
        "test_rows": int(len(y_test)),
        "candidate_models": model_results,
    }
    return best_model, metrics


def score_customers(features: pd.DataFrame, model: Pipeline) -> pd.DataFrame:
    scored = features.copy()
    x = scored[PREDICTION_NUMERIC_FEATURES + PREDICTION_CATEGORICAL_FEATURES]
    scored["repeat_purchase_probability"] = model.predict_proba(x)[:, 1]
    scored["recommended_action"] = np.select(
        [
            scored["repeat_purchase_probability"] >= 0.55,
            scored["repeat_purchase_probability"] >= 0.30,
        ],
        ["Nurture loyalty", "Send targeted offer"],
        default="Win-back campaign",
    )
    return scored


def extract_feature_importance(model: Pipeline, top_n: int = 30) -> pd.DataFrame:
    preprocessor = model.named_steps["preprocess"]
    classifier = model.named_steps["classifier"]
    feature_names = preprocessor.get_feature_names_out()
    clean_names = [_clean_feature_name(name) for name in feature_names]

    if hasattr(classifier, "feature_importances_"):
        raw_importance = classifier.feature_importances_
        signed_weight = raw_importance
        importance_type = "tree_importance"
    elif hasattr(classifier, "coef_"):
        signed_weight = classifier.coef_[0]
        raw_importance = np.abs(signed_weight)
        importance_type = "absolute_coefficient"
    else:
        raw_importance = np.zeros(len(clean_names))
        signed_weight = raw_importance
        importance_type = "unknown"

    importance = pd.DataFrame(
        {
            "feature": clean_names,
            "importance": raw_importance,
            "signed_weight": signed_weight,
            "importance_type": importance_type,
        }
    )
    total = importance["importance"].sum()
    if total > 0:
        importance["normalized_importance"] = importance["importance"] / total
    else:
        importance["normalized_importance"] = 0
    return importance.sort_values("importance", ascending=False).head(top_n).reset_index(drop=True)


def _classification_metrics(y_true: pd.Series, predictions: np.ndarray, probabilities: np.ndarray) -> dict:
    return {
        "accuracy": round(float(accuracy_score(y_true, predictions)), 4),
        "precision": round(float(precision_score(y_true, predictions, zero_division=0)), 4),
        "recall": round(float(recall_score(y_true, predictions, zero_division=0)), 4),
        "f1": round(float(f1_score(y_true, predictions, zero_division=0)), 4),
        "roc_auc": round(float(roc_auc_score(y_true, probabilities)), 4),
    }


def _clean_feature_name(name: str) -> str:
    return (
        name.replace("num__", "")
        .replace("cat__", "")
        .replace("acquisition_channel_", "channel: ")
        .replace("region_", "region: ")
        .replace("preferred_category_", "preferred: ")
        .replace("top_category_", "top category: ")
        .replace("segment_", "segment: ")
    )


def _name_segments(features: pd.DataFrame) -> pd.Series:
    stats = (
        features.groupby("segment_id")
        .agg(
            monetary=("monetary", "mean"),
            frequency=("frequency", "mean"),
            recency_days=("recency_days", "mean"),
        )
        .reset_index()
    )

    high_value = stats.sort_values("monetary", ascending=False).iloc[0]["segment_id"]
    newest = stats.sort_values("recency_days", ascending=False).iloc[0]["segment_id"]
    loyal = stats.sort_values("frequency", ascending=False).iloc[0]["segment_id"]

    names = {}
    for row in stats.itertuples(index=False):
        if row.segment_id == high_value:
            names[row.segment_id] = "High-value loyalists"
        elif row.segment_id == loyal:
            names[row.segment_id] = "Frequent shoppers"
        elif row.segment_id == newest:
            names[row.segment_id] = "At-risk or dormant"
        else:
            names[row.segment_id] = "Emerging customers"

    return features["segment_id"].map(names)
