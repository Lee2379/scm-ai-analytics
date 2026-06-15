from __future__ import annotations

from pathlib import Path

import pandas as pd


TRANSFER_COST_PER_UNIT = 120
ORDER_HANDLING_COST_PER_UNIT = 40
HOLDING_COST_RATE_28D = 0.015


def load_inputs(data_dir: str | Path) -> dict[str, pd.DataFrame]:
    data_dir = Path(data_dir)
    return {
        "policy": pd.read_csv(data_dir / "inventory_policy.csv"),
        "recommendations": pd.read_csv(data_dir / "recommendations.csv"),
        "forecast": pd.read_csv(data_dir / "forecast.csv"),
        "products": pd.read_csv(data_dir / "products.csv"),
        "stores": pd.read_csv(data_dir / "stores.csv"),
        "transfers": pd.read_csv(data_dir / "transfer_recommendations.csv"),
    }


def _transfer_adjustments(transfers: pd.DataFrame) -> pd.DataFrame:
    if transfers.empty:
        return pd.DataFrame(columns=["store_id", "sku_id", "inbound_transfer_qty", "outbound_transfer_qty"])

    inbound = (
        transfers.groupby(["to_store", "sku_id"], as_index=False)["transfer_qty"]
        .sum()
        .rename(columns={"to_store": "store_id", "transfer_qty": "inbound_transfer_qty"})
    )
    outbound = (
        transfers.groupby(["from_store", "sku_id"], as_index=False)["transfer_qty"]
        .sum()
        .rename(columns={"from_store": "store_id", "transfer_qty": "outbound_transfer_qty"})
    )
    return inbound.merge(outbound, on=["store_id", "sku_id"], how="outer").fillna(0)


def _evaluate_policy(df: pd.DataFrame, group: str, order_col: str, transfer_enabled: bool) -> pd.DataFrame:
    result = df.copy()
    if transfer_enabled:
        result["inbound_transfer_qty"] = result["inbound_transfer_qty"].fillna(0)
        result["outbound_transfer_qty"] = result["outbound_transfer_qty"].fillna(0)
    else:
        result["inbound_transfer_qty"] = 0
        result["outbound_transfer_qty"] = 0

    result["group"] = group
    result["order_qty"] = result[order_col].clip(lower=0)
    result["available_units"] = (
        result["stock_on_hand"]
        + result["order_qty"]
        + result["inbound_transfer_qty"]
        - result["outbound_transfer_qty"]
    ).clip(lower=0)
    result["fulfilled_units"] = result[["available_units", "forecast_28d"]].min(axis=1)
    result["lost_sales_units"] = (result["forecast_28d"] - result["fulfilled_units"]).clip(lower=0)
    result["ending_inventory_units"] = (result["available_units"] - result["forecast_28d"]).clip(lower=0)
    result["service_level"] = result["fulfilled_units"] / result["forecast_28d"].replace(0, pd.NA)
    result["stockout_flag"] = result["lost_sales_units"] > 0
    result["ending_days_of_supply"] = result["ending_inventory_units"] / result["avg_daily_demand"].replace(0, pd.NA)
    result["overstock_flag"] = result["ending_days_of_supply"] > 42

    result["lost_sales_proxy_jpy"] = result["lost_sales_units"] * result["unit_price"]
    result["holding_cost_jpy"] = result["ending_inventory_units"] * result["unit_price"] * HOLDING_COST_RATE_28D
    result["order_handling_cost_jpy"] = result["order_qty"] * ORDER_HANDLING_COST_PER_UNIT
    result["transfer_cost_jpy"] = (
        result["inbound_transfer_qty"] + result["outbound_transfer_qty"]
    ) * TRANSFER_COST_PER_UNIT
    result["total_scm_cost_jpy"] = (
        result["lost_sales_proxy_jpy"]
        + result["holding_cost_jpy"]
        + result["order_handling_cost_jpy"]
        + result["transfer_cost_jpy"]
    )
    return result


