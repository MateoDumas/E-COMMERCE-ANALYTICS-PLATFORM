"""
Higher-level analytical helpers.

Used by the EDA and Business Analysis notebooks and by the dashboard.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def category_revenue_vs_profit_share(fact: pd.DataFrame) -> pd.DataFrame:
    """Return a per-category DataFrame with revenue/profit totals and shares."""
    completed = fact[fact["is_completed"]]
    g = (
        completed.groupby("category", as_index=False)
        .agg(revenue=("net_revenue", "sum"),
             profit=("profit", "sum"),
             units=("quantity", "sum"),
             orders=("order_id", "nunique"))
    )
    total_rev = g["revenue"].sum()
    total_profit = g["profit"].sum()
    g["revenue_share"] = g["revenue"] / total_rev if total_rev else 0
    g["profit_share"] = g["profit"] / total_profit if total_profit else 0
    g["profit_margin"] = np.where(g["revenue"] != 0, g["profit"] / g["revenue"], 0)
    return g.sort_values("revenue", ascending=False).reset_index(drop=True)


def high_volume_low_margin(fact: pd.DataFrame, top_n: int = 10) -> pd.DataFrame:
    """Products with high sales but low profit margin."""
    completed = fact[fact["is_completed"]]
    g = (
        completed.groupby(["product_id", "product_name", "category"], as_index=False)
        .agg(revenue=("net_revenue", "sum"),
             profit=("profit", "sum"),
             units=("quantity", "sum"),
             discount=("discount", "mean"))
    )
    g["profit_margin"] = np.where(g["revenue"] != 0, g["profit"] / g["revenue"], 0)
    revenue_threshold = g["revenue"].quantile(0.75)
    return g[(g["revenue"] >= revenue_threshold) & (g["profit_margin"] < 0.15)] \
        .sort_values("revenue", ascending=False) \
        .head(top_n) \
        .reset_index(drop=True)


def low_volume_products(fact: pd.DataFrame, max_units: int = 5) -> pd.DataFrame:
    completed = fact[fact["is_completed"]]
    g = (
        completed.groupby(["product_id", "product_name", "category"], as_index=False)
        .agg(units=("quantity", "sum"),
             revenue=("net_revenue", "sum"),
             profit=("profit", "sum"))
    )
    return g[g["units"] <= max_units].sort_values("units").reset_index(drop=True)


def monthly_seasonality(fact: pd.DataFrame) -> pd.DataFrame:
    completed = fact[fact["is_completed"]].copy()
    completed["month"] = completed["order_date"].dt.month
    g = (
        completed.groupby("month", as_index=False)
        .agg(revenue=("net_revenue", "sum"),
             profit=("profit", "sum"),
             orders=("order_id", "nunique"))
    )
    return g


def return_analysis(fact: pd.DataFrame, returns: pd.DataFrame) -> pd.DataFrame:
    """Return rate and refund value per category."""
    completed = fact[fact["is_completed"]].copy()
    cat_items = completed.groupby("category").size().rename("items_sold")
    returned = completed[completed["returned_flag"]].groupby("category").size().rename("items_returned")
    df = pd.concat([cat_items, returned], axis=1).fillna(0)
    df["return_rate"] = df["items_returned"] / df["items_sold"]
    refund = returns.groupby("item_id")["refund_amount"].sum()
    return df


def correlation_matrix(fact: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    return fact[columns].corr(numeric_only=True)


def new_vs_returning(fact: pd.DataFrame) -> pd.DataFrame:
    completed = fact[fact["is_completed"]].copy()
    first_order = completed.groupby("customer_id")["order_date"].min().rename("first_order")
    completed = completed.join(first_order, on="customer_id")
    completed["is_new"] = completed["order_date"] == completed["first_order"]
    g = (
        completed.assign(period=completed["order_date"].dt.to_period("M").astype(str))
        .groupby(["period", "is_new"], as_index=False)
        .agg(revenue=("net_revenue", "sum"),
             orders=("order_id", "nunique"))
    )
    return g


def pareto_products(fact: pd.DataFrame, top_pct: float = 0.20) -> pd.DataFrame:
    """Compute cumulative revenue contribution per product (Pareto)."""
    completed = fact[fact["is_completed"]]
    g = (
        completed.groupby("product_id", as_index=False)
        .agg(product_name=("product_name", "first"),
             category=("category", "first"),
             revenue=("net_revenue", "sum"))
        .sort_values("revenue", ascending=False)
        .reset_index(drop=True)
    )
    total = g["revenue"].sum()
    g["cum_revenue"] = g["revenue"].cumsum()
    g["cum_pct"] = g["cum_revenue"] / total if total else 0
    cutoff = int(len(g) * top_pct)
    return g, cutoff
