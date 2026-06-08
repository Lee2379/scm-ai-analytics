from __future__ import annotations

import os
from pathlib import Path

import pandas as pd


GEMINI_MODEL = "gemini-3.5-flash"


def load_agent_tables(data_dir: str | Path) -> dict[str, pd.DataFrame]:
    data_dir = Path(data_dir)
    return {
        "policy": pd.read_csv(data_dir / "inventory_policy.csv"),
        "recommendations": pd.read_csv(data_dir / "recommendations.csv"),
        "transfers": pd.read_csv(data_dir / "transfer_recommendations.csv"),
        "products": pd.read_csv(data_dir / "products.csv"),
        "stores": pd.read_csv(data_dir / "stores.csv"),
    }


def gemini_ready() -> bool:
    return bool(os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY"))


def build_scm_context(tables: dict[str, pd.DataFrame]) -> str:
    policy = tables["policy"]
    recs = tables["recommendations"]
    transfers = tables["transfers"]
    products = tables["products"]
    stores = tables["stores"]

    product_names = products.set_index("sku_id")["product_name"].to_dict()
    store_cities = stores.set_index("store_id")["city"].to_dict()

    top_reorders = recs[recs["recommended_order_qty"] > 0].sort_values(
        ["priority", "risk_score"], ascending=[True, False]
    ).head(8)
    top_risks = policy[policy["stock_status"] == "Stockout Risk"].sort_values("days_of_supply").head(8)
    top_safety = policy.sort_values("safety_stock", ascending=False).head(6)
    top_transfers = transfers.head(6)

    lines = [
        "SCM LIVE DATA SNAPSHOT",
        f"- SKU-store pairs monitored: {len(policy)}",
        f"- Stockout risks: {int((policy['stock_status'] == 'Stockout Risk').sum())}",
        f"- Overstock cases: {int((policy['stock_status'] == 'Overstock').sum())}",
        f"- Total recommended order units: {int(recs['recommended_order_qty'].sum())}",
        f"- Store-transfer recommendations: {len(transfers)}",
        "",
        "INVENTORY POLICY FORMULAS",
        "- ROP = average daily demand x lead time + safety stock.",
        "- Safety stock = demand standard deviation x Z-value x sqrt(lead time).",
        "",
        "TOP REORDER ACTIONS",
    ]

    if top_reorders.empty:
        lines.append("- No immediate reorder action is required.")
    for _, row in top_reorders.iterrows():
        lines.append(
            "- "
            f"{row.store_id} ({store_cities.get(row.store_id, '')}) / "
            f"{product_names.get(row.sku_id, row.sku_id)}: "
            f"priority={row.priority}, stock={row.stock_on_hand:.0f}, ROP={row.rop:.0f}, "
            f"safety_stock={row.safety_stock:.0f}, forecast_28d={row.forecast_28d:.0f}, "
            f"recommended_order_qty={int(row.recommended_order_qty)}."
        )

    lines.extend(["", "HIGHEST STOCKOUT RISKS"])
    if top_risks.empty:
        lines.append("- No current stockout risk.")
    for _, row in top_risks.iterrows():
        lines.append(
            "- "
            f"{row.store_id} ({store_cities.get(row.store_id, '')}) / "
            f"{product_names.get(row.sku_id, row.sku_id)}: "
            f"days_of_supply={row.days_of_supply:.1f}, stock={row.stock_on_hand:.0f}, "
            f"ROP={row.rop:.0f}, lead_time_days={row.lead_time_days:.0f}."
        )

    lines.extend(["", "HIGHEST SAFETY STOCK REQUIREMENTS"])
    for _, row in top_safety.iterrows():
        lines.append(
            "- "
            f"{row.store_id} / {product_names.get(row.sku_id, row.sku_id)}: "
            f"safety_stock={row.safety_stock:.0f}, service_level={row.service_level:.0%}, "
            f"std_daily_demand={row.std_daily_demand:.1f}."
        )

    lines.extend(["", "STORE TRANSFER RECOMMENDATIONS"])
    if top_transfers.empty:
        lines.append("- No current store transfer recommendation.")
    for _, row in top_transfers.iterrows():
        lines.append(
            "- "
            f"{row.from_store} ({row.from_city}) -> {row.to_store} ({row.to_city}): "
            f"{int(row.transfer_qty)} units of {row.product_name}."
        )

    return "\n".join(lines)


def local_agent_reply(question: str, tables: dict[str, pd.DataFrame], lang: str = "ja") -> str:
    q = question.lower()
    context = build_scm_context(tables)
    reorder_terms = [
        "rop",
        "sku",
        "reorder",
        "order",
        "replenish",
        "priority",
        "prioritize",
        "\u518d\u767a\u6ce8",
        "\u767a\u6ce8",
        "\u88dc\u5145",
        "\u512a\u5148",
        "\uc7ac\uc8fc\ubb38",
        "\ubc1c\uc8fc",
        "\uc6b0\uc120",
    ]
    if any(k in q for k in reorder_terms):
        return _format_reorder_answer(tables, lang)
    if any(k in q for k in ["safety", "safety stock"]):
        return _reply(_section(context, "HIGHEST SAFETY STOCK REQUIREMENTS"))
    if any(k in q for k in ["transfer", "store"]):
        return _reply(_section(context, "STORE TRANSFER RECOMMENDATIONS"))
    if any(k in q for k in ["risk", "stockout"]):
        return _reply(_section(context, "HIGHEST STOCKOUT RISKS"))
    return _reply(_section(context, "SCM LIVE DATA SNAPSHOT"))


def gemini_reply_if_configured(question: str, context: str, lang: str = "ja") -> str | None:
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        return None

    try:
        from google import genai
        from google.genai import types
    except ImportError:
        return None

    language = {"ja": "Japanese", "en": "English", "ko": "Korean"}.get(lang, "Japanese")
    system_instruction = (
        "You are a cutting-edge SCM AI Agent for the AI SCM Data Analysis Project. "
        "You track live SCM dashboard data and answer as a business-ready supply chain analyst. "
        "Use only the supplied context. Do not invent numbers. "
        "When answering reorder-priority questions, do NOT dump the raw data. "
        "Structure the answer as: 1) one-sentence conclusion, 2) top 3 priority SKU-store actions, "
        "3) decision logic, 4) recommended next action. "
        "Use short bullets and explain stock, ROP, forecast demand, and order quantity in plain language. "
        "Keep answers concise, executive-friendly, readable, and specific."
    )
    prompt = (
        f"Preferred response language: {language}\n\n"
        f"{context}\n\n"
        f"User question:\n{question}"
    )

    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.25,
                thinking_config=types.ThinkingConfig(thinking_level="low"),
            ),
        )
        return response.text
    except Exception as exc:
        return f"Gemini connection failed. Showing local SCM context fallback.\n\n{context}\n\nError: {exc}"


