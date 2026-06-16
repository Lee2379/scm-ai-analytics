from __future__ import annotations

import html
import os
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from src.agent import build_scm_context, gemini_ready, gemini_reply_if_configured, load_agent_tables, local_agent_reply


ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"

RETAIL_RED = "#e60012"
INK_BLACK = "#111111"
STATUS_COLORS = {
    "Healthy": INK_BLACK,
    "Stockout Risk": RETAIL_RED,
    "Overstock": "#8a8a8a",
}
STORE_COLORS = [RETAIL_RED, INK_BLACK, "#777777", "#b0000d", "#d8d8d8"]
LANG_OPTIONS = {
    "en": "English",
    "ja": "\u65e5\u672c\u8a9e",
    "ko": "\ud55c\uad6d\uc5b4",
}

JP = {
    "portfolio": "AI SCM\u30c7\u30fc\u30bf\u5206\u6790\u30b7\u30b9\u30c6\u30e0",
    "hero_title": "AI SCM Data Analysis Project",
    "summary": "\u9700\u8981\u4e88\u6e2c\u3001SKU\u30fb\u5e97\u8217\u5225\u767a\u6ce8\u70b9\u3001\u5b89\u5168\u5728\u5eab\u3001\u88dc\u5145\u63a8\u85a6\u3001\u5e97\u8217\u9593\u5728\u5eab\u79fb\u52d5\u3092\u7d71\u5408\u3057\u305fSCM\u610f\u601d\u6c7a\u5b9a\u652f\u63f4\u30b7\u30b9\u30c6\u30e0\u3002",
    "chatbot": "\u30c1\u30e3\u30c3\u30c8\u30dc\u30c3\u30c8",
    "chat_desc": "\u73fe\u5728\u306eSCM\u30c7\u30e2\u30c7\u30fc\u30bf\u3092\u3082\u3068\u306b\u3001\u6b20\u54c1\u30ea\u30b9\u30af\u3001\u767a\u6ce8\u70b9\u3001\u5b89\u5168\u5728\u5eab\u3001\u88dc\u5145\u6570\u91cf\u3001\u5e97\u8217\u9593\u79fb\u52d5\u3092\u8ffd\u8de1\u3057\u307e\u3059\u3002",
    "controls": "\u64cd\u4f5c",
    "city": "\u90fd\u5e02",
    "status": "\u5728\u5eab\u30b9\u30c6\u30fc\u30bf\u30b9",
    "agent_lang": "\u30a8\u30fc\u30b8\u30a7\u30f3\u30c8\u8a00\u8a9e",
    "live_question": "\u30ea\u30a2\u30eb\u30bf\u30a4\u30e0SCM\u8cea\u554f",
    "track": "SCM\u3092\u8ffd\u8de1",
    "pairs": "SKU\u30fb\u5e97\u8217\u30da\u30a2",
    "stockout": "\u6b20\u54c1\u30ea\u30b9\u30af",
    "overstock": "\u904e\u5270\u5728\u5eab",
    "order_units": "\u63a8\u5968\u767a\u6ce8\u6570",
    "overview": "\u6982\u8981",
    "forecast": "\u9700\u8981\u4e88\u6e2c",
    "rop": "\u767a\u6ce8\u70b9\u30fb\u5b89\u5168\u5728\u5eab",
    "transfer": "\u5e97\u8217\u9593\u79fb\u52d5",
    "agent": "AI\u30a8\u30fc\u30b8\u30a7\u30f3\u30c8",
    "risk_dist": "\u5728\u5eab\u30ea\u30b9\u30af\u5206\u5e03",
    "city_risk": "\u90fd\u5e02\u5225\u30ea\u30b9\u30af",
    "top_replenishment": "\u512a\u5148\u88dc\u5145\u63a8\u85a6",
    "product": "\u5546\u54c1",
    "recent_sales": "\u76f4\u8fd1\u8ca9\u58f2\u30d1\u30bf\u30fc\u30f3",
    "sales_history": "\u5e97\u8217\u5225\u8ca9\u58f2\u5c65\u6b74",
    "policy": "SKU\u30fb\u5e97\u8217\u5225\u767a\u6ce8\u70b9\u30dd\u30ea\u30b7\u30fc",
    "transfer_rec": "\u5e97\u8217\u9593\u5728\u5eab\u79fb\u52d5\u63a8\u85a6",
    "no_transfer": "\u73fe\u5728\u306e\u30b7\u30ca\u30ea\u30aa\u3067\u306f\u5e97\u8217\u9593\u79fb\u52d5\u63a8\u85a6\u306f\u3042\u308a\u307e\u305b\u3093\u3002",
    "manager": "SCM\u30de\u30cd\u30fc\u30b8\u30e3\u30fc\u30a8\u30fc\u30b8\u30a7\u30f3\u30c8",
    "question": "\u8cea\u554f",
    "ask_agent": "SCM Agent\u306b\u8cea\u554f",
}


