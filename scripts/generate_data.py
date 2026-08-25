"""
Synthetic data generator for the E-Commerce Analytics Platform.

This script produces five CSV files with realistic business distributions:
- Heavy-tailed product demand (Pareto 80/20)
- Realistic margins (10-40% by category)
- Seasonal patterns (Q4 spike)
- Category-specific return rates
- Customer segments with different CLV

Deliberately polluted with real-world quality issues.
"""

from __future__ import annotations

import os
import random
from datetime import datetime, timedelta

import numpy as np
import pandas as pd


SEED = 42
random.seed(SEED)
np.random.seed(SEED)

RAW_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
RAW_DIR = os.path.abspath(RAW_DIR)
os.makedirs(RAW_DIR, exist_ok=True)

START_DATE = datetime(2022, 1, 1)
END_DATE = datetime(2024, 12, 31)
TOTAL_DAYS = (END_DATE - START_DATE).days

CATEGORY_CONFIG = {
    "Electronics": {"weight": 0.20, "cost_range": (30, 300), "margin_range": (0.15, 0.28), "return_rate": 0.08, "season_boost": {10: 1.5, 11: 1.6, 12: 1.8, 1: 1.1}},
    "Clothing": {"weight": 0.18, "cost_range": (10, 80), "margin_range": (0.35, 0.55), "return_rate": 0.18, "season_boost": {11: 1.3, 12: 1.4, 4: 1.2, 5: 1.2}},
    "Home & Kitchen": {"weight": 0.15, "cost_range": (15, 120), "margin_range": (0.25, 0.40), "return_rate": 0.06, "season_boost": {11: 1.4, 12: 1.5, 1: 1.1}},
    "Sports & Outdoors": {"weight": 0.12, "cost_range": (12, 150), "margin_range": (0.30, 0.45), "return_rate": 0.07, "season_boost": {4: 1.3, 5: 1.3, 6: 1.2, 7: 1.2}},
    "Books": {"weight": 0.10, "cost_range": (5, 25), "margin_range": (0.40, 0.55), "return_rate": 0.04, "season_boost": {11: 1.3, 12: 1.4, 8: 1.1}},
    "Beauty": {"weight": 0.08, "cost_range": (8, 60), "margin_range": (0.45, 0.65), "return_rate": 0.12, "season_boost": {11: 1.2, 12: 1.3}},
    "Toys & Games": {"weight": 0.10, "cost_range": (8, 80), "margin_range": (0.25, 0.40), "return_rate": 0.09, "season_boost": {11: 2.0, 12: 2.2, 1: 1.1}},
    "Office Supplies": {"weight": 0.07, "cost_range": (3, 40), "margin_range": (0.30, 0.50), "return_rate": 0.05, "season_boost": {8: 1.2, 9: 1.2}},
}

REGIONS = ["North", "South", "East", "West", "Central"]
REGION_WEIGHTS = [0.25, 0.20, 0.22, 0.18, 0.15]
PAYMENT_METHODS = ["Credit Card", "Debit Card", "PayPal", "Bank Transfer", "Cash on Delivery"]
PAYMENT_WEIGHTS = [0.45, 0.25, 0.18, 0.07, 0.05]
CHANNELS = ["Web", "Mobile App", "Marketplace"]
CHANNEL_WEIGHTS = [0.55, 0.30, 0.15]
SEGMENTS = ["Consumer", "Corporate", "Home Office"]
SEGMENT_WEIGHTS = [0.65, 0.20, 0.15]
RETURN_REASONS = ["Damaged", "Wrong Item", "Not as Described", "Late Delivery", "Changed Mind"]
REASON_WEIGHTS = [0.25, 0.15, 0.30, 0.15, 0.15]

rng = np.random.default_rng(SEED)


def random_date() -> datetime:
    return START_DATE + timedelta(days=int(rng.integers(0, TOTAL_DAYS)))


def seasonal_date(category: str) -> datetime:
    """Fast seasonality: pick a month with weighted probability."""
    cfg = CATEGORY_CONFIG.get(category, {})
    months = list(range(1, 13))
    weights = [cfg.get("season_boost", {}).get(m, 1.0) for m in months]
    total = sum(weights)
    probs = [w / total for w in weights]
    month = rng.choice(months, p=probs)
    day = int(rng.integers(1, 28))
    year = int(rng.integers(2022, 2025))
    return datetime(year, month, day)


