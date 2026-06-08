# AI SCM Data Analysis Project

Japanese / English portfolio project for SCM, data analysis, and AI agent roles.

This project is a Streamlit-based SCM decision-support dashboard for global fashion retail. It connects demand forecasting, SKU-store inventory policy, reorder-point calculation, replenishment recommendations, inter-store transfer recommendations, and an SCM Manager Agent into one practical business workflow.

## Portfolio Target

- Target roles: SCM Analyst, Data Analyst, AI Solution Planner, Retail Operations Analyst
- Target market: Japanese retail / apparel / logistics companies
- Portfolio owner: Lee
- Demo data: simulated retail SCM data only. No private company data is included.

## Japanese Summary

本プロジェクトは、グローバルファッション小売業のSCM業務を想定したデータ分析ポートフォリオです。需要予測、SKU・店舗別の発注点、安全在庫、補充推奨、店舗間在庫移動、AIエージェントによる意思決定支援を一つのダッシュボードに統合しています。

面接では、単なるチャート作成ではなく、在庫切れ・過剰在庫・補充優先度というビジネス課題を、データとルールベースのロジック、さらに任意のGemini API連携で説明できる点をアピールできます。

## Business Problem

Global apparel retailers need to reduce stockouts, overstock, and logistics inefficiency while responding to demand volatility across stores and products.

This portfolio answers the question:

> How can an AI Agent support SCM managers by forecasting demand, detecting SKU-store inventory risk, and recommending replenishment or store-transfer actions?

## Key Features

- Demand forecasting by SKU and store
- Reorder Point (ROP) and safety-stock calculation
- SKU-store stockout and overstock risk detection
- Replenishment recommendation with priority levels
- Inter-store inventory transfer recommendation
- Streamlit dashboard with English, Japanese, and Korean UI labels
- SCM Manager Agent chat
- Optional Gemini API response generation with local rule-based fallback
- PowerPoint portfolio deck generation scripts

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
- python-pptx
- Google GenAI SDK (optional)

## Folder Structure

```text
scm-agent-portfolio/
  app.py
  requirements.txt
  .env.example
  data/
    sales.csv
    inventory.csv
    forecast.csv
    recommendations.csv
    transfer_recommendations.csv
  outputs/
    AI_SCM_Data_Analysis_Project_3pages.pptx
    AI_SCM_Data_Analysis_Project_Agent_Architecture_1page.pptx
  assets/
    screenshots/
      dashboard-risk-overview.jpg
      dashboard-demand-forecast.jpg
      dashboard-rop-policy.jpg
      dashboard-ai-agent.jpg
  scripts/
    build_demo_data.py
    generate_ppt.py
    generate_3page_interview_ppt.py
    generate_hierarchical_agent_1page_ppt.py
  src/
    agent.py
    scm_engine.py
```

## Setup

```bat
cd scm-agent-portfolio
python -m pip install -r requirements.txt
```

## Build Demo Data

```bat
python scripts\build_demo_data.py
```

Optional Open-Meteo weather API version:

```bat
python scripts\build_demo_data.py --use-open-meteo
```

Open-Meteo does not require an API key.

## Run Dashboard

```bat
streamlit run app.py --server.port 8502
```

Then open:

```text
http://localhost:8502
```

## Generate Portfolio PPT

```bat
python scripts\generate_3page_interview_ppt.py
python scripts\generate_hierarchical_agent_1page_ppt.py
```

Example outputs:

```text
outputs\AI_SCM_Data_Analysis_Project_3pages.pptx
outputs\AI_SCM_Data_Analysis_Project_Agent_Architecture_1page.pptx
```

## Optional API Keys

Do not commit real keys into GitHub.

The chatbot can use Google's official GenAI SDK when `GEMINI_API_KEY` is configured. Without an API key, the dashboard automatically uses a local rule-based SCM Agent.

Environment variable example:

```bat
set "GEMINI_API_KEY=your_key_here"
streamlit run app.py --server.port 8502
```

Streamlit secrets example:

```text
.streamlit\secrets.toml
```

```toml
GEMINI_API_KEY = "your_key_here"
```

## Interview Talking Points

- I designed the portfolio around a real SCM decision flow, not only visualization.
- I converted sales, inventory, supply, and forecast data into SKU-store level actions.
- I implemented ROP and safety-stock logic to explain replenishment decisions clearly.
- I added an AI Agent layer so SCM managers can ask business questions in natural language.
- The system works without external API keys, but can be extended with Gemini when available.

## Japanese Interview Pitch

このポートフォリオは、ファッション小売SCMにおける在庫切れと過剰在庫の削減を目的に作成しました。需要予測、発注点、安全在庫、補充推奨、店舗間在庫移動を一つのワークフローとして設計し、SCMマネージャーが優先対応すべきSKUと店舗を判断できるようにしています。

AIエージェント部分では、ダッシュボード上のSCMデータをもとに、補充優先度や在庫リスクについて自然言語で説明できます。外部APIがない場合でもローカルルールベースで動作するため、面接やデモ環境でも安定して説明できます。

## Security Notes

- `.env` and Streamlit secrets are ignored by Git.
- The included data is simulated demo data.
- Real API keys should be provided only through environment variables or local secrets.

