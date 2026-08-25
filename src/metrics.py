"""
Business metrics helpers.

All metric functions accept a `fact_sales` DataFrame produced by
`transformation.build_fact_sales`. They are designed to be pure and
side-effect-free.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass
class KPISummary:
    revenue: float
    profit: float
    orders: int
    customers: int
    aov: float
    return_rate: float
    profit_margin: float

    def as_dict(self) -> dict:
        return {
            "Total Revenue": self.revenue,
            "Total Profit": self.profit,
            "Orders": self.orders,
            "Customers": self.customers,
            "Average Order Value": self.aov,
            "Return Rate": self.return_rate,
            "Profit Margin": self.profit_margin,
        }


def total_revenue(fact: pd.DataFrame) -> float:
    return float(fact.loc[fact["is_completed"], "net_revenue"].sum())


def total_profit(fact: pd.DataFrame) -> float:
    return float(fact.loc[fact["is_completed"], "profit"].sum())


def profit_margin(fact: pd.DataFrame) -> float:
    rev = total_revenue(fact)
    if rev == 0:
        return 0.0
    return total_profit(fact) / rev


def total_orders(fact: pd.DataFrame) -> int:
    return int(fact.loc[fact["is_completed"], "order_id"].nunique())


def total_customers(fact: pd.DataFrame) -> int:
    return int(fact.loc[fact["is_completed"], "customer_id"].nunique())


def average_order_value(fact: pd.DataFrame) -> float:
    orders = total_orders(fact)
    if orders == 0:
        return 0.0
    return total_revenue(fact) / orders


def return_rate(fact: pd.DataFrame) -> float:
    items_sold = fact[fact["is_completed"]].shape[0]
    if items_sold == 0:
        return 0.0
    returned = fact.loc[fact["is_completed"], "returned_flag"].sum()
    return float(returned / items_sold)


def customer_lifetime_value(rfm: pd.DataFrame) -> pd.DataFrame:
    """Append a CLV proxy column to an RFM table.

    CLV is approximated as: average order value * purchase frequency
    * expected lifespan (we use 3 years as a business assumption).
    """
    rfm = rfm.copy()
    rfm["aov"] = rfm["revenue"] / rfm["frequency"].replace(0, np.nan)
    rfm["aov"] = rfm["aov"].fillna(0)
    rfm["clv"] = rfm["aov"] * rfm["frequency"] * 3  # 3-year horizon
    return rfm


def kpi_summary(fact: pd.DataFrame) -> KPISummary:
    return KPISummary(
        revenue=total_revenue(fact),
        profit=total_profit(fact),
        orders=total_orders(fact),
        customers=total_customers(fact),
        aov=average_order_value(fact),
        return_rate=return_rate(fact),
        profit_margin=profit_margin(fact),
    )