def build_products(n: int = 500) -> pd.DataFrame:
    rows = []
    cat_list = list(CATEGORY_CONFIG.keys())
    cat_weights = [CATEGORY_CONFIG[c]["weight"] for c in cat_list]

    for i in range(1, n + 1):
        cat = rng.choice(cat_list, p=cat_weights)
        cfg = CATEGORY_CONFIG[cat]
        cost = rng.uniform(*cfg["cost_range"])
        margin = rng.uniform(*cfg["margin_range"])
        price = cost / (1 - margin)
        popularity = max(1, min(int(rng.zipf(1.5)), 1000))

        rows.append({
            "product_id": f"PROD-{i:05d}",
            "product_name": f"{cat.split()[0]} {rng.choice(['Pro','Max','Ultra','Plus','Lite','Standard'])} {i:03d}",
            "category": cat,
            "sub_category": rng.choice(["Premium", "Standard", "Budget", "Essential"], p=[0.15, 0.5, 0.25, 0.1]),
            "unit_cost": round(cost, 2),
            "unit_price": round(price, 2),
            "launch_date": random_date(),
            "stock_units": int(rng.integers(0, 2000)),
            "_popularity": popularity,
        })
    df = pd.DataFrame(rows)
    df["_pop_weight"] = df["_popularity"] / df["_popularity"].sum()

    # Issues
    dup = df.sample(30, random_state=SEED + 100)
    df = pd.concat([df, dup], ignore_index=True)
    df.loc[df.sample(20, random_state=SEED + 101).index, "category"] = np.nan
    cat_map = {
        "Electronics": rng.choice(["Electronics", "ELECTRONICS", "electronic", "Elec."]),
        "Clothing": rng.choice(["Clothing", "CLOTHING", "cloth", "Apparel"]),
        "Books": rng.choice(["Books", "BOOKS", "book", "Reading"]),
    }
    df["category"] = df["category"].map(lambda v: cat_map.get(v, v) if isinstance(v, str) else v)
    df.loc[df.sample(12, random_state=SEED + 102).index, "unit_cost"] = -df.loc[df.sample(12, random_state=SEED + 102).index, "unit_cost"]
    df.loc[df.sample(10, random_state=SEED + 103).index, "unit_price"] = -df.loc[df.sample(10, random_state=SEED + 103).index, "unit_price"]
    df.loc[df.sample(6, random_state=SEED + 104).index, "unit_price"] = df.loc[df.sample(6, random_state=SEED + 104).index, "unit_price"] * rng.uniform(20, 80, size=6)
    df.loc[df.sample(50, random_state=SEED + 105).index, "product_name"] = "  " + df.loc[df.sample(50, random_state=SEED + 105).index, "product_name"] + "  "
    return df


def build_customers(n: int = 6000) -> pd.DataFrame:
    first_names = ["Ana", "Luis", "Maria", "John", "Sofia", "Carlos", "Emma", "David", "Laura", "Pedro", "Marta", "James", "Lucia", "Diego", "Olivia", "Mateo", "Valentina", "Sebastian", "Camila", "Andres", "Isabella", "Santiago", "Victoria", "Gabriel", "Martina", "Alejandro"]
    last_names = ["Gomez", "Smith", "Garcia", "Lopez", "Martinez", "Brown", "Davis", "Rodriguez", "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson", "White", "Harris"]
    countries = ["USA", "Canada", "Mexico", "Brazil", "UK", "Germany", "Spain", "France", "Italy", "Australia"]

    rows = []
    for i in range(1, n + 1):
        rows.append({
            "customer_id": f"CUST-{i:06d}",
            "first_name": rng.choice(first_names),
            "last_name": rng.choice(last_names),
            "email": f"{rng.choice(first_names).lower()}.{rng.choice(last_names).lower()}{rng.integers(1, 9999)}@example.com",
            "phone": f"+1-{rng.integers(200, 999)}-{rng.integers(200, 999)}-{rng.integers(1000, 9999)}",
            "signup_date": random_date(),
            "country": rng.choice(countries),
            "region": rng.choice(REGIONS, p=REGION_WEIGHTS),
            "segment": rng.choice(SEGMENTS, p=SEGMENT_WEIGHTS),
        })
    df = pd.DataFrame(rows)
    dup = df.sample(100, random_state=SEED + 110)
    df = pd.concat([df, dup], ignore_index=True)
    df.loc[df.sample(150, random_state=SEED + 111).index, "email"] = np.nan
    df.loc[df.sample(180, random_state=SEED + 112).index, "phone"] = np.nan
    df.loc[df.sample(80, random_state=SEED + 113).index, "region"] = np.nan
    df.loc[df.sample(250, random_state=SEED + 114).index, "first_name"] = df.loc[df.sample(250, random_state=SEED + 114).index, "first_name"].str.upper()
    df.loc[df.sample(220, random_state=SEED + 115).index, "last_name"] = " " + df.loc[df.sample(220, random_state=SEED + 115).index, "last_name"] + "  "
    df["region"] = df["region"].replace({"North": "north ", "South": " SOUTH", "East": "EAST", "West": "west", "Central": "CENTRAL"})
    for idx in df.sample(40, random_state=SEED + 116).index:
        df.loc[idx, "signup_date"] = END_DATE + timedelta(days=int(rng.integers(10, 400)))
    return df


