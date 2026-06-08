from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.scm_engine import build_all_outputs


STORE_ROWS = [
    ("TOKYO_01", "Tokyo", 35.6812, 139.7671, "Flagship"),
    ("TOKYO_02", "Tokyo", 35.6895, 139.6917, "Urban"),
    ("YOKOHAMA_01", "Yokohama", 35.4437, 139.6380, "Urban"),
    ("OSAKA_01", "Osaka", 34.6937, 135.5023, "Flagship"),
    ("FUKUOKA_01", "Fukuoka", 33.5902, 130.4017, "Urban"),
]

PRODUCT_ROWS = [
    ("SKU_HT_001", "HEATTECH Crew Neck", "Innerwear", "Winter", 1290),
    ("SKU_HT_002", "HEATTECH Turtleneck", "Innerwear", "Winter", 1990),
    ("SKU_AR_001", "AIRism Cotton T-Shirt", "Innerwear", "Summer", 1490),
    ("SKU_AR_002", "AIRism Hoodie", "Outerwear", "Summer", 2990),
    ("SKU_DN_001", "Ultra Stretch Jeans", "Bottoms", "All-season", 3990),
    ("SKU_DN_002", "Wide Fit Jeans", "Bottoms", "All-season", 3990),
    ("SKU_SH_001", "Oxford Shirt", "Shirts", "All-season", 2990),
    ("SKU_SH_002", "Linen Blend Shirt", "Shirts", "Summer", 2990),
    ("SKU_OUT_001", "Light Down Jacket", "Outerwear", "Winter", 6990),
    ("SKU_OUT_002", "Blocktech Parka", "Outerwear", "Rain", 5990),
    ("SKU_KN_001", "Merino Knit", "Knitwear", "Winter", 3990),
    ("SKU_KN_002", "Cotton Cardigan", "Knitwear", "Spring", 2990),
]


def fetch_open_meteo(city: str, lat: float, lon: float, start: str, end: str) -> pd.DataFrame | None:
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start,
        "end_date": end,
        "daily": "temperature_2m_mean,precipitation_sum",
        "timezone": "Asia/Tokyo",
    }
    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        daily = response.json()["daily"]
        return pd.DataFrame(
            {
                "date": pd.to_datetime(daily["time"]),
                "city": city,
                "temperature": daily["temperature_2m_mean"],
                "precipitation": daily["precipitation_sum"],
            }
        )
    except Exception:
        return None


