"""
Data cleaning utilities.

All functions are **deterministic** so that the cleaning pipeline produces
the same output on every run (important for reproducibility).

Each function returns a NEW DataFrame; none of them mutate the input.
"""

from __future__ import annotations

import re
from typing import Iterable

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Generic helpers
# ---------------------------------------------------------------------------
def strip_whitespace(df: pd.DataFrame, columns: Iterable[str]) -> pd.DataFrame:
    """Trim leading/trailing whitespace and collapse internal double-spaces."""
    df = df.copy()
    for col in columns:
        if col in df.columns and df[col].dtype == object:
            df[col] = (
                df[col]
                .astype(str)
                .str.strip()
                .str.replace(r"\s+", " ", regex=True)
            )
            df.loc[df[col].isin(["nan", "None", "NaN", ""]), col] = np.nan
    return df


def normalize_case(df: pd.DataFrame, columns: Iterable[str], case: str = "title") -> pd.DataFrame:
    df = df.copy()
    for col in columns:
        if col not in df.columns:
            continue
        if case == "title":
            df[col] = df[col].astype(str).str.title()
        elif case == "lower":
            df[col] = df[col].astype(str).str.lower()
        elif case == "upper":
            df[col] = df[col].astype(str).str.upper()
    return df


def drop_duplicates_keep_first(df: pd.DataFrame, subset: list[str] | None = None) -> pd.DataFrame:
    """Drop exact duplicates, keeping the first occurrence."""
    return df.drop_duplicates(subset=subset, keep="first").reset_index(drop=True)


