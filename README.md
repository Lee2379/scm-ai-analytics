# AI SCM Data Analysis Project

SCM analytics and decision-support dashboard for global fashion retail operations.

This project is a Streamlit-based SCM decision-support dashboard for global fashion retail. It connects demand forecasting, SKU-store inventory policy, reorder-point calculation, replenishment recommendations, inter-store transfer recommendations, and an SCM Manager Agent into one practical business workflow.

## Project Scope

- Domain: fashion retail SCM and inventory operations
- Focus areas: demand forecasting, inventory policy, replenishment planning, and store-transfer decisions
- Decision level: SKU-store-level risk monitoring and action prioritization
- Data scope: simulated retail SCM data only. No private company data is included.

## Japanese Summary

本プロジェクトは、グローバルファッション小売業のSCM業務を想定したデータ分析・意思決定支援ダッシュボードです。需要予測、SKU・店舗別の発注点、安全在庫、補充推奨、店舗間在庫移動、AIエージェントによる判断支援を一つの業務フローとして統合しています。

在庫切れ・過剰在庫・補充優先度というSCM上の課題に対し、データ処理、在庫ロジック、可視化、自然言語による確認機能を組み合わせて、実務に近い意思決定プロセスを再現します。

## Data Source and Dataset Notes

This project is designed around public retail datasets available on Kaggle and uses a reproducible synthetic SCM layer for dashboard execution. It does not use confidential, customer, transaction, or internal company data.

Public data references:

