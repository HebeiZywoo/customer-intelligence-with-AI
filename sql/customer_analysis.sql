-- Customer Intelligence SQL Analysis
-- These are the portfolio-facing DuckDB queries used by scripts/run_sql_analysis.py.

-- 1. Segment performance
SELECT
    segment,
    COUNT(*) AS customers,
    ROUND(SUM(monetary), 2) AS revenue,
    ROUND(AVG(monetary), 2) AS avg_customer_value,
    ROUND(AVG(frequency), 2) AS avg_orders,
    ROUND(AVG(repeat_purchase_probability), 4) AS avg_predicted_repeat,
    ROUND(AVG(repeat_purchase_60d), 4) AS actual_repeat_rate
FROM customer_features
GROUP BY segment
ORDER BY revenue DESC;

-- 2. Campaign lift
SELECT
    treatment_group,
    COUNT(*) AS customers,
    ROUND(AVG(converted_30d), 4) AS conversion_rate
FROM campaign_events
GROUP BY treatment_group;

-- 3. Acquisition channel cohorts
SELECT
    acquisition_channel,
    COUNT(*) AS customers,
    ROUND(AVG(monetary), 2) AS avg_customer_value,
    ROUND(AVG(repeat_purchase_probability), 4) AS avg_predicted_repeat,
    ROUND(AVG(email_engagement_score), 3) AS avg_email_engagement
FROM customer_features
GROUP BY acquisition_channel
ORDER BY avg_customer_value DESC;