# ---------------------------------------------------------------------------
# Customers
# ---------------------------------------------------------------------------
def clean_customers(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # 1. Trim strings
    df = strip_whitespace(df, ["first_name", "last_name", "email", "country", "region", "segment"])

    # 2. Normalize case
    df = normalize_case(df, ["first_name", "last_name"], case="title")
    df = normalize_case(df, ["country"], case="title")

    # 3. Region: collapse inconsistent labels
    region_map = {
        "North": "North", "NORTH": "North", "north": "North", "north ": "North", " North": "North",
        "South": "South", "SOUTH": "South", "south": "South", " SOUTH": "South",
        "East": "East", "EAST": "East", "east": "East",
        "West": "West", "WEST": "West", "west": "West",
        "Central": "Central", "CENTRAL": "Central", "central": "Central",
    }
    df["region"] = df["region"].map(lambda v: region_map.get(v, v) if isinstance(v, str) else v)
    df["region"] = df["region"].fillna("Unknown")

    # 4. Segment: canonical values
    df["segment"] = df["segment"].astype(str).str.strip().str.title()
    df["segment"] = df["segment"].replace({"Nan": np.nan, "None": np.nan})
    df["segment"] = df["segment"].fillna("Consumer")

    # 5. Email validation / reconstruction
    df["email"] = df["email"].astype(str).str.lower().str.strip()
    bad = ~df["email"].str.contains(r"^[\w\.-]+@[\w\.-]+\.\w+$", na=True)
    df.loc[bad, "email"] = np.nan

    # 6. Dates: signup_date must be <= END_DATE
    df["signup_date"] = pd.to_datetime(df["signup_date"], errors="coerce")
    cutoff = pd.Timestamp("2024-12-31")
    df.loc[df["signup_date"] > cutoff, "signup_date"] = np.nan

    # 7. Deduplicate (keep first)
    df = drop_duplicates_keep_first(df)

    return df


# ---------------------------------------------------------------------------
# Products
# ---------------------------------------------------------------------------
def clean_products(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # 1. Trim whitespace
    df = strip_whitespace(df, ["product_name", "category", "sub_category"])

    # 2. Canonicalize categories
    cat_map = {
        "Electronics": "Electronics", "ELECTRONICS": "Electronics", "electronic": "Electronics", "Elec.": "Electronics",
        "Clothing": "Clothing", "CLOTHING": "Clothing", "cloth": "Clothing",
        "Home & Kitchen": "Home & Kitchen", "HOME & KITCHEN": "Home & Kitchen",
        "Sports & Outdoors": "Sports & Outdoors", "SPORTS & OUTDOORS": "Sports & Outdoors",
        "Books": "Books", "BOOKS": "Books", "book": "Books",
        "Beauty": "Beauty", "BEAUTY": "Beauty",
        "Toys & Games": "Toys & Games", "TOYS & GAMES": "Toys & Games",
        "Office Supplies": "Office Supplies", "OFFICE SUPPLIES": "Office Supplies",
    }
    df["category"] = df["category"].map(lambda v: cat_map.get(v, v) if isinstance(v, str) else v)
    df["category"] = df["category"].fillna("Uncategorized")

    # 3. Sub-category
    df["sub_category"] = df["sub_category"].astype(str).str.title().str.strip()
    df["sub_category"] = df["sub_category"].replace({"Nan": np.nan, "None": np.nan})
    df["sub_category"] = df["sub_category"].fillna("Standard")

    # 4. Numeric sanity: cost, price, stock
    for col in ["unit_cost", "unit_price", "stock_units"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Replace negatives with NaN, then impute with median by category
    df.loc[df["unit_cost"] <= 0, "unit_cost"] = np.nan
    df.loc[df["unit_price"] <= 0, "unit_price"] = np.nan
    df.loc[df["stock_units"] < 0, "stock_units"] = 0

    # Cap extreme outliers (anything above 99th percentile) -> 99th percentile
    for col in ["unit_cost", "unit_price"]:
        p99 = df[col].quantile(0.99)
        df.loc[df[col] > p99 * 2, col] = p99  # very aggressive outliers only

    # Median imputation within category
    df["unit_cost"] = df.groupby("category")["unit_cost"].transform(lambda s: s.fillna(s.median()))
    df["unit_price"] = df.groupby("category")["unit_price"].transform(lambda s: s.fillna(s.median()))

    # If margin <= 0, force price = cost * 1.5
    bad_margin = df["unit_price"] <= df["unit_cost"]
    df.loc[bad_margin, "unit_price"] = df.loc[bad_margin, "unit_cost"] * 1.5

    # 5. Dates
    df["launch_date"] = pd.to_datetime(df["launch_date"], errors="coerce")

    # 6. Dedup
    df = drop_duplicates_keep_first(df)

    return df


# ---------------------------------------------------------------------------
# Orders
# ---------------------------------------------------------------------------
def clean_orders(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # 1. Trim
    df = strip_whitespace(df, ["payment_method", "channel", "region", "status"])

    # 2. Normalize region (same map as customers)
    region_map = {
        "North": "North", "north": "North", " North": "North", "north ": "North",
        "South": "South", "south": "South", " SOUTH": "South",
        "East": "East", "east": "East",
        "West": "West", "west": "West",
        "Central": "Central", "central": "Central",
    }
    df["region"] = df["region"].astype(str).str.strip()
    df["region"] = df["region"].map(lambda v: region_map.get(v, v.title()) if isinstance(v, str) else v)
    df["region"] = df["region"].fillna("Unknown")

    # 3. Payment method normalization
    pay_map = {
        "Credit Card": "Credit Card", "credit card": "Credit Card", "cc": "Credit Card",
        "Debit Card": "Debit Card", "debit card": "Debit Card", "dc": "Debit Card",
        "Paypal": "PayPal", "paypal": "PayPal", "PayPal": "PayPal", "PAYPAL": "PayPal",
        "Bank Transfer": "Bank Transfer", "bank_transfer": "Bank Transfer",
        "Cash On Delivery": "Cash on Delivery", "cod": "Cash on Delivery",
        "Cash on Delivery": "Cash on Delivery",
    }
    df["payment_method"] = df["payment_method"].astype(str).str.strip()
    df["payment_method"] = df["payment_method"].map(lambda v: pay_map.get(v.title(), v) if isinstance(v, str) else v)
    df["payment_method"] = df["payment_method"].fillna("Unknown")

    # 4. Channel & status
    df["channel"] = df["channel"].astype(str).str.strip().str.title()
    df["channel"] = df["channel"].fillna("Web")

    df["status"] = df["status"].astype(str).str.strip().str.title()
    df["status"] = df["status"].replace({"Complete": "Completed"})
    df["status"] = df["status"].fillna("Unknown")

    # 5. Parse dates with multiple formats
    df["order_date"] = pd.to_datetime(df["order_date"], errors="coerce", dayfirst=False)
    # Anything that failed -> try dayfirst=True
    mask_failed = df["order_date"].isna()
    df.loc[mask_failed, "order_date"] = pd.to_datetime(
        df.loc[mask_failed, "order_date"], errors="coerce", dayfirst=True
    )
    # Drop future / absurd dates
    cutoff = pd.Timestamp("2024-12-31")
    df.loc[df["order_date"] > cutoff, "order_date"] = pd.NaT

    # 6. Drop duplicates
    df = drop_duplicates_keep_first(df)

    return df


# ---------------------------------------------------------------------------
# Order Items
# ---------------------------------------------------------------------------
def clean_order_items(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # 1. Numeric
    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce")
    df["unit_price"] = pd.to_numeric(df["unit_price"], errors="coerce")
    df["discount"] = pd.to_numeric(df["discount"], errors="coerce")

    # 2. Discount must be in [0, 0.9]
    df["discount"] = df["discount"].where(df["discount"].between(0, 0.9), np.nan)
    df["discount"] = df["discount"].fillna(0.0)

    # 3. Quantity: must be positive, drop extreme outliers
    df.loc[df["quantity"] <= 0, "quantity"] = np.nan
    p99 = df["quantity"].quantile(0.99)
    df.loc[df["quantity"] > p99 * 3, "quantity"] = p99
    df["quantity"] = df["quantity"].fillna(1).astype(int)

    # 4. Unit price: must be positive
    df.loc[df["unit_price"] <= 0, "unit_price"] = np.nan
    p99p = df["unit_price"].quantile(0.99)
    df.loc[df["unit_price"] > p99p * 5, "unit_price"] = p99p
    df["unit_price"] = df["unit_price"].fillna(df["unit_price"].median())

    # 5. Dedup
    df = drop_duplicates_keep_first(df)

    return df


# ---------------------------------------------------------------------------
# Returns
# ---------------------------------------------------------------------------
def clean_returns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # 1. Trim
    df = strip_whitespace(df, ["reason"])

    # 2. Reason normalization
    reason_map = {
        "Damaged": "Damaged", "DAMAGED": "Damaged", "damaged": "Damaged", "dmg": "Damaged",
        "Wrong Item": "Wrong Item", "wrong_item": "Wrong Item", "Wrongitem": "Wrong Item",
        "Not As Described": "Not as Described", "NAD": "Not as Described",
        "Not As Described": "Not as Described",
        "Late Delivery": "Late Delivery", "Changed Mind": "Changed Mind",
    }
    df["reason"] = df["reason"].astype(str).str.strip()
    df["reason"] = df["reason"].map(lambda v: reason_map.get(v.title(), v) if isinstance(v, str) else v)
    df["reason"] = df["reason"].replace({"Nan": np.nan, "None": np.nan})
    df["reason"] = df["reason"].fillna("Unknown")

    # 3. Refund amount
    df["refund_amount"] = pd.to_numeric(df["refund_amount"], errors="coerce")
    df.loc[df["refund_amount"] < 0, "refund_amount"] = df["refund_amount"].abs()
    df["refund_amount"] = df["refund_amount"].fillna(0.0)

    # 4. Dates
    df["return_date"] = pd.to_datetime(df["return_date"], errors="coerce", dayfirst=True)
    cutoff = pd.Timestamp("2024-12-31")
    df.loc[df["return_date"] > cutoff, "return_date"] = pd.NaT

    # 5. Dedup
    df = drop_duplicates_keep_first(df)

    return df
