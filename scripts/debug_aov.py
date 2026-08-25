"""Debug AOV - check raw revenue calculation."""

import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import pandas as pd
from src.cleaning import (clean_customers, clean_products, clean_orders,
                         clean_order_items, clean_returns)
from src.transformation import build_fact_sales

RAW = ROOT / "data" / "raw"

customers = clean_customers(pd.read_csv(RAW / "customers.csv"))
products  = clean_products(pd.read_csv(RAW / "products.csv"))
orders    = clean_orders(pd.read_csv(RAW / "orders.csv"))
items     = clean_order_items(pd.read_csv(RAW / "order_items.csv"))
returns   = clean_returns(pd.read_csv(RAW / "returns.csv"))

print("Items after clean:", items.shape)
print("Items price stats:")
print(items["unit_price"].describe())
print("Items quantity stats:")
print(items["quantity"].describe())
print("Items discount stats:")
print(items["discount"].describe())

fact = build_fact_sales(orders, items, products, customers, returns)
c = fact[fact["is_completed"]]
print("\nFact (completed):")
print(c[["quantity", "discount", "unit_price_sold", "gross_revenue", "net_revenue"]].describe())

# Revenue per order (line level)
per_order = c.groupby("order_id").agg(rev=("net_revenue", "sum"), lines=("item_id", "count"))
print("\nPer-order:")
print(per_order.describe())

# So per-order average is around $700+ because discount isn't applied at order-level aggregation but we set discount=0.5 randomly across items...
print("Total net_revenue:", c["net_revenue"].sum())
print("Unique orders:", c["order_id"].nunique())
