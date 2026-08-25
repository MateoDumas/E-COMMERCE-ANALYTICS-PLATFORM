"""Run the full pipeline: clean -> transform -> persist outputs.

Populates data/processed (cleaned CSVs) and data/final (analytical tables)
mirroring notebooks 02 and 03.
"""

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.cleaning import (
    clean_customers, clean_products, clean_orders,
    clean_order_items, clean_returns,
)
from src.transformation import (
    build_fact_sales, aggregate_monthly, aggregate_by_category,
    aggregate_by_region, aggregate_by_channel, top_products,
    customer_rfm, rfm_segment,
)
from src.metrics import customer_lifetime_value

RAW = ROOT / "data" / "raw"
PROC = ROOT / "data" / "processed"
FINAL = ROOT / "data" / "final"
PROC.mkdir(parents=True, exist_ok=True)
FINAL.mkdir(parents=True, exist_ok=True)


def main() -> None:
    customers = clean_customers(pd.read_csv(RAW / "customers.csv"))
    products = clean_products(pd.read_csv(RAW / "products.csv"))
    orders = clean_orders(pd.read_csv(RAW / "orders.csv"))
    items = clean_order_items(pd.read_csv(RAW / "order_items.csv"))
    returns = clean_returns(pd.read_csv(RAW / "returns.csv"))

    # data/processed
    customers.to_csv(PROC / "customers.csv", index=False)
    products.to_csv(PROC / "products.csv", index=False)
    orders.to_csv(PROC / "orders.csv", index=False)
    items.to_csv(PROC / "order_items.csv", index=False)
    returns.to_csv(PROC / "returns.csv", index=False)
    print("Saved cleaned files to", PROC)

    # data/final
    fact = build_fact_sales(orders, items, products, customers, returns)
    fact.to_csv(FINAL / "fact_sales.csv", index=False)

    aggregate_monthly(fact).to_csv(FINAL / "monthly_summary.csv", index=False)
    aggregate_by_category(fact).to_csv(FINAL / "category_summary.csv", index=False)
    aggregate_by_region(fact).to_csv(FINAL / "region_summary.csv", index=False)
    aggregate_by_channel(fact).to_csv(FINAL / "channel_summary.csv", index=False)
    top_products(fact, n=20, by="revenue").to_csv(FINAL / "top_products.csv", index=False)

    rfm = rfm_segment(customer_rfm(fact))
    rfm = customer_lifetime_value(rfm)
    rfm.to_csv(FINAL / "rfm_segments.csv", index=False)

    print("Saved final tables to", FINAL)


if __name__ == "__main__":
    main()