def build_orders(customer_ids: list[str], products: pd.DataFrame, n: int = 30000) -> pd.DataFrame:
    pop_weights = products.drop_duplicates("product_id")["_pop_weight"].values
    pop_weights = pop_weights / pop_weights.sum()
    product_ids = products.drop_duplicates("product_id")["product_id"].values

    rows = []
    for i in range(1, n + 1):
        cust = rng.choice(customer_ids)
        cat = rng.choice(list(CATEGORY_CONFIG.keys()), p=[CATEGORY_CONFIG[c]["weight"] for c in CATEGORY_CONFIG])
        rows.append({
            "order_id": f"ORD-{i:07d}",
            "customer_id": cust,
            "order_date": seasonal_date(cat),
            "payment_method": rng.choice(PAYMENT_METHODS, p=PAYMENT_WEIGHTS),
            "channel": rng.choice(CHANNELS, p=CHANNEL_WEIGHTS),
            "region": rng.choice(REGIONS, p=REGION_WEIGHTS),
            "status": rng.choice(["Completed", "Pending", "Cancelled", "Refunded"], p=[0.88, 0.06, 0.04, 0.02]),
        })
    df = pd.DataFrame(rows)
    df.loc[df.sample(60, random_state=SEED + 120).index, "customer_id"] = np.nan
    sample_idx = df.sample(400, random_state=SEED + 121).index
    formats = ["%d/%m/%Y", "%m-%d-%Y", "%Y.%m.%d", "%d-%b-%Y", "%Y-%m-%d %H:%M:%S"]
    for fmt in formats:
        sub = df.loc[sample_idx].sample(frac=0.2, random_state=SEED + 122)
        df.loc[sub.index, "order_date"] = pd.to_datetime(sub["order_date"]).dt.strftime(fmt)
    df["region"] = df["region"].replace({"North": "north ", "South": " SOUTH"})
    pay_map = {
        "Credit Card": rng.choice(["Credit Card", "credit card", "CC", "CREDIT CARD"]),
        "Debit Card": rng.choice(["Debit Card", "debit card", "DC"]),
        "PayPal": rng.choice(["PayPal", "paypal", "PAYPAL"]),
        "Bank Transfer": rng.choice(["Bank Transfer", "bank_transfer", "Bank Transfer "]),
        "Cash on Delivery": rng.choice(["Cash on Delivery", "COD", "cod"]),
    }
    df["payment_method"] = df["payment_method"].map(lambda v: pay_map.get(v, v))
    df["status"] = df["status"].replace({"Completed": rng.choice(["Completed", "complete", "COMPLETE"])})
    df.loc[df.sample(50, random_state=SEED + 123).index, "order_date"] = (END_DATE + timedelta(days=int(rng.integers(30, 200)))).strftime("%Y-%m-%d")
    dup = df.sample(200, random_state=SEED + 124)
    df = pd.concat([df, dup], ignore_index=True)
    return df


def build_order_items(orders: pd.DataFrame, products: pd.DataFrame, n: int = 90000) -> pd.DataFrame:
    order_ids = orders["order_id"].dropna().unique().tolist()
    prod_unique = products.drop_duplicates("product_id")
    pop_weights = prod_unique["_pop_weight"].values
    pop_weights = pop_weights / pop_weights.sum()
    product_ids = prod_unique["product_id"].values
    prod_info = prod_unique.set_index("product_id")[["unit_price", "unit_cost", "category"]].to_dict("index")

    rows = []
    for i in range(1, n + 1):
        oid = rng.choice(order_ids)
        pid = rng.choice(product_ids, p=pop_weights)
        info = prod_info.get(pid, {})
        base_price = info.get("unit_price", rng.uniform(10, 200))
        cat = info.get("category", "Electronics")

        qty = int(rng.choice([1, 2, 3, 4, 5, 6, 10, 20], p=[0.45, 0.25, 0.12, 0.08, 0.05, 0.02, 0.02, 0.01]))
        cat_cfg = CATEGORY_CONFIG.get(cat, {})
        avg_disc = 0.05 if cat_cfg.get("margin_range", (0.3, 0.5))[0] < 0.3 else 0.12
        discount = max(0, min(0.45, rng.normal(avg_disc, 0.08)))
        unit_price = round(base_price * rng.uniform(0.95, 1.05), 2)

        rows.append({
            "item_id": f"ITEM-{i:08d}",
            "order_id": oid,
            "product_id": pid,
            "quantity": qty,
            "discount": round(discount, 2),
            "unit_price": unit_price,
        })
    df = pd.DataFrame(rows)
    df.loc[df.sample(250, random_state=SEED + 130).index, "product_id"] = np.nan
    df.loc[df.sample(200, random_state=SEED + 131).index, "order_id"] = np.nan
    df.loc[df.sample(80, random_state=SEED + 132).index, "quantity"] = -df.loc[df.sample(80, random_state=SEED + 132).index, "quantity"]
    df.loc[df.sample(50, random_state=SEED + 133).index, "unit_price"] = 0
    df.loc[df.sample(30, random_state=SEED + 134).index, "unit_price"] = -df.loc[df.sample(30, random_state=SEED + 134).index, "unit_price"]
    df.loc[df.sample(100, random_state=SEED + 135).index, "discount"] = rng.uniform(1.1, 5.0, 100)
    df.loc[df.sample(60, random_state=SEED + 136).index, "discount"] = -rng.uniform(0.1, 0.8, 60)
    df.loc[df.sample(25, random_state=SEED + 137).index, "quantity"] = rng.integers(100, 2000, 25)
    dup = df.sample(300, random_state=SEED + 138)
    df = pd.concat([df, dup], ignore_index=True)
    return df


