# Case Study: AI-Powered Customer Intelligence Platform

## Executive Summary

This project simulates a real ecommerce retention problem: how should a marketing team decide which customers to target, which customers to protect from churn, and whether a campaign is financially worth scaling?

I built an end-to-end customer intelligence platform that combines DuckDB SQL analytics, customer segmentation, repeat-purchase prediction, campaign experiment analysis, model explainability, and an interactive Streamlit dashboard.

The final recommendation is to prioritize high-value loyalists for retention while using targeted offers for mid-probability customers. The campaign analysis estimates a 7.2 percentage point absolute lift, with a 95% confidence interval from 2.5% to 11.8%, and a projected ROI of 115.7% under the stated cost and margin assumptions.

## Business Problem

The business team wants to improve customer retention without wasting discounts. A broad coupon campaign may increase conversion, but it can also spend money on customers who would have purchased anyway.

The core questions are:

- Which customers are most valuable?
- Which customers are likely to purchase again in the next 60 days?
- Which customers should receive a targeted offer?
- Did the campaign create incremental conversion compared with a holdout group?
- What is the expected financial impact if the campaign is scaled?

## Data

The project uses simulated ecommerce data with realistic relationships between customer behavior, engagement, purchases, and campaign response.

The raw tables are:

- `customers`: signup date, channel, region, age, preferred category, engagement score, loyalty score.
- `products`: product category and list price.
- `transactions`: order date, product, quantity, discount, and revenue.
- `campaign_events`: treatment group, campaign date, and 30-day conversion outcome.

The modeling dataset is built at the customer level using a time-based cutoff. Historical behavior before the cutoff becomes features, while future behavior after the cutoff becomes the 60-day repeat-purchase label. This avoids using future information in training.

## Methodology

### 1. Analytics Warehouse Layer

I used DuckDB to simulate an analytics warehouse. The pipeline registers raw data and model outputs as relational tables, then exports reusable SQL reporting tables.

The SQL outputs include:

- Segment performance by revenue, value, repeat rate, and predicted repeat probability.
- Campaign lift comparing targeted customers with a holdout group.
- Acquisition channel cohorts.
- Customer lifecycle stages.

This mirrors a common data science workflow where model outputs are joined back into reporting tables for business stakeholders.

### 2. Customer Segmentation

I created RFM-style customer features:

- `recency_days`: days since last order.
- `frequency`: historical order count.
- `monetary`: historical revenue.
- `avg_order_value`: average spend per order.

Then I used KMeans clustering to create interpretable customer segments.

Key segments:

| Segment | Customers | Avg Monetary | Repeat Rate | Campaign Conversion |
|---|---:|---:|---:|---:|
| High-value loyalists | 177 | $1,572 | 66.1% | 56.5% |
| Emerging customers | 1,053 | $354 | 42.6% | 25.9% |
| At-risk or dormant | 570 | $0 | 26.3% | 1.1% |

This segmentation gives the business a simple way to distinguish loyalty, growth, and win-back strategies.

### 3. Repeat-Purchase Prediction

The target variable is `repeat_purchase_60d`, which indicates whether a customer purchased again within 60 days after the cutoff date.

I compared three supervised learning models:

| Model | ROC AUC | Accuracy | Precision | Recall | F1 |
|---|---:|---:|---:|---:|---:|
| Logistic Regression | 0.697 | 0.636 | 0.538 | 0.592 | 0.564 |
| Random Forest | 0.709 | 0.647 | 0.560 | 0.525 | 0.542 |
| Gradient Boosting | 0.704 | 0.658 | 0.591 | 0.453 | 0.513 |

Random Forest was selected because it had the best ROC AUC. For this use case, ROC AUC is a useful primary metric because the business cares about ranking customers by likelihood to repeat, not only assigning a binary label.

### 4. Model Explainability

I exported feature importance from the selected model and surfaced the top drivers in the dashboard.

Top model drivers include:

- `orders_per_100_days`
- `monetary_per_100_days`
- `days_since_signup`
- `recency_days`
- `loyalty_score`
- `email_engagement_score`
- `discounted_revenue`

These drivers are directionally reasonable for a retention model: active customers, higher-value customers, recent buyers, loyal customers, and engaged customers are more likely to repeat.

### 5. Experimentation and ROI

The campaign analysis compares a targeted group against a holdout group.

| Metric | Value |
|---|---:|
| Targeted conversion rate | 30.0% |
| Holdout conversion rate | 22.8% |
| Absolute lift | 7.2 percentage points |
| Relative lift | 31.4% |
| 95% CI for lift | 2.5% to 11.8% |
| p-value | 0.0025 |

I then translated lift into business impact using explicit assumptions:

- Average order value: $133.87
- Gross margin assumption: 45%
- Offer cost per targeted customer: $2.00
- Targeted-offer candidates: 883

Estimated impact:

| Metric | Value |
|---|---:|
| Incremental conversions | 63.2 |
| Incremental revenue | $8,464 |
| Incremental margin | $3,809 |
| Campaign cost | $1,766 |
| Net profit | $2,043 |
| Projected ROI | 115.7% |

This turns the project from a prediction exercise into a decision-support tool.

## Dashboard

The Streamlit dashboard has seven main areas:

- Executive Brief: recommendation, expected impact, and decision guardrails.
- Overview: revenue, repeat rate, and recommended marketing actions.
- Segments: segment summary and RFM map.
- Prediction: model comparison, model metrics, feature importance, and ranked customers.
- Experiment: lift, confidence interval, p-value, ROI, and segment-level lift.
- SQL Insights: DuckDB-powered reporting tables.
- AI Assistant: a grounded question-answering layer over project metrics.

## Recommendation

The recommended campaign strategy is:

1. Protect high-value loyalists with loyalty-oriented retention, not heavy discounts.
2. Send targeted offers to mid-probability customers where the offer is more likely to influence behavior.
3. Keep a holdout group in every campaign wave to measure incremental lift.
4. Scale only while the lift confidence interval remains positive and ROI remains above the business threshold.
5. Re-score customers before each campaign wave to account for behavior changes.

## Limitations

This is a portfolio project using simulated data, so results should be interpreted as a demonstration of method rather than a real business conclusion.

Important limitations:

- The data-generating process is simplified compared with a real ecommerce business.
- The campaign simulation does not fully solve selection bias or heterogeneous treatment effects.
- The ROI estimate depends on margin and offer-cost assumptions.
- The AI assistant is currently grounded in project outputs but is not connected to a production LLM or vector database.
- Model monitoring and drift detection are not yet implemented.

## Next Steps

The strongest next extensions would be:

- Add uplift modeling to estimate individual treatment effect instead of only repeat-purchase probability.
- Add bootstrap confidence intervals for segment-level lift.
- Add model monitoring for data drift and prediction stability.
- Connect the assistant to an LLM with retrieval over SQL outputs and model artifacts.
- Deploy the dashboard and add a short project demo video.

## What This Demonstrates

This project demonstrates the core skills expected of a Data Scientist:

- Framing a business problem.
- Building clean customer-level features.
- Using SQL for analytical reporting.
- Training and comparing machine learning models.
- Explaining model behavior.
- Designing experiment analysis with a holdout group.
- Translating model and experiment results into ROI.
- Communicating recommendations through an interactive dashboard.
