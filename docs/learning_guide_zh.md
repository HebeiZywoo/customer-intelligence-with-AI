# 手把手学习路线

这个项目的目标不是炫技，而是训练你像 Data Scientist 一样讲业务问题、数据、方法、结果和下一步。

## 第 1 步：先跑通项目

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/generate_data.py
python scripts/train_models.py
python scripts/run_sql_analysis.py
streamlit run app/streamlit_app.py
```

你要先确认三件事：

- 数据能生成。
- 模型能训练。
- Dashboard 能打开。
- SQL 分析结果能出现在 `SQL Insights` 页签。
- `Executive Brief` 能直接给出业务建议、预估收益和风险控制。

## 第 2 步：理解业务问题

面试里不要先说模型。先说：

> 我模拟了一个电商增长团队的问题：如何识别高价值客户、预测未来 60 天复购概率，并把营销预算投给最可能产生增量收益的人群。

## 第 3 步：理解特征

重点特征：

- `recency_days`: 距离上次购买多久。
- `frequency`: 历史购买次数。
- `monetary`: 历史消费金额。
- `avg_order_value`: 平均订单金额。
- `campaign_converted_30d`: 过去营销活动是否转化。
- `orders_per_100_days`: 标准化后的购买频率。

这些特征能自然对应业务直觉，所以比盲目堆模型更好讲。

## 第 4 步：理解标签

标签是 `repeat_purchase_60d`：

> 在 2025-10-01 之后 60 天内是否再次购买。

这可以展示你知道如何避免时间泄漏：训练特征只使用 cutoff date 之前的数据，标签来自 cutoff date 之后的未来窗口。

## 第 5 步：理解模型

本项目使用两类模型：

- KMeans 做 RFM 客户分群。
- 多个监督学习模型做 60 天复购预测，并自动选择 ROC AUC 最好的模型。

面试时可以说：

> 我先用 RFM + KMeans 得到可解释客户群，再比较 Logistic Regression、Random Forest 和 Gradient Boosting 来预测复购概率。分群帮助业务理解人群，预测模型帮助排序营销优先级。

## 第 6 步：理解 SQL 层

DuckDB 层模拟真实公司的 analytics warehouse。脚本 `scripts/run_sql_analysis.py` 会把原始数据和模型输出注册成表，然后用 SQL 产出：

- `sql_segment_performance.csv`: 各客户群收入、复购率、预测复购概率。
- `sql_campaign_lift.csv`: Targeted vs Holdout 的营销 lift。
- `sql_channel_cohorts.csv`: 不同获客渠道的客户价值和复购倾向。
- `sql_lifecycle_stages.csv`: 客户生命周期阶段分析。

## 第 7 步：理解指标

不要只说 accuracy。营销场景更关心排序能力，所以 ROC AUC 很重要。

你可以这样讲：

> 这个模型主要用于客户排序，所以我看 ROC AUC 来判断模型能否把高复购概率客户排在前面。同时看 precision 和 recall，平衡营销成本和覆盖率。

## 第 8 步：理解模型解释性

`feature_importance.csv` 会告诉你模型最依赖哪些特征。面试时不要只说“模型效果不错”，要说：

> 我检查了 feature importance，确认模型主要依赖 recency、frequency、monetary、engagement 等符合业务直觉的信号。如果重要特征不符合业务直觉，我会回头检查数据泄漏或特征定义。

## 第 9 步：理解实验和 ROI

`campaign_experiment_summary.csv` 会输出：

- Targeted 和 Holdout 转化率。
- absolute lift 和 relative lift。
- 95% confidence interval。
- p-value。
- incremental conversions、revenue、margin、cost、ROI。

面试时可以这样讲：

> 我没有只看模型预测，还用 holdout group 估计营销活动的增量效果，并把 lift 转换成 ROI，帮助业务判断是否值得扩大投放。

## 第 10 步：理解 AI 助手

当前版本的 AI Assistant 是一个 grounded insight assistant：它不是随便编答案，而是只基于模型指标和分群结果回答。

下一步可以接入真实 LLM：

- 把 `segment_summary.csv`、`model_metrics.json` 和业务规则作为检索上下文。
- 用户提问后先检索相关指标。
- LLM 只根据检索到的证据生成回答。

## 第 11 步：简历讲法

英文 bullet：

> Built an AI-powered customer intelligence platform using Python, DuckDB SQL, scikit-learn, and Streamlit to segment customers, compare repeat-purchase models, explain model drivers, estimate campaign lift/ROI with confidence intervals, and generate executive-ready business recommendations through an interactive dashboard.

中文讲法：

> 我做了一个端到端客户智能分析平台，从数据生成、特征工程、客户分群、复购预测，到 dashboard 和 AI 分析助手。它模拟真实电商增长团队如何用数据决定营销资源分配。