def build_returns(order_items: pd.DataFrame) -> pd.DataFrame:
    eligible = order_items.dropna(subset=["item_id"]).drop_duplicates("item_id")
    n_returns = int(len(eligible) * 0.08)
    sampled = eligible.sample(n_returns, random_state=SEED + 140)

    rows = []
    for _, row in sampled.iterrows():
        order_date = random_date()
        return_date = order_date + timedelta(days=int(rng.integers(1, 45)))
        reason = rng.choice(RETURN_REASONS, p=REASON_WEIGHTS)
        qty = max(1, row["quantity"])
        price = row["unit_price"]
        refund = round(price * qty * (1 - row["discount"]), 2)
        rows.append({
            "return_id": f"RET-{len(rows) + 1:06d}",
            "item_id": row["item_id"],
            "order_id": row["order_id"],
            "return_date": return_date,
            "reason": reason,
            "refund_amount": refund,
        })
    df = pd.DataFrame(rows)
    df.loc[df.sample(50, random_state=SEED + 141).index, "reason"] = np.nan
    df.loc[df.sample(30, random_state=SEED + 142).index, "refund_amount"] = -df.loc[df.sample(30, random_state=SEED + 142).index, "refund_amount"]
    reason_map = {
        "Damaged": rng.choice(["Damaged", "DAMAGED", "damaged", "dmg"]),
        "Wrong Item": rng.choice(["Wrong Item", "wrong_item", "WrongItem"]),
        "Not as Described": rng.choice(["Not as Described", "NAD", "not as described"]),
    }
    df["reason"] = df["reason"].map(lambda v: reason_map.get(v, v) if isinstance(v, str) else v)
    df.loc[df.sample(20, random_state=SEED + 143).index, "return_date"] = END_DATE + timedelta(days=int(rng.integers(20, 180)))
    dup = df.sample(40, random_state=SEED + 144)
    df = pd.concat([df, dup], ignore_index=True)
    return df


def main() -> None:
    print("Generating realistic synthetic e-commerce data (intentionally messy)...")
    products = build_products(500)
    customers = build_customers(6000)
    customer_ids = customers["customer_id"].dropna().unique().tolist()
    orders = build_orders(customer_ids, products, 30000)
    items = build_order_items(orders, products, 90000)
    returns = build_returns(items)

    for col in ["_popularity", "_pop_weight"]:
        if col in products.columns:
            products = products.drop(columns=[col])

    products.to_csv(os.path.join(RAW_DIR, "products.csv"), index=False)
    customers.to_csv(os.path.join(RAW_DIR, "customers.csv"), index=False)
    orders.to_csv(os.path.join(RAW_DIR, "orders.csv"), index=False)
    items.to_csv(os.path.join(RAW_DIR, "order_items.csv"), index=False)
    returns.to_csv(os.path.join(RAW_DIR, "returns.csv"), index=False)

    print(f"  -> customers.csv     ({len(customers):,} rows)")
    print(f"  -> products.csv      ({len(products):,} rows)")
    print(f"  -> orders.csv        ({len(orders):,} rows)")
    print(f"  -> order_items.csv   ({len(items):,} rows)")
    print(f"  -> returns.csv       ({len(returns):,} rows)")
    print(f"Saved to {RAW_DIR}")


if __name__ == "__main__":
    main()