st.set_page_config(
    page_title="AI SCM Data Analysis Project",
    page_icon="SCM",
    layout="wide",
)

try:
    if "GEMINI_API_KEY" in st.secrets and not os.environ.get("GEMINI_API_KEY"):
        os.environ["GEMINI_API_KEY"] = st.secrets["GEMINI_API_KEY"]
except Exception:
    pass


@st.cache_data
def load_tables() -> dict[str, pd.DataFrame]:
    return {
        "sales": pd.read_csv(DATA_DIR / "sales.csv", parse_dates=["date"]),
        "products": pd.read_csv(DATA_DIR / "products.csv"),
        "stores": pd.read_csv(DATA_DIR / "stores.csv"),
        "policy": pd.read_csv(DATA_DIR / "inventory_policy.csv"),
        "recommendations": pd.read_csv(DATA_DIR / "recommendations.csv"),
        "forecast": pd.read_csv(DATA_DIR / "forecast.csv", parse_dates=["date"]),
        "transfers": pd.read_csv(DATA_DIR / "transfer_recommendations.csv"),
        "policy_results": pd.read_csv(DATA_DIR / "policy_eval_results.csv"),
        "policy_summary": pd.read_csv(DATA_DIR / "policy_eval_kpi_summary.csv"),
        "policy_segments": pd.read_csv(DATA_DIR / "policy_eval_segment_summary.csv"),
        "policy_tests": pd.read_csv(DATA_DIR / "policy_eval_statistical_tests.csv"),
    }


def data_ready() -> bool:
    required_files = [
        "sales.csv",
        "inventory_policy.csv",
        "recommendations.csv",
        "policy_eval_results.csv",
        "policy_eval_kpi_summary.csv",
        "policy_eval_segment_summary.csv",
        "policy_eval_statistical_tests.csv",
    ]
    return all((DATA_DIR / name).exists() for name in required_files)


def ask_scm_agent(question: str, lang: str) -> str:
    agent_tables = load_agent_tables(DATA_DIR)
    scm_context = build_scm_context(agent_tables)
    gemini_answer = gemini_reply_if_configured(question, scm_context, lang=lang)
    return gemini_answer or local_agent_reply(question, agent_tables, lang=lang)


def response_box(text: str) -> None:
    safe = html.escape(text).replace("\n", "<br>")
    st.markdown(f'<div class="chat-response">{safe}</div>', unsafe_allow_html=True)


def tr(lang: str, en: str, ja: str, ko: str) -> str:
    return {"en": en, "ja": ja, "ko": ko}.get(lang, en)


st.markdown(
    """
    <style>
    .stApp {
      background:
        linear-gradient(90deg, rgba(230, 0, 18, .05) 0 1px, transparent 1px 100%),
        linear-gradient(180deg, #ffffff 0%, #f7f7f7 100%);
      background-size: 56px 56px, auto;
      color: #111111;
    }
    [data-testid="stHeader"] {
      background: rgba(255, 255, 255, 0.88);
      border-bottom: 1px solid #ececec;
      backdrop-filter: blur(16px);
    }
    [data-testid="stSidebar"] {
      background: #ffffff;
      border-right: 1px solid #ececec;
    }
    .language-strip {
      display: flex;
      justify-content: flex-end;
      align-items: center;
      gap: 10px;
      margin: 0 0 14px;
      color: #555555;
      font-size: 12px;
      font-weight: 900;
      text-transform: uppercase;
    }
    .hero,
    .chat-panel {
      min-height: 304px;
      border: 1px solid #111111;
      border-radius: 0;
      background: #ffffff;
      box-shadow: 0 24px 60px rgba(0, 0, 0, .12);
    }
    .hero {
      padding: 30px;
      overflow: hidden;
    }
    .hero-kicker {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      margin: 0 0 14px;
      color: #e60012;
      font-size: 13px;
      font-weight: 900;
      text-transform: uppercase;
    }
    .hero-kicker::before {
      width: 28px;
      height: 3px;
      background: #e60012;
      content: "";
    }
    .ja-small {
      display: block;
      margin-top: 4px;
      color: #777777;
      font-size: 12px;
      font-weight: 700;
      line-height: 1.35;
      text-transform: none;
    }
    .hero h1 {
      margin: 0 0 10px;
      color: #111111;
      font-size: 48px;
      letter-spacing: 0;
      line-height: 1.05;
      font-weight: 900;
    }
    .portfolio-name {
      margin: 0 0 12px;
      color: #111111;
      font-size: 20px;
      font-weight: 900;
    }
    .hero p {
      margin: 0;
      color: #4b4b4b;
      font-size: 17px;
      line-height: 1.6;
    }
    .chat-panel {
      min-height: auto;
      padding: 0;
      margin-bottom: 10px;
      border: 2px solid #e60012;
      border-radius: 0;
      overflow: hidden;
      background: #ffffff;
      box-shadow: 0 22px 52px rgba(0, 0, 0, .18);
    }
    .chat-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      padding: 12px 14px;
      background: #e60012;
      color: #ffffff;
    }
    .chat-title {
      margin: 0;
      color: #ffffff;
      font-size: 15px;
      font-weight: 900;
      line-height: 1.15;
    }
    .chat-close {
      width: 24px;
      height: 24px;
      display: grid;
      place-items: center;
      background: rgba(255, 255, 255, .16);
      color: #ffffff;
      font-weight: 900;
      line-height: 1;
    }
    .chat-response {
      min-height: 250px;
      max-height: 330px;
      overflow-y: auto;
      margin-top: 0;
      padding: 16px;
      border: 0;
      background: #ffffff;
      color: #111111;
      font-size: 14px;
      line-height: 1.62;
      white-space: pre-wrap;
      box-shadow: none;
    }
    .chat-response:empty::before {
      color: #8a8a8a;
      content: "";
    }
    div[data-testid="stForm"] {
      border: 0;
      border-radius: 0;
      background: transparent;
      padding: 0;
      box-shadow: none;
    }
    div[data-testid="stForm"] textarea {
      min-height: 128px !important;
      border-radius: 0 !important;
      border: 1px solid #111111 !important;
      font-size: 15px !important;
      line-height: 1.55 !important;
      box-shadow: none !important;
    }
    [data-testid="stMetric"] {
      padding: 18px 18px 16px;
      border: 1px solid #e4e4e4;
      background: #ffffff;
      box-shadow: 0 12px 34px rgba(0, 0, 0, .06);
    }
    [data-testid="stMetricLabel"] {
      color: #555555;
      font-weight: 800;
    }
    [data-testid="stMetricValue"] {
      color: #e60012;
      font-weight: 900;
    }
    div[data-baseweb="tab-list"] {
      gap: 28px;
      border-bottom: 1px solid #d8d8d8;
    }
    button[data-baseweb="tab"] {
      min-height: 58px;
      border: 0;
      border-bottom: 3px solid transparent;
      border-radius: 0;
      background: transparent;
      color: #111111;
      font-weight: 900;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
      border-bottom-color: #e60012;
      background: transparent;
      color: #e60012;
    }
    button[data-baseweb="tab"] p {
      margin: 0;
      line-height: 1.12;
    }
    .stButton > button {
      border: 1px solid #e60012;
      border-radius: 0;
      background: #e60012;
      color: #ffffff;
      font-weight: 900;
    }
    .stButton > button:hover {
      border-color: #111111;
      background: #111111;
      color: #ffffff;
    }
    .stDataFrame {
      border: 1px solid #ececec;
      background: #ffffff;
    }
    @media (max-width: 760px) {
      .hero h1 {
        font-size: 36px;
      }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

if not data_ready():
    st.warning("Demo data files are missing. Please verify that the required CSV files exist in the data directory.")
    st.stop()

if "site_lang" not in st.session_state:
    st.session_state["site_lang"] = "ja"

st.markdown('<div class="language-strip">Website Language</div>', unsafe_allow_html=True)
spacer, lang_en_col, lang_ja_col, lang_ko_col = st.columns([6, 1, 1, 1])
with lang_en_col:
    if st.button("English" + (" ✓" if st.session_state["site_lang"] == "en" else ""), use_container_width=True):
        st.session_state["site_lang"] = "en"
with lang_ja_col:
    if st.button("日本語" + (" ✓" if st.session_state["site_lang"] == "ja" else ""), use_container_width=True):
        st.session_state["site_lang"] = "ja"
with lang_ko_col:
    if st.button("한국어" + (" ✓" if st.session_state["site_lang"] == "ko" else ""), use_container_width=True):
        st.session_state["site_lang"] = "ko"

lang = st.session_state["site_lang"]
portfolio_label = tr(lang, "AI SCM Data Analysis Project", JP["portfolio"], "AI SCM 데이터 분석 프로젝트")
hero_title = tr(
    lang,
    "AI SCM Data Analysis Project",
    JP["hero_title"],
    "AI SCM Data Analysis Project",
)
hero_summary = tr(
    lang,
    "Demand forecasting, SKU-store-level ROP, safety stock, replenishment recommendations, and store-transfer decisions for modern global retail operations.",
    JP["summary"],
    "수요예측, SKU-매장별 ROP, 안전재고, 보충 추천, 매장 간 재고 이동을 통합한 SCM 의사결정 지원 시스템입니다.",
)
chat_title = tr(lang, "AI Chatbot", "AIチャットボット", "AI 챗봇")
question_label = tr(lang, "Live SCM question", JP["live_question"], "실시간 SCM 질문")
question_placeholder = tr(
    lang,
    "Ask about reorder actions, stockout risk, safety stock, or store transfers.",
    "再発注、欠品リスク、安全在庫、店舗間移動について質問してください。",
    "재발주, 결품 리스크, 안전재고, 매장 간 이동에 대해 질문하세요.",
)
track_label = tr(lang, "Track SCM", JP["track"], "SCM 추적")

tables = load_tables()
sales = tables["sales"]
products = tables["products"]
stores = tables["stores"]
policy = tables["policy"].merge(products[["sku_id", "product_name", "category"]], on="sku_id", how="left")
policy = policy.merge(stores[["store_id", "city", "store_type"]], on="store_id", how="left")
recs = tables["recommendations"].merge(products[["sku_id", "product_name", "category"]], on="sku_id", how="left")
forecast = tables["forecast"].merge(products[["sku_id", "product_name"]], on="sku_id", how="left")
transfers = tables["transfers"]
policy_results = tables["policy_results"]
policy_summary = tables["policy_summary"]
policy_segments = tables["policy_segments"]
policy_tests = tables["policy_tests"]

with st.sidebar:
    st.subheader(tr(lang, "Controls", JP["controls"], "컨트롤"))
    cities = ["All"] + sorted(policy["city"].dropna().unique().tolist())
    city = st.selectbox(tr(lang, "City", JP["city"], "도시"), cities)
    statuses = ["All"] + sorted(policy["stock_status"].dropna().unique().tolist())
    status = st.selectbox(tr(lang, "Stock status", JP["status"], "재고 상태"), statuses)

top_left, top_right = st.columns([1.45, 0.82], gap="large")

with top_left:
    st.markdown(
        f"""
        <div class="hero">
          <div class="hero-kicker">{portfolio_label}</div>
          <div class="portfolio-name">SCM Decision Support Dashboard</div>
          <h1>{hero_title}</h1>
          <p>{hero_summary}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with top_right:
    st.markdown(
        f"""
        <div class="chat-panel">
          <div class="chat-header">
            <div class="chat-title">{chat_title}</div>
            <div class="chat-close">x</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    with st.form("top_scm_chat"):
        top_question = st.text_area(
            question_label,
            placeholder=question_placeholder,
            height=208,
        )
        top_submitted = st.form_submit_button(track_label)
    if top_submitted and top_question.strip():
        st.session_state["top_chat_reply"] = ask_scm_agent(top_question, lang)
    response_box(st.session_state.get("top_chat_reply", ""))

view = policy.copy()
if city != "All":
    view = view[view["city"] == city]
if status != "All":
    view = view[view["stock_status"] == status]

col1, col2, col3, col4 = st.columns(4)
col1.metric(tr(lang, "SKU-store pairs", JP["pairs"], "SKU-매장 페어"), f"{len(view):,}")
col2.metric(tr(lang, "Stockout risks", JP["stockout"], "결품 리스크"), f"{(view['stock_status'] == 'Stockout Risk').sum():,}")
col3.metric(tr(lang, "Overstock cases", JP["overstock"], "과잉재고"), f"{(view['stock_status'] == 'Overstock').sum():,}")
col4.metric(tr(lang, "Recommended order units", JP["order_units"], "추천 발주 수량"), f"{int(recs['recommended_order_qty'].sum()):,}")

st.caption(
    "ROP = average daily demand x lead time + safety stock.\n"
    "Safety stock = demand standard deviation x Z-value x sqrt(lead time)."
)

tab_overview, tab_forecast, tab_inventory, tab_transfer, tab_ab, tab_agent = st.tabs(
    [
        tr(lang, "Overview", JP["overview"], "개요"),
        tr(lang, "Demand Forecast", JP["forecast"], "수요예측"),
        tr(lang, "ROP & Safety Stock", JP["rop"], "ROP 및 안전재고"),
        tr(lang, "Store Transfer", JP["transfer"], "매장 간 이동"),
        tr(lang, "Policy Eval", "政策比較", "Policy Eval"),
        tr(lang, "AI Agent", JP["agent"], "AI 에이전트"),
    ]
)

with tab_overview:
    left, right = st.columns(2)
    with left:
        status_count = view.groupby("stock_status", as_index=False).size()
        fig = px.bar(
            status_count,
            x="stock_status",
            y="size",
            color="stock_status",
            color_discrete_map=STATUS_COLORS,
            title=tr(lang, "Inventory Risk Distribution", JP["risk_dist"], "재고 리스크 분포"),
        )
        fig.update_layout(showlegend=False, height=380, paper_bgcolor="white", plot_bgcolor="white")
        st.plotly_chart(fig, use_container_width=True)
    with right:
        city_count = policy.groupby(["city", "stock_status"], as_index=False).size()
        fig = px.bar(
            city_count,
            x="city",
            y="size",
            color="stock_status",
            color_discrete_map=STATUS_COLORS,
            title=tr(lang, "Risk by City", JP["city_risk"], "도시별 리스크"),
        )
        fig.update_layout(height=380, paper_bgcolor="white", plot_bgcolor="white")
        st.plotly_chart(fig, use_container_width=True)

    st.subheader(tr(lang, "Top Replenishment Recommendations", JP["top_replenishment"], "우선 보충 추천"))
    st.dataframe(
        recs[recs["recommended_order_qty"] > 0][
            [
                "store_id",
                "sku_id",
                "product_name",
                "priority",
                "stock_on_hand",
                "rop",
                "safety_stock",
                "forecast_28d",
                "recommended_order_qty",
                "reason",
            ]
        ].head(12),
        use_container_width=True,
        hide_index=True,
    )

with tab_forecast:
    product_options = sorted(forecast["product_name"].dropna().unique().tolist())
    selected_product = st.selectbox(tr(lang, "Product", JP["product"], "상품"), product_options)
    product_forecast = forecast[forecast["product_name"] == selected_product]
    fig = px.line(
        product_forecast,
        x="date",
        y="forecast_units",
        color="store_id",
        color_discrete_sequence=STORE_COLORS,
        title=f"{tr(lang, '28-Day Forecast', '28日需要予測', '28일 수요예측')}: {selected_product}",
    )
    fig.update_layout(height=420, paper_bgcolor="white", plot_bgcolor="white")
    st.plotly_chart(fig, use_container_width=True)

    st.subheader(tr(lang, "Recent Sales Pattern", JP["recent_sales"], "최근 판매 패턴"))
    sku_id = products[products["product_name"] == selected_product]["sku_id"].iloc[0]
    recent_sales = sales[sales["sku_id"] == sku_id].merge(stores[["store_id", "city"]], on="store_id", how="left")
    fig = px.line(
        recent_sales.tail(5 * 60),
        x="date",
        y="units_sold",
        color="store_id",
        color_discrete_sequence=STORE_COLORS,
        title=tr(lang, "Historical Sales by Store", JP["sales_history"], "매장별 판매 이력"),
    )
    fig.update_layout(height=360, paper_bgcolor="white", plot_bgcolor="white")
    st.plotly_chart(fig, use_container_width=True)

with tab_inventory:
    st.subheader(tr(lang, "SKU-store-level ROP Policy", JP["policy"], "SKU-매장별 ROP 정책"))
    st.dataframe(
        view[
            [
                "city",
                "store_id",
                "product_name",
                "category",
                "avg_daily_demand",
                "std_daily_demand",
                "lead_time_days",
                "service_level",
                "safety_stock",
                "rop",
                "stock_on_hand",
                "days_of_supply",
                "stock_status",
            ]
        ].sort_values(["stock_status", "days_of_supply"]),
        use_container_width=True,
        hide_index=True,
    )

with tab_transfer:
    st.subheader(tr(lang, "Store-to-store Transfer Recommendations", JP["transfer_rec"], "매장 간 재고 이동 추천"))
    if transfers.empty:
        st.info(tr(lang, "No transfer recommendation available in the current scenario.", JP["no_transfer"], "현재 시나리오에서는 매장 간 이동 추천이 없습니다."))
    else:
        st.dataframe(transfers, use_container_width=True, hide_index=True)

with tab_ab:
    st.subheader("Offline Policy Evaluation: SCM KPI Comparison")
    st.caption(
        "Baseline = planner-style replenishment policy. Candidate = constrained AI-assisted replenishment plus limited store-transfer policy. "
        "This is a synthetic offline policy comparison, not a randomized production experiment."
    )
    st.info(
        "Interpretation note: p-values only evaluate paired differences under this synthetic simulation. "
        "They do not prove real-world causal impact; production rollout would require backtesting, pilot stores, constraints, and sensitivity checks."
    )
    st.caption(
        "日本語: ベースライン在庫運用と、制約付きAI補充推奨・店舗間移動施策を比較する、"
        "合成デモデータに基づくオフライン政策評価シミュレーションです。"
    )

    control = policy_summary[policy_summary["group"].str.contains("Baseline")].iloc[0]
    treatment = policy_summary[policy_summary["group"].str.contains("Candidate")].iloc[0]
    cost_reduction_pct = float(treatment["cost_reduction_vs_control_pct"]) * 100
    cost_reduction_jpy = float(control["total_scm_cost_jpy"] - treatment["total_scm_cost_jpy"])
    stockout_reduction_pp = float(control["stockout_rate"] - treatment["stockout_rate"]) * 100
    service_level_uplift_pp = float(treatment["service_level"] - control["service_level"]) * 100
    lost_sales_reduction_jpy = float(control["lost_sales_proxy_jpy"] - treatment["lost_sales_proxy_jpy"])

    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric("Total SCM cost proxy reduction", f"{cost_reduction_pct:.1f}%", f"-JPY {cost_reduction_jpy:,.0f}")
    kpi2.metric("Stockout-rate reduction", f"{stockout_reduction_pp:.1f} pp")
    kpi3.metric("Service-level uplift", f"{service_level_uplift_pp:.1f} pp")
    kpi4.metric("Lost-sales reduction", f"JPY {lost_sales_reduction_jpy:,.0f}")

    cost_fig = px.bar(
        policy_summary,
        x="group",
        y="total_scm_cost_jpy",
        color="group",
        color_discrete_sequence=[INK_BLACK, RETAIL_RED],
        title="Baseline vs Candidate: Total SCM Cost Proxy",
    )
    cost_fig.update_layout(showlegend=False, height=390, paper_bgcolor="white", plot_bgcolor="white")

    rate_long = policy_summary.melt(
        id_vars=["group"],
        value_vars=["stockout_rate", "service_level"],
        var_name="metric",
        value_name="rate",
    )
    rate_fig = px.bar(
        rate_long,
        x="metric",
        y="rate",
        color="group",
        barmode="group",
        color_discrete_sequence=[INK_BLACK, RETAIL_RED],
        title="Operational KPI Rate Comparison",
    )
    rate_fig.update_layout(height=390, paper_bgcolor="white", plot_bgcolor="white", yaxis_tickformat=".0%")

    left, right = st.columns(2)
    with left:
        st.plotly_chart(cost_fig, use_container_width=True)
    with right:
        st.plotly_chart(rate_fig, use_container_width=True)

    st.subheader("Hypothesis Test and p-value")
    st.caption(
        "Methodology: paired t-test for continuous KPI deltas and McNemar exact test for paired stockout outcomes. "
        "H0 means the AI-assisted candidate policy does not improve the KPI versus the baseline policy."
    )
    st.caption(
        "日本語: SKU・店舗ペアを同一単位として比較し、連続値KPIは対応のあるt検定、"
        "欠品有無はMcNemar正確検定でp値を算出しています。"
    )
    st.dataframe(
        policy_tests[
            [
                "metric",
                "null_hypothesis",
                "test",
                "sample_size",
                "mean_improvement",
                "confidence_interval_95",
                "effect_size",
                "test_statistic",
                "p_value_display",
                "significance_0_05",
                "business_interpretation",
            ]
        ],
        use_container_width=True,
        hide_index=True,
    )

    segment_cost = policy_segments.pivot_table(
        index=["city", "category"],
        columns="group",
        values="total_scm_cost_jpy",
        aggfunc="sum",
    ).reset_index()
    segment_cost["cost_reduction_jpy"] = (
        segment_cost["Baseline: planner policy"]
        - segment_cost["Candidate: constrained AI-assisted policy"]
    )
    segment_cost["cost_reduction_pct"] = (
        segment_cost["cost_reduction_jpy"] / segment_cost["Baseline: planner policy"].replace(0, pd.NA)
    )
    segment_cost = segment_cost.sort_values("cost_reduction_jpy", ascending=False)

    st.subheader("Where logistics should improve first")
    st.caption("改善優先領域: Cost-reduction drivers by city and product category.")
    driver_fig = px.bar(
        segment_cost.head(10),
        x="cost_reduction_jpy",
        y="city",
        color="category",
        orientation="h",
        title="Top Improvement Drivers by City and Category",
    )
    driver_fig.update_layout(height=440, paper_bgcolor="white", plot_bgcolor="white")
    st.plotly_chart(driver_fig, use_container_width=True)

    st.dataframe(
        segment_cost[["city", "category", "cost_reduction_jpy", "cost_reduction_pct"]].head(12),
        use_container_width=True,
        hide_index=True,
    )

    st.subheader("Offline Policy Evaluation Detail Table")
    st.dataframe(
        policy_results[
            [
                "group",
                "city",
                "store_id",
                "product_name",
                "category",
                "forecast_28d",
                "order_qty",
                "inbound_transfer_qty",
                "outbound_transfer_qty",
                "service_level",
                "lost_sales_units",
                "ending_inventory_units",
                "total_scm_cost_jpy",
            ]
        ].sort_values(["group", "total_scm_cost_jpy"], ascending=[True, False]).head(30),
        use_container_width=True,
        hide_index=True,
    )

with tab_agent:
    st.subheader(tr(lang, "SCM Manager Agent", JP["manager"], "SCM 매니저 에이전트"))
    st.write("Ask about reorder actions, safety stock, stockout risk, or store-transfer recommendations.")
    question = st.text_input(
        tr(lang, "Question", JP["question"], "질문"),
        placeholder=question_placeholder,
    )
    if st.button(tr(lang, "Ask SCM Agent", JP["ask_agent"], "SCM Agent에게 질문"), type="primary") and question.strip():
        st.markdown(ask_scm_agent(question, lang).replace("\n", "  \n"))