def synthetic_weather(dates: pd.DatetimeIndex, stores: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, store in stores.iterrows():
        city_shift = {"Tokyo": 0, "Yokohama": 0.4, "Osaka": 1.2, "Fukuoka": 2.0}.get(store.city, 0)
        for i, date in enumerate(dates):
            seasonal = 18 + 10 * np.sin((date.dayofyear - 80) / 365 * 2 * np.pi)
            rows.append(
                {
                    "date": date,
                    "city": store.city,
                    "temperature": round(seasonal + city_shift + np.random.normal(0, 2.2), 1),
                    "precipitation": round(max(0, np.random.gamma(1.2, 2.0) - 1.5), 1),
                }
            )
    return pd.DataFrame(rows).drop_duplicates(["date", "city"])


def make_calendar(dates: pd.DatetimeIndex) -> pd.DataFrame:
    calendar = pd.DataFrame({"date": dates})
    calendar["dow"] = calendar["date"].dt.dayofweek
    calendar["is_weekend"] = calendar["dow"].isin([5, 6]).astype(int)
    calendar["month"] = calendar["date"].dt.month
    calendar["is_golden_week"] = (
        (calendar["date"].dt.month == 5) & (calendar["date"].dt.day.between(1, 7))
    ).astype(int)
    calendar["is_year_end"] = (
        (calendar["date"].dt.month == 12) & (calendar["date"].dt.day >= 24)
    ).astype(int)
    calendar["is_holiday_like"] = (
        (calendar["is_weekend"] == 1)
        | (calendar["is_golden_week"] == 1)
        | (calendar["is_year_end"] == 1)
    ).astype(int)
    return calendar


def build_demo_data(data_dir: Path, use_open_meteo: bool = False) -> None:
    rng = np.random.default_rng(42)
    np.random.seed(42)
    data_dir.mkdir(parents=True, exist_ok=True)

    dates = pd.date_range("2025-01-01", periods=180, freq="D")
    stores = pd.DataFrame(STORE_ROWS, columns=["store_id", "city", "lat", "lon", "store_type"])
    products = pd.DataFrame(PRODUCT_ROWS, columns=["sku_id", "product_name", "category", "season", "unit_price"])
    calendar = make_calendar(dates)

    if use_open_meteo:
        weather_parts = [
            fetch_open_meteo(row.city, row.lat, row.lon, str(dates.min().date()), str(dates.max().date()))
            for _, row in stores.drop_duplicates("city").iterrows()
        ]
        weather_parts = [part for part in weather_parts if part is not None]
        weather = pd.concat(weather_parts, ignore_index=True) if weather_parts else synthetic_weather(dates, stores)
    else:
        weather = synthetic_weather(dates, stores)

    rows = []
    for _, store in stores.iterrows():
        store_scale = 1.25 if store.store_type == "Flagship" else 1.0
        if store.city == "Tokyo":
            store_scale += 0.15
        city_weather = weather[weather["city"] == store.city]
        for _, product in products.iterrows():
            base = rng.uniform(7, 28) * store_scale
            for date in dates:
                cal = calendar[calendar["date"] == date].iloc[0]
                w = city_weather[city_weather["date"] == date].iloc[0]
                season_factor = 1.0
                if product.season == "Winter" and w.temperature < 12:
                    season_factor = 1.75
                elif product.season == "Summer" and w.temperature > 24:
                    season_factor = 1.65
                elif product.season == "Rain" and w.precipitation > 4:
                    season_factor = 1.55
                elif product.season == "Spring" and 12 <= w.temperature <= 22:
                    season_factor = 1.25
                promo = 1 if rng.random() < 0.08 else 0
                holiday_factor = 1.22 if cal.is_holiday_like else 1.0
                promo_factor = 1.45 if promo else 1.0
                demand = base * season_factor * holiday_factor * promo_factor
                units = max(0, int(rng.normal(demand, max(2.0, demand * 0.18))))
                rows.append(
                    {
                        "date": date,
                        "store_id": store.store_id,
                        "sku_id": product.sku_id,
                        "units_sold": units,
                        "unit_price": product.unit_price,
                        "promotion": promo,
                        "temperature": w.temperature,
                        "precipitation": w.precipitation,
                        "is_holiday_like": int(cal.is_holiday_like),
                    }
                )

    sales = pd.DataFrame(rows)
    latest = sales[sales["date"] > dates.max() - pd.Timedelta(days=28)]
    avg = latest.groupby(["store_id", "sku_id"], as_index=False)["units_sold"].mean()
    avg["stock_on_hand"] = (avg["units_sold"] * rng.uniform(2.0, 52.0, size=len(avg))).round().astype(int)
    avg.loc[avg.sample(frac=0.22, random_state=7).index, "stock_on_hand"] = (
        avg["units_sold"] * rng.uniform(1.0, 4.0, size=len(avg))
    ).round().astype(int)
    inventory = avg.assign(date=dates.max())[["date", "store_id", "sku_id", "stock_on_hand"]]

    supply = avg[["store_id", "sku_id"]].copy()
    supply["lead_time_days"] = rng.choice([3, 5, 7, 10, 14], size=len(supply), p=[0.16, 0.24, 0.32, 0.18, 0.10])
    supply["service_level"] = rng.choice([0.90, 0.95, 0.97], size=len(supply), p=[0.18, 0.62, 0.20])
    supply["supplier_region"] = rng.choice(["Japan DC", "East Asia", "Global Supplier"], size=len(supply), p=[0.45, 0.35, 0.20])

    stores.to_csv(data_dir / "stores.csv", index=False)
    products.to_csv(data_dir / "products.csv", index=False)
    weather.to_csv(data_dir / "weather.csv", index=False)
    calendar.to_csv(data_dir / "calendar.csv", index=False)
    sales.to_csv(data_dir / "sales.csv", index=False)
    inventory.to_csv(data_dir / "inventory.csv", index=False)
    supply.to_csv(data_dir / "supply.csv", index=False)
    build_all_outputs(data_dir)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build demo SCM data and calculated outputs.")
    parser.add_argument("--data-dir", default=str(ROOT / "data"))
    parser.add_argument("--use-open-meteo", action="store_true")
    args = parser.parse_args()
    build_demo_data(Path(args.data_dir), use_open_meteo=args.use_open_meteo)
    print(f"Demo SCM data written to {args.data_dir}")


if __name__ == "__main__":
    main()
