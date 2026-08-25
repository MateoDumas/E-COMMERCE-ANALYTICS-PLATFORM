"""End-to-end verification of the analytical pipeline."""

import importlib
import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# 1. Import check
for m in ["src.cleaning", "src.transformation", "src.metrics", "src.analysis"]:
    try:
        importlib.import_module(m)
        print("OK   ", m)
    except Exception:
        traceback.print_exc()
        sys.exit(1)

# 2. End-to-end run
import pandas as pd
from src.cleaning import (
    clean_customers, clean_products, clean_orders,
    clean_order_items, clean_returns,
)
from src.transformation import build_fact_sales, customer_rfm, rfm_segment
from src.metrics import kpi_summary, customer_lifetime_value
from src.analysis import (
    category_revenue_vs_profit_share, high_volume_low_margin,
    low_volume_products, monthly_seasonality, pareto_products,
)

RAW = ROOT / "data" / "raw"

customers = clean_customers(pd.read_csv(RAW / "customers.csv"))
products  = clean_products(pd.read_csv(RAW / "products.csv"))
orders    = clean_orders(pd.read_csv(RAW / "orders.csv"))
items     = clean_order_items(pd.read_csv(RAW / "order_items.csv"))
returns   = clean_returns(pd.read_csv(RAW / "returns.csv"))
print("Cleaned shapes:", customers.shape, products.shape, orders.shape,
      items.shape, returns.shape)

fact = build_fact_sales(orders, items, products, customers, returns)
print("Fact shape:", fact.shape)

kpis = kpi_summary(fact)
print("KPI:", kpis.as_dict())

cat = category_revenue_vs_profit_share(fact)
print("Category shares:")
print(cat[["category", "revenue_share", "profit_share"]].round(3).to_string(index=False))

hvl = high_volume_low_margin(fact, top_n=5)
print("HVM products:", len(hvl))

rl = low_volume_products(fact, max_units=5)
print("Slow movers:", len(rl))

season = monthly_seasonality(fact)
print("Months in seasonality:", season.shape[0])

pareto, cutoff = pareto_products(fact, top_pct=0.20)
print(f"Pareto: top {cutoff} products -> "
      f"{pareto.iloc[:cutoff]['cum_pct'].iloc[-1]:.1%} of revenue")

# RFM + CLV
rfm = rfm_segment(customer_rfm(fact))
rfm = customer_lifetime_value(rfm)
print("RFM segments:", rfm["segment"].value_counts().to_dict())
print("Avg CLV:", round(rfm["clv"].mean(), 2))

print("ALL CHECKS PASSED")