| Source | Public Dataset | How It Is Used in This Project |
| --- | --- | --- |
| Kaggle | [H&M Personalized Fashion Recommendations](https://www.kaggle.com/competitions/h-and-m-personalized-fashion-recommendations) | Reference for fashion retail product, customer transaction, and article metadata concepts. |
| Kaggle | [M5 Forecasting - Accuracy](https://www.kaggle.com/competitions/m5-forecasting-accuracy) | Reference for retail demand forecasting, hierarchical sales structure, and 28-day forecast workflow. |

The CSV files committed in this repository are not raw Kaggle exports. They are demonstration-ready SCM tables modeled from public retail data concepts so the dashboard can run without private data, large raw files, or external credentials.

- Store master data represents five Japanese city-level retail locations: Tokyo, Yokohama, Osaka, and Fukuoka.
- Product master data uses representative fashion retail categories such as innerwear, outerwear, bottoms, shirts, and knitwear.
- Sales, inventory, supply, weather, forecast, replenishment, and transfer tables are generated through deterministic simulation logic.
- Demand patterns include seasonality, weekends, holiday-like periods, promotions, weather sensitivity, and store-type effects.
- Inventory policy outputs are calculated from average demand, demand variation, lead time, service level, safety stock, and reorder point logic.
- Weather values are simulation inputs for demand modeling and are not presented as official meteorological observations.

The data is intended to demonstrate SCM analytics workflow design, inventory policy calculation, and operational decision support under controlled assumptions.

## Data EDA Summary

The EDA process focuses on confirming that the dataset is suitable for SKU-store-level SCM decision support before applying forecasting, reorder point, and transfer logic.

| EDA Area | Check | Result |
| --- | --- | --- |
| Data volume | Sales history coverage | 10,800 sales rows from 2025-01-01 to 2025-06-29 |
| Master data | Store and product coverage | 5 Japanese city-level stores and 12 fashion retail SKUs |
| Granularity | SCM decision unit | 60 SKU-store combinations |
| Inventory risk | Stock status distribution | 26 stockout-risk cases and 3 overstock cases |
| Recommendation output | Action table coverage | 60 replenishment records and 8 store-transfer recommendations |

EDA workflow:

1. Validate table structure and key fields across sales, product, store, inventory, supply, forecast, and recommendation tables.
2. Check time coverage, SKU-store combinations, and whether each operational table can be joined through `store_id` and `sku_id`.
3. Review demand patterns by product, store, seasonality, weekend or holiday-like periods, promotions, and weather-sensitive categories.
4. Compare current inventory against calculated safety stock and reorder point to identify stockout and overstock risk.
5. Convert EDA findings into dashboard views: risk distribution, city-level risk, demand forecast, ROP policy, replenishment priority, and store-transfer recommendations.

## Business Problem

Global apparel retailers need to reduce stockouts, overstock, and logistics inefficiency while responding to demand volatility across stores and products.

This system answers the question:

> How can an AI Agent support SCM managers by forecasting demand, detecting SKU-store inventory risk, and recommending replenishment or store-transfer actions?

## End-to-End Delivery Flow

This project is structured as an end-to-end analytics delivery workflow, from business planning to a deployable dashboard.

```mermaid
flowchart LR
    A["Business Planning<br/>SCM issue framing"] --> B["Problem Definition<br/>Stockout, overstock, replenishment priority"]
    B --> C["Data Design<br/>Store, product, sales, inventory, supply, weather"]
    C --> D["Analytics Logic<br/>Forecast, safety stock, ROP, transfer rules"]
    D --> E["Application Development<br/>Streamlit dashboard and SCM Agent"]
    E --> F["Validation<br/>Risk tables, charts, and recommendation checks"]
    F --> G["Deployment Preparation<br/>GitHub versioning, dependency setup, runtime command"]
```

| Delivery Area | Implementation in This Project |
| --- | --- |
| Planning | Defines a retail SCM decision-support system around inventory risk and replenishment actions. |
| Business Problem | Converts stockout, overstock, and transfer decisions into measurable SKU-store-level logic. |
| Data Preparation | Uses structured CSV tables for store, product, sales, inventory, supply, weather, forecast, and recommendations. |
| Development | Implements SCM calculation logic, dashboard visualization, and natural-language Agent responses. |
| Deployment Readiness | Provides a GitHub-hosted project structure, dependency file, and Streamlit runtime command. |

## Key Features

- Demand forecasting by SKU and store
- Reorder Point (ROP) and safety-stock calculation
- SKU-store stockout and overstock risk detection
- Replenishment recommendation with priority levels
- Inter-store inventory transfer recommendation
- Streamlit dashboard with English, Japanese, and Korean UI labels
- SCM Manager Agent chat

## Dashboard Screenshots

### Inventory Risk and Replenishment Overview

![Inventory risk distribution and top replenishment recommendations](assets/screenshots/dashboard-risk-overview.jpg)

### Demand Forecast and Sales Pattern

![Demand forecast and recent sales pattern charts](assets/screenshots/dashboard-demand-forecast.jpg)

### SKU-Store ROP Policy

![SKU-store-level ROP policy table](assets/screenshots/dashboard-rop-policy.jpg)

### SCM Manager Agent

![Japanese SCM Manager Agent response for reorder priority](assets/screenshots/dashboard-ai-agent.jpg)

## SCM Logic

```text
Safety Stock = std_daily_demand x Z-value x sqrt(lead_time_days)
ROP = avg_daily_demand x lead_time_days + Safety Stock
```

If current inventory is below ROP, the system marks the SKU-store pair as stockout risk and recommends replenishment.

```text
current_inventory < ROP -> replenishment recommendation
```

## Tech Stack

- Python
- Streamlit
- pandas / NumPy
- Plotly
- scikit-learn
- Google GenAI SDK (optional)

## Folder Structure

```text
ai-scm-data-analysis-project/
  app.py
  requirements.txt
  .env.example
  data/
    sales.csv
    inventory.csv
    forecast.csv
    recommendations.csv
    transfer_recommendations.csv
  assets/
    screenshots/
      dashboard-risk-overview.jpg
      dashboard-demand-forecast.jpg
      dashboard-rop-policy.jpg
      dashboard-ai-agent.jpg
  src/
    agent.py
    scm_engine.py
```

## Setup

```bat
cd ai-scm-data-analysis-project
python -m pip install -r requirements.txt
```

## Run Dashboard

```bat
streamlit run app.py --server.port 8502
```

Then open:

```text
http://localhost:8502
```

## Project Value

- Designed an end-to-end SCM decision workflow from demand signals to inventory actions.
- Converted sales, inventory, supply, and forecast data into SKU-store-level replenishment recommendations.
- Implemented ROP and safety-stock logic to make replenishment decisions explainable and auditable.
- Added an AI Agent layer that helps SCM managers review inventory risk and action priorities in natural language.
- Built the system to run with local rule-based logic by default for stable dashboard demonstrations.

## Japanese Project Summary

本プロジェクトは、ファッション小売SCMにおける在庫切れと過剰在庫の削減をテーマにしたデータ分析・意思決定支援システムです。需要予測、発注点、安全在庫、補充推奨、店舗間在庫移動を一つの業務フローとして設計し、SKU・店舗単位で優先対応すべき在庫リスクを可視化します。

AIエージェント機能では、ダッシュボード上のSCMデータをもとに、補充優先度、在庫リスク、判断ロジックを自然言語で確認できます。ローカルのルールベースロジックで安定して動作するため、データ分析から意思決定支援までの流れを一貫して確認できます。

## Security Notes

- `.env` and Streamlit secrets are ignored by Git.
- The included data is simulated demo data.
- Real API keys should be provided only through environment variables or local secrets.