def _section(context: str, start_title: str) -> str:
    lines = context.splitlines()
    try:
        start = lines.index(start_title)
    except ValueError:
        return context
    collected = []
    for line in lines[start:]:
        if collected and line.isupper() and not line.startswith("-"):
            break
        collected.append(line)
    return "\n".join(collected)


def _reply(text: str) -> str:
    return text


def _format_reorder_answer(tables: dict[str, pd.DataFrame], lang: str) -> str:
    recs = tables["recommendations"]
    products = tables["products"]
    stores = tables["stores"]
    product_names = products.set_index("sku_id")["product_name"].to_dict()
    store_cities = stores.set_index("store_id")["city"].to_dict()
    top = recs[recs["recommended_order_qty"] > 0].sort_values(
        ["priority", "risk_score"], ascending=[True, False]
    ).head(3)

    if top.empty:
        return _reply("No urgent reorder is required. Current inventory is above ROP for the monitored SKU-store pairs.")

    if lang == "ja":
        lines = [
            "結論: 優先的に再発注すべきSKUは、在庫がROPを大きく下回り、28日需要予測に対して補充不足が大きいものです。",
            "",
            "優先再発注リスト",
        ]
        for i, (_, row) in enumerate(top.iterrows(), 1):
            product = product_names.get(row.sku_id, row.sku_id)
            city = store_cities.get(row.store_id, "")
            lines.append(
                f"{i}. {product} / {row.store_id} ({city})\n"
                f"   - 推奨発注数: {int(row.recommended_order_qty)} units\n"
                f"   - 現在在庫: {row.stock_on_hand:.0f}, ROP: {row.rop:.0f}, 28日需要予測: {row.forecast_28d:.0f}"
            )
        lines.extend(
            [
                "",
                "判断ロジック",
                "- 現在在庫がROPを下回るSKUを優先します。",
                "- ROPは「日平均需要 x リードタイム + 安全在庫」で計算します。",
                "- 推奨発注数は、28日需要予測と安全在庫を満たすために不足している数量です。",
                "",
                "次のアクション: 上位3SKUは欠品リスクが高いため、まず発注処理または近隣店舗からの在庫移動を検討してください。",
            ]
        )
        return _reply("\n".join(lines))

    lines = [
        "Conclusion: reorder priority should go to SKU-store pairs where current stock is far below ROP and the 28-day demand forecast is not covered.",
        "",
        "Top reorder priorities",
    ]
    for i, (_, row) in enumerate(top.iterrows(), 1):
        product = product_names.get(row.sku_id, row.sku_id)
        city = store_cities.get(row.store_id, "")
        lines.append(
            f"{i}. {product} / {row.store_id} ({city})\n"
            f"   - Recommended order: {int(row.recommended_order_qty)} units\n"
            f"   - Current stock: {row.stock_on_hand:.0f}, ROP: {row.rop:.0f}, 28-day forecast: {row.forecast_28d:.0f}"
        )
    lines.extend(
        [
            "",
            "Decision logic",
            "- Prioritize SKUs where current stock is below ROP.",
            "- ROP is calculated as average daily demand x lead time + safety stock.",
            "- Order quantity covers the 28-day forecast plus safety stock gap.",
            "",
            "Next action: execute replenishment for the top 3 items first, or check store-transfer options if overstock exists nearby.",
        ]
    )
    return _reply("\n".join(lines))