def build_ab_test_outputs(data_dir: str | Path) -> dict[str, pd.DataFrame]:
    data_dir = Path(data_dir)
    inputs = load_inputs(data_dir)

    forecast_28d = (
        inputs["forecast"].groupby(["store_id", "sku_id"], as_index=False)["forecast_units"]
        .sum()
        .rename(columns={"forecast_units": "forecast_28d"})
    )
    transfer_adj = _transfer_adjustments(inputs["transfers"])

    base = (
        inputs["policy"]
        .merge(forecast_28d, on=["store_id", "sku_id"], how="left")
        .merge(
            inputs["recommendations"][["store_id", "sku_id", "recommended_order_qty", "priority", "risk_score"]],
            on=["store_id", "sku_id"],
            how="left",
        )
        .merge(transfer_adj, on=["store_id", "sku_id"], how="left")
        .merge(inputs["products"][["sku_id", "product_name", "category", "unit_price"]], on="sku_id", how="left")
        .merge(inputs["stores"][["store_id", "city", "store_type"]], on="store_id", how="left")
    )
    base["forecast_28d"] = base["forecast_28d"].fillna(0)
    base["recommended_order_qty"] = base["recommended_order_qty"].fillna(0)
    base["priority"] = base["priority"].fillna("Monitor")
    base["risk_score"] = base["risk_score"].fillna(0)
    base["control_order_qty"] = (base["rop"] - base["stock_on_hand"]).clip(lower=0).round()

    control = _evaluate_policy(base, "Control: baseline ROP policy", "control_order_qty", transfer_enabled=False)
    treatment = _evaluate_policy(base, "Treatment: AI recommendation policy", "recommended_order_qty", transfer_enabled=True)
    results = pd.concat([control, treatment], ignore_index=True)

    metric_summary = (
        results.groupby("group", as_index=False)
        .agg(
            experimental_units=("sku_id", "count"),
            stockout_rate=("stockout_flag", "mean"),
            overstock_rate=("overstock_flag", "mean"),
            service_level=("service_level", "mean"),
            lost_sales_units=("lost_sales_units", "sum"),
            lost_sales_proxy_jpy=("lost_sales_proxy_jpy", "sum"),
            holding_cost_jpy=("holding_cost_jpy", "sum"),
            order_handling_cost_jpy=("order_handling_cost_jpy", "sum"),
            transfer_cost_jpy=("transfer_cost_jpy", "sum"),
            total_scm_cost_jpy=("total_scm_cost_jpy", "sum"),
        )
        .round(3)
    )

    control_cost = metric_summary.loc[
        metric_summary["group"] == "Control: baseline ROP policy", "total_scm_cost_jpy"
    ].iloc[0]
    treatment_cost = metric_summary.loc[
        metric_summary["group"] == "Treatment: AI recommendation policy", "total_scm_cost_jpy"
    ].iloc[0]
    metric_summary["cost_delta_vs_control_jpy"] = metric_summary["total_scm_cost_jpy"] - control_cost
    metric_summary["cost_reduction_vs_control_pct"] = (
        (control_cost - metric_summary["total_scm_cost_jpy"]) / control_cost
    ).round(4)

    segment_summary = (
        results.groupby(["group", "city", "category"], as_index=False)
        .agg(
            experimental_units=("sku_id", "count"),
            stockout_rate=("stockout_flag", "mean"),
            service_level=("service_level", "mean"),
            lost_sales_units=("lost_sales_units", "sum"),
            total_scm_cost_jpy=("total_scm_cost_jpy", "sum"),
        )
        .round(3)
    )

    results = results.round(
        {
            "forecast_28d": 1,
            "available_units": 1,
            "fulfilled_units": 1,
            "lost_sales_units": 1,
            "ending_inventory_units": 1,
            "service_level": 4,
            "ending_days_of_supply": 1,
            "lost_sales_proxy_jpy": 0,
            "holding_cost_jpy": 0,
            "order_handling_cost_jpy": 0,
            "transfer_cost_jpy": 0,
            "total_scm_cost_jpy": 0,
        }
    )

    results.to_csv(data_dir / "ab_test_results.csv", index=False)
    metric_summary.to_csv(data_dir / "ab_test_kpi_summary.csv", index=False)
    segment_summary.to_csv(data_dir / "ab_test_segment_summary.csv", index=False)
    return {
        "ab_results": results,
        "ab_kpi_summary": metric_summary,
        "ab_segment_summary": segment_summary,
    }


if __name__ == "__main__":
    build_ab_test_outputs(Path(__file__).resolve().parents[1] / "data")
