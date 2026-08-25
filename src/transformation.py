"""
Data transformation utilities.

This module builds the analytical fact table by joining the cleaned
datasets and creating business-level metrics:

    - revenue, cost, profit, profit_margin
    - net_revenue (after returns)
    - order-level flags

The output is a single denormalized table (`fact_sales`) which is the
foundation for EDA and dashboarding.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def build_fact_sales(
    orders: pd.DataFrame,
    order_items: pd.DataFrame,
    products: pd.DataFrame,
    customers: pd.DataFrame,
    returns: pd.DataFrame,
) -> pd.DataFrame:
    """Return the unified fact table used for analysis."""

    # 1. Order_items + orders
    items = order_items.merge(orders, on="order_id", how="left", suffixes=("", "_order"))

    # 2. + products
    items = items.merge(
        products[["product_id", "product_name", "category", "sub_category",
                  "unit_cost", "unit_price", "launch_date"]],
        on="product_id", how="left", suffixes=("_sold", "_product"),
    )

    # 3. + customers
    items = items.merge(
        customers[["customer_id", "country", "region", "segment", "signup_date"]],
        on="customer_id", how="left", suffixes=("", "_customer"),
    )

    # 4. Aggregate returns per item
    returns_per_item = (
        returns.groupby("item_id", as_index=False)
        .agg(returned=("return_id", "count"),
             refund_amount=("refund_amount", "sum"))
    )

    items = items.merge(returns_per_item, on="item_id", how="left")
    items["returned"] = items["returned"].fillna(0).astype(int)
    items["refund_amount"] = items["refund_amount"].fillna(0.0)

    # 5. Choose canonical unit cost: prefer product unit_cost, fallback to sold price
    items["effective_unit_cost"] = items["unit_cost"].fillna(items["unit_price_sold"] * 0.6)

    # 6. Metrics
    items["gross_revenue"] = items["unit_price_sold"] * items["quantity"]
    items["discount_amount"] = items["gross_revenue"] * items["discount"]
    items["net_revenue"] = items["gross_revenue"] - items["discount_amount"]
    items["cost"] = items["effective_unit_cost"] * items["quantity"]
    items["profit"] = items["net_revenue"] - items["cost"]
    items["profit_margin"] = np.where(
        items["net_revenue"] != 0,
        items["profit"] / items["net_revenue"],
        0.0,
    )

    items["returned_flag"] = items["returned"].astype(bool)
    items["net_revenue_after_returns"] = items["net_revenue"] - items["refund_amount"]

    # 7. Date helpers
    items["order_date"] = pd.to_datetime(items["order_date"], errors="coerce")
    items["year"] = items["order_date"].dt.year
    items["month"] = items["order_date"].dt.month
    items["year_month"] = items["order_date"].dt.to_period("M").astype(str)
    items["quarter"] = items["order_date"].dt.quarter

    # 8. Status filter: only completed orders contribute to revenue/profit
    items["is_completed"] = items["status"].eq("Completed")

    return items


def aggregate_monthly(fact: pd.DataFrame) -> pd.DataFrame:
    completed = fact[fact["is_completed"]]
    g = (
        completed.groupby("year_month", as_index=False)
        .agg(revenue=("net_revenue", "sum"),
             profit=("profit", "sum"),
             orders=("order_id", "nunique"),
             units=("quantity", "sum"),
             customers=("customer_id", "nunique"))
    )
    return g.sort_values("year_month")


def aggregate_by_category(fact: pd.DataFrame) -> pd.DataFrame:
    completed = fact[fact["is_completed"]]
    g = (
        completed.groupby("category", as_index=False)
        .agg(revenue=("net_revenue", "sum"),
             profit=("profit", "sum"),
             units=("quantity", "sum"),
             orders=("order_id", "nunique"))
    )
    g["profit_margin"] = (g["profit"] / g["revenue"]).fillna(0)
    return g.sort_values("revenue", ascending=False)


def aggregate_by_region(fact: pd.DataFrame) -> pd.DataFrame:
    completed = fact[fact["is_completed"]]
    g = (
        completed.groupby("region", as_index=False)
        .agg(revenue=("net_revenue", "sum"),
             profit=("profit", "sum"),
             orders=("order_id", "nunique"),
             customers=("customer_id", "nunique"))
    )
    return g.sort_values("revenue", ascending=False)


def aggregate_by_channel(fact: pd.DataFrame) -> pd.DataFrame:
    completed = fact[fact["is_completed"]]
    g = (
        completed.groupby("channel", as_index=False)
        .agg(revenue=("net_revenue", "sum"),
             orders=("order_id", "nunique"),
             customers=("customer_id", "nunique"))
    )
    return g.sort_values("revenue", ascending=False)


def top_products(fact: pd.DataFrame, n: int = 20, by: str = "revenue") -> pd.DataFrame:
    completed = fact[fact["is_completed"]]
    g = (
        completed.groupby(["product_id", "product_name", "category"], as_index=False)
        .agg(revenue=("net_revenue", "sum"),
             profit=("profit", "sum"),
             units=("quantity", "sum"))
    )
    g["profit_margin"] = (g["profit"] / g["revenue"]).fillna(0)
    return g.sort_values(by, ascending=False).head(n).reset_index(drop=True)


def slow_moving_products(fact: pd.DataFrame, min_units: int = 5) -> pd.DataFrame:
    completed = fact[fact["is_completed"]]
    g = (
        completed.groupby(["product_id", "product_name", "category"], as_index=False)
        .agg(units=("quantity", "sum"),
             revenue=("net_revenue", "sum"),
             profit=("profit", "sum"))
    )
    return g[g["units"] <= min_units].sort_values("units").reset_index(drop=True)


def customer_rfm(fact: pd.DataFrame, snapshot_date: pd.Timestamp | None = None) -> pd.DataFrame:
    """Classic Recency / Frequency / Monetary table per customer."""
    completed = fact[fact["is_completed"]].copy()
    if snapshot_date is None:
        snapshot_date = completed["order_date"].max() + pd.Timedelta(days=1)

    g = (
        completed.groupby("customer_id", as_index=False)
        .agg(last_order=("order_date", "max"),
             frequency=("order_id", "nunique"),
             monetary=("net_revenue", "sum"))
    )
    g["recency"] = (snapshot_date - g["last_order"]).dt.days
    g = g.rename(columns={"monetary": "revenue"})
    return g[["customer_id", "recency", "frequency", "revenue", "last_order"]]


def rfm_segment(rfm: pd.DataFrame) -> pd.DataFrame:
    """Assign each customer to a simple RFM segment using quartiles."""

    def score_with_qcut(series, labels):
        """Bin a series into quartiles, returning integer scores.

        Falls back to the median bin if there aren't enough unique values.
        """
        try:
            return pd.qcut(series.rank(method="first"), 4,
                           labels=labels, duplicates="drop").astype(int)
        except (ValueError, IndexError):
            return pd.Series(2, index=rfm.index, dtype=int)

    rfm = rfm.copy()
    # Score each axis 1..4 (4 = best)
    # R: high score = low recency (recent purchase)
    rfm["R"] = score_with_qcut(rfm["recency"], labels=[4, 3, 2, 1])
    # F and M: high score = high frequency / high monetary value
    rfm["F"] = score_with_qcut(rfm["frequency"], labels=[1, 2, 3, 4])
    rfm["M"] = score_with_qcut(rfm["revenue"], labels=[1, 2, 3, 4])
    rfm["RFM_score"] = rfm["R"] * 100 + rfm["F"] * 10 + rfm["M"]

    def label(row):
        if row["R"] >= 3 and row["F"] >= 3 and row["M"] >= 3:
            return "Champions"
        if row["F"] >= 3 and row["M"] >= 3:
            return "Loyal Customers"
        if row["R"] >= 3 and row["M"] >= 3:
            return "Potential Loyalists"
        if row["R"] <= 2 and row["F"] <= 2:
            return "At Risk / Lost"
        if row["R"] >= 3 and row["F"] <= 2:
            return "Recent Customers"
        return "Others"

    rfm["segment"] = rfm.apply(label, axis=1)
    return rfm