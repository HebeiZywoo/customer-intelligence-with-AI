# Data Dictionary

## Raw Tables

### `customers.csv`

| Column | Description |
|---|---|
| `customer_id` | Unique customer identifier. |
| `signup_date` | Date the customer joined. |
| `acquisition_channel` | Channel where the customer was acquired. |
| `region` | Customer region. |
| `age` | Customer age. |
| `preferred_category` | Simulated preferred product category. |
| `email_engagement_score` | Simulated engagement score from 0 to 1. |
| `loyalty_score` | Simulated loyalty score from 0 to 1. |

### `products.csv`

| Column | Description |
|---|---|
| `product_id` | Unique product identifier. |
| `category` | Product category. |
| `list_price` | Product list price. |

### `transactions.csv`

| Column | Description |
|---|---|
| `transaction_id` | Unique transaction identifier. |
| `customer_id` | Customer identifier. |
| `order_date` | Date of the transaction. |
| `product_id` | Product identifier. |
| `category` | Product category. |
| `quantity` | Quantity purchased. |
| `discount_pct` | Discount percentage applied. |
| `revenue` | Transaction revenue after discount. |

### `campaign_events.csv`

| Column | Description |
|---|---|
| `customer_id` | Customer identifier. |
| `campaign_name` | Campaign label. |
| `campaign_date` | Campaign launch date. |
| `treatment_group` | `Targeted` or `Holdout`. |
| `converted_30d` | Whether the customer converted within 30 days. |

## Processed Tables

### `customer_features.csv`

| Column | Description |
|---|---|
| `frequency` | Historical number of transactions before cutoff. |
| `monetary` | Historical customer revenue before cutoff. |
| `avg_order_value` | Average transaction value. |
| `total_quantity` | Total units purchased. |
| `avg_discount` | Average discount percentage. |
| `unique_categories` | Number of distinct categories purchased. |
| `top_category` | Category with the highest historical revenue. |
| `campaign_targeted` | Whether customer was previously targeted. |
| `campaign_converted_30d` | Whether customer converted after campaign. |
| `recency_days` | Days since last order at cutoff. |
| `days_since_signup` | Customer age in days at cutoff. |
| `orders_per_100_days` | Normalized order frequency. |
| `monetary_per_100_days` | Normalized customer value. |
| `discounted_revenue` | Monetary value multiplied by average discount. |
| `preference_match` | Whether preferred category matches top purchased category. |
| `segment` | RFM-derived customer segment. |
| `repeat_purchase_60d` | Future 60-day repeat-purchase label. |
| `repeat_purchase_probability` | Model-predicted repeat-purchase probability. |
| `recommended_action` | Suggested marketing action. |

### `campaign_experiment_summary.csv`

| Column | Description |
|---|---|
| `targeted_conversion_rate` | Conversion rate in targeted group. |
| `holdout_conversion_rate` | Conversion rate in holdout group. |
| `absolute_lift` | Difference between targeted and holdout conversion rates. |
| `relative_lift` | Relative lift compared with holdout. |
| `lift_ci_low` | Lower bound of 95% confidence interval. |
| `lift_ci_high` | Upper bound of 95% confidence interval. |
| `p_value` | Two-sided p-value for lift estimate. |
| `incremental_conversions` | Estimated incremental conversions. |
| `incremental_revenue` | Estimated revenue from incremental conversions. |
| `incremental_margin` | Estimated gross margin from incremental revenue. |
| `campaign_cost` | Estimated campaign cost. |
| `net_profit` | Incremental margin minus campaign cost. |
| `roi` | Net profit divided by campaign cost. |
