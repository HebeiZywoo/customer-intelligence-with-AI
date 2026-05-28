from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
RANDOM_SEED = 42


def make_customers(rng: np.random.Generator, n_customers: int = 1800) -> pd.DataFrame:
    acquisition_channels = ["Organic", "Paid Search", "Social", "Referral", "Email"]
    regions = ["West", "Northeast", "South", "Midwest"]
    preferred_categories = ["Home", "Beauty", "Electronics", "Fitness", "Apparel", "Kitchen"]
    channel_probs = [0.34, 0.22, 0.18, 0.16, 0.10]
    region_probs = [0.32, 0.23, 0.28, 0.17]

    signup_dates = pd.to_datetime(
        rng.integers(
            pd.Timestamp("2024-01-01").value // 10**9,
            pd.Timestamp("2025-11-30").value // 10**9,
            size=n_customers,
        ),
        unit="s",
    ).normalize()

    engagement_base = rng.beta(2.4, 3.0, n_customers)
    loyalty_base = rng.beta(2.0, 2.7, n_customers)
    customers = pd.DataFrame(
        {
            "customer_id": [f"C{i:05d}" for i in range(1, n_customers + 1)],
            "signup_date": signup_dates,
            "acquisition_channel": rng.choice(acquisition_channels, n_customers, p=channel_probs),
            "region": rng.choice(regions, n_customers, p=region_probs),
            "age": np.clip(rng.normal(37, 11, n_customers).round(), 18, 72).astype(int),
            "preferred_category": rng.choice(preferred_categories, n_customers),
            "email_engagement_score": np.round(engagement_base, 3),
            "loyalty_score": np.round(loyalty_base, 3),
        }
    )
    return customers.sort_values("signup_date").reset_index(drop=True)


def make_products(rng: np.random.Generator, n_products: int = 80) -> pd.DataFrame:
    categories = ["Home", "Beauty", "Electronics", "Fitness", "Apparel", "Kitchen"]
    category_base_price = {
        "Home": 45,
        "Beauty": 28,
        "Electronics": 120,
        "Fitness": 55,
        "Apparel": 38,
        "Kitchen": 42,
    }

    rows = []
    for i in range(1, n_products + 1):
        category = rng.choice(categories)
        base = category_base_price[category]
        price = max(8, rng.normal(base, base * 0.28))
        rows.append(
            {
                "product_id": f"P{i:04d}",
                "category": category,
                "list_price": round(price, 2),
            }
        )
    return pd.DataFrame(rows)


def make_transactions(
    rng: np.random.Generator, customers: pd.DataFrame, products: pd.DataFrame
) -> pd.DataFrame:
    rows = []
    product_lookup = products.set_index("product_id")
    end_date = pd.Timestamp("2025-12-31")

    channel_multiplier = {
        "Organic": 1.04,
        "Paid Search": 0.88,
        "Social": 0.82,
        "Referral": 1.22,
        "Email": 1.35,
    }
    region_multiplier = {"West": 1.12, "Northeast": 1.06, "South": 0.92, "Midwest": 0.96}

    for row in customers.itertuples(index=False):
        days_active = max(1, (end_date - row.signup_date).days)
        base_rate = rng.gamma(shape=1.8, scale=1.15)
        behavioral_multiplier = 0.55 + row.email_engagement_score * 0.75 + row.loyalty_score * 1.25
        purchase_lambda = base_rate * channel_multiplier[row.acquisition_channel] * region_multiplier[row.region]
        purchase_lambda *= behavioral_multiplier
        expected_orders = purchase_lambda * (days_active / 365)
        n_orders = int(rng.poisson(expected_orders))

        if rng.random() < 0.08 + row.loyalty_score * 0.22:
            n_orders += rng.integers(1, 4)

        for _ in range(n_orders):
            order_date = row.signup_date + pd.Timedelta(days=int(rng.integers(0, days_active + 1)))
            if rng.random() < 0.62:
                product_pool = products[products["category"] == row.preferred_category]
            else:
                product_pool = products
            product = product_pool.sample(1, random_state=int(rng.integers(0, 1_000_000))).iloc[0]
            quantity = int(np.clip(rng.poisson(1.35) + 1, 1, 6))
            discount_pct = float(rng.choice([0, 0.05, 0.10, 0.15, 0.20], p=[0.46, 0.18, 0.18, 0.12, 0.06]))
            unit_price = float(product_lookup.loc[product.product_id, "list_price"])
            revenue = unit_price * quantity * (1 - discount_pct)
            rows.append(
                {
                    "transaction_id": f"T{len(rows) + 1:07d}",
                    "customer_id": row.customer_id,
                    "order_date": order_date,
                    "product_id": product.product_id,
                    "category": product.category,
                    "quantity": quantity,
                    "discount_pct": discount_pct,
                    "revenue": round(revenue, 2),
                }
            )

    transactions = pd.DataFrame(rows)
    return transactions.sort_values("order_date").reset_index(drop=True)


def make_campaign_events(rng: np.random.Generator, customers: pd.DataFrame, transactions: pd.DataFrame) -> pd.DataFrame:
    campaign_date = pd.Timestamp("2025-08-01")
    eligible = customers[customers["signup_date"] < campaign_date].copy()
    treated = set(rng.choice(eligible["customer_id"], size=int(len(eligible) * 0.38), replace=False))

    tx_after = transactions[
        (transactions["order_date"] >= campaign_date)
        & (transactions["order_date"] < campaign_date + pd.Timedelta(days=30))
    ]
    bought_after = set(tx_after["customer_id"])

    rows = []
    for customer_id in eligible["customer_id"]:
        customer = eligible.loc[eligible["customer_id"] == customer_id].iloc[0]
        is_treated = customer_id in treated
        base_response = customer_id in bought_after
        incremental_probability = 0.025 + customer["email_engagement_score"] * 0.08 + customer["loyalty_score"] * 0.05
        incremental = is_treated and (rng.random() < incremental_probability)
        rows.append(
            {
                "customer_id": customer_id,
                "campaign_name": "Back-to-school retention offer",
                "campaign_date": campaign_date,
                "treatment_group": "Targeted" if is_treated else "Holdout",
                "converted_30d": int(base_response or incremental),
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(RANDOM_SEED)

    customers = make_customers(rng)
    products = make_products(rng)
    transactions = make_transactions(rng, customers, products)
    campaign_events = make_campaign_events(rng, customers, transactions)

    customers.to_csv(RAW_DIR / "customers.csv", index=False)
    products.to_csv(RAW_DIR / "products.csv", index=False)
    transactions.to_csv(RAW_DIR / "transactions.csv", index=False)
    campaign_events.to_csv(RAW_DIR / "campaign_events.csv", index=False)

    print(f"Generated {len(customers):,} customers")
    print(f"Generated {len(products):,} products")
    print(f"Generated {len(transactions):,} transactions")
    print(f"Generated {len(campaign_events):,} campaign events")


if __name__ == "__main__":
    main()
