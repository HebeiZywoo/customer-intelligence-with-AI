# Interview Talk Track

## 30-Second Version

I built an AI-powered customer intelligence platform for an ecommerce retention use case. The project uses DuckDB SQL for analytical reporting, segments customers with RFM features, compares models for 60-day repeat purchase prediction, explains model drivers, estimates campaign lift and ROI, and exposes the results in a Streamlit dashboard with executive recommendations.

## Problem

The business question is how to allocate marketing budget more efficiently. Instead of sending discounts to everyone, the team needs to know which customers are valuable, which customers are at risk, and which groups are likely to respond to a campaign.

## Data

The dataset contains customers, products, transactions, campaign events, and CRM-style engagement signals. I used a time-based cutoff date so that features are built only from historical behavior and the target is future repeat purchase within 60 days.

## Methods

I used RFM features for customer segmentation because they are interpretable for marketing stakeholders. Then I compared logistic regression, random forest, and gradient boosting classifiers to predict repeat purchase probability. I evaluated the models with ROC AUC, precision, recall, and F1, and selected the best model by ROC AUC.

## Explainability

I exported feature importance for the selected model and surfaced the top drivers in the dashboard. This helps validate that the model is learning from sensible signals such as recency, frequency, monetary value, engagement, and loyalty rather than relying on suspicious leakage.

## Experimentation

I used the campaign holdout group to estimate incremental lift, a 95% confidence interval, and a p-value. Then I translated lift into expected incremental conversions, revenue, margin, campaign cost, net profit, and ROI. That turns the project from a prediction exercise into a business decision tool.

## SQL Layer

I added a DuckDB layer to simulate an analytics warehouse. The SQL outputs summarize segment performance, acquisition channel cohorts, and campaign lift. This makes the project closer to a real data scientist workflow where model outputs are joined back into business reporting tables.

## Business Impact

The dashboard lets a marketer find high-value loyal customers, at-risk customers, and targeted-offer candidates. The assistant summarizes the recommendation using model metrics and segment-level evidence.

## What I Would Improve Next

- Add a real SQL warehouse layer using DuckDB.
- Add uplift modeling to estimate incremental campaign impact.
- Connect the assistant to an LLM with retrieval over trusted metric tables.
- Add model monitoring for data drift and prediction stability.
