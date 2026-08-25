"""
Interactive Plotly Dash dashboard for the E-Commerce Analytics Platform.

Run:
    python dashboard/app.py

Then open http://127.0.0.1:8050 in your browser.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, Input, Output, dcc, html
from dash import dash_table

# ---------------------------------------------------------------------------
# Paths & data loading
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

FINAL = ROOT / "data" / "final"

monthly = pd.read_csv(FINAL / "monthly_summary.csv")
by_cat = pd.read_csv(FINAL / "category_summary.csv")
by_reg = pd.read_csv(FINAL / "region_summary.csv")
by_ch = pd.read_csv(FINAL / "channel_summary.csv")
top_products = pd.read_csv(FINAL / "top_products.csv")
rfm = pd.read_csv(FINAL / "rfm_segments.csv")
fact = pd.read_csv(FINAL / "fact_sales.csv", parse_dates=["order_date"])
returns_df = pd.read_csv(ROOT / "data" / "processed" / "returns.csv",
                         parse_dates=["return_date"])

completed = fact[fact["is_completed"]].copy()


# ---------------------------------------------------------------------------
# Reusable palette
# ---------------------------------------------------------------------------
PALETTE = px.colors.qualitative.Safe
COLOR_REVENUE = "#1f77b4"
COLOR_PROFIT = "#2ca02c"
COLOR_NEUTRAL = "#7f7f7f"


def fmt_currency(x: float) -> str:
    if x >= 1_000_000:
        return f"${x / 1_000_000:.2f}M"
    if x >= 1_000:
        return f"${x / 1_000:.1f}K"
    return f"${x:,.2f}"


# ---------------------------------------------------------------------------
# Layout helpers
# ---------------------------------------------------------------------------
def kpi_card(title: str, value: str, subtitle: str = "") -> html.Div:
    return html.Div(
        className="kpi-card",
        children=[
            html.Div(title, className="kpi-title"),
            html.Div(value, className="kpi-value"),
            html.Div(subtitle, className="kpi-subtitle"),
        ],
    )


CATEGORY_OPTIONS = [{"label": c, "value": c} for c in sorted(by_cat["category"].unique())]
REGION_OPTIONS = [{"label": r, "value": r} for r in sorted(by_reg["region"].unique())]
CHANNEL_OPTIONS = [{"label": c, "value": c} for c in sorted(by_ch["channel"].unique())]

DEFAULT_CATS = [o["value"] for o in CATEGORY_OPTIONS]
DEFAULT_REGS = [o["value"] for o in REGION_OPTIONS]


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = Dash(__name__, title="E-Commerce Analytics Platform")
app.index_string = """<!DOCTYPE html>
<html>
<head>
    {%metas%}
    <title>E-Commerce Analytics Platform</title>
    {%favicon%}
    {%css%}
    <style>
        body { font-family: 'Segoe UI', Roboto, Arial, sans-serif; background: #f4f6fa; color: #1f2933; margin: 0; }
        .header { background: linear-gradient(90deg, #1f77b4 0%, #2ca02c 100%); color: white; padding: 18px 28px; }
        .header h1 { margin: 0; font-size: 22px; font-weight: 600; }
        .header p { margin: 4px 0 0 0; font-size: 13px; opacity: 0.9; }
        .container { padding: 22px 28px; }
        .kpi-row { display: grid; grid-template-columns: repeat(7, 1fr); gap: 14px; margin-bottom: 22px; }
        .kpi-card { background: white; border-radius: 8px; padding: 14px 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.08); }
        .kpi-title { font-size: 11px; text-transform: uppercase; letter-spacing: 0.06em; color: #6b7280; }
        .kpi-value { font-size: 22px; font-weight: 700; margin-top: 4px; color: #111827; }
        .kpi-subtitle { font-size: 11px; color: #9ca3af; margin-top: 2px; }
        .row { display: grid; grid-template-columns: 1fr 1fr; gap: 18px; margin-bottom: 18px; }
        .panel { background: white; border-radius: 8px; padding: 16px 18px; box-shadow: 0 1px 3px rgba(0,0,0,0.08); }
        .panel h3 { margin: 0 0 10px 0; font-size: 14px; color: #1f2933; font-weight: 600; }
        .filter-row { display: flex; gap: 18px; align-items: flex-end; margin-bottom: 18px; flex-wrap: wrap; }
        .filter { background: white; border-radius: 8px; padding: 12px 14px; box-shadow: 0 1px 3px rgba(0,0,0,0.08); min-width: 220px; }
        .filter label { display: block; font-size: 11px; text-transform: uppercase; letter-spacing: 0.06em; color: #6b7280; margin-bottom: 4px; }
    </style>
</head>
<body class="dash-template">
    <div class="header">
        <h1>E-Commerce Analytics Platform</h1>
        <p>Executive dashboard - revenue, profit, customers, products and returns</p>
    </div>
    <div class="container">
        {%app_entry%}
    </div>
    <footer style="text-align:center; padding:18px; color:#9ca3af; font-size:12px;">
        Built with Pandas + Plotly Dash
    </footer>
    {%config%}
    {%scripts%}
    {%renderer%}
</body>
</html>"""


app.layout = html.Div(
    children=[
        html.Div(
            className="filter-row",
            children=[
                html.Div(
                    className="filter",
                    children=[
                        html.Label("Categories"),
                        dcc.Dropdown(
                            id="filter-category",
                            options=CATEGORY_OPTIONS,
                            value=DEFAULT_CATS,
                            multi=True,
                            placeholder="Select categories...",
                        ),
                    ],
                ),
                html.Div(
                    className="filter",
                    children=[
                        html.Label("Regions"),
                        dcc.Dropdown(
                            id="filter-region",
                            options=REGION_OPTIONS,
                            value=DEFAULT_REGS,
                            multi=True,
                            placeholder="Select regions...",
                        ),
                    ],
                ),
                html.Div(
                    className="filter",
                    children=[
                        html.Label("Channels"),
                        dcc.Dropdown(
                            id="filter-channel",
                            options=CHANNEL_OPTIONS,
                            value=[o["value"] for o in CHANNEL_OPTIONS],
                            multi=True,
                        ),
                    ],
                ),
                html.Div(
                    className="filter",
                    children=[
                        html.Label("Year"),
                        dcc.Dropdown(
                            id="filter-year",
                            options=[{"label": "All", "value": "All"}]
                            + [{"label": str(y), "value": y}
                               for y in sorted(fact["year"].dropna().unique().astype(int))],
                            value="All",
                        ),
                    ],
                ),
            ],
        ),
        html.Div(id="kpi-row", className="kpi-row"),
        html.Div(
            className="row",
            children=[
                html.Div(className="panel", children=[html.H3("Revenue over time"),
                                                       dcc.Graph(id="chart-revenue")]),
                html.Div(className="panel", children=[html.H3("Profit over time"),
                                                       dcc.Graph(id="chart-profit")]),
            ],
        ),
        html.Div(
            className="row",
            children=[
                html.Div(className="panel", children=[html.H3("Sales by category"),
                                                       dcc.Graph(id="chart-category")]),
                html.Div(className="panel", children=[html.H3("Revenue by region"),
                                                       dcc.Graph(id="chart-region")]),
            ],
        ),
        html.Div(
            className="row",
            children=[
                html.Div(className="panel", children=[html.H3("Top 15 products"),
                                                       dcc.Graph(id="chart-top-products")]),
                html.Div(className="panel", children=[html.H3("Customer segments"),
                                                       dcc.Graph(id="chart-segments")]),
            ],
        ),
        html.Div(
            className="row",
            children=[
                html.Div(className="panel", children=[html.H3("Return rate by category"),
                                                       dcc.Graph(id="chart-return-rate")]),
                html.Div(className="panel", children=[html.H3("Channel performance"),
                                                       dcc.Graph(id="chart-channel")]),
            ],
        ),
        html.Div(
            className="panel",
            children=[
                html.H3("Top products table (revenue, profit, margin)"),
                dash_table.DataTable(
                    id="table-top-products",
                    page_size=10,
                    style_table={"overflowX": "auto"},
                    style_cell={"fontSize": 12, "padding": "6px"},
                    style_header={"backgroundColor": "#f3f4f6", "fontWeight": "bold"},
                    style_data_conditional=[
                        {"if": {"row_index": "odd"}, "backgroundColor": "#fafafa"},
                    ],
                ),
            ],
        ),
    ]
)


# ---------------------------------------------------------------------------
# Filtering callback
# ---------------------------------------------------------------------------
def apply_filters(cats, regs, chs, year):
    df = completed.copy()
    if cats:
        df = df[df["category"].isin(cats)]
    if regs:
        df = df[df["region"].isin(regs)]
    if chs:
        df = df[df["channel"].isin(chs)]
    if year and year != "All":
        df = df[df["year"] == int(year)]
    return df


@app.callback(
    Output("kpi-row", "children"),
    Output("chart-revenue", "figure"),
    Output("chart-profit", "figure"),
    Output("chart-category", "figure"),
    Output("chart-region", "figure"),
    Output("chart-top-products", "figure"),
    Output("chart-segments", "figure"),
    Output("chart-return-rate", "figure"),
    Output("chart-channel", "figure"),
    Output("table-top-products", "data"),
    Output("table-top-products", "columns"),
    Input("filter-category", "value"),
    Input("filter-region", "value"),
    Input("filter-channel", "value"),
    Input("filter-year", "value"),
)
def update_dashboard(cats, regs, chs, year):
    df = apply_filters(cats, regs, chs, year)

    revenue = float(df["net_revenue"].sum())
    profit = float(df["profit"].sum())
    orders = int(df["order_id"].nunique())
    customers = int(df["customer_id"].nunique())
    aov = revenue / orders if orders else 0.0
    return_rate = df["returned_flag"].mean() if len(df) else 0.0
    profit_margin = profit / revenue if revenue else 0.0

    kpis = [
        kpi_card("Total Revenue", fmt_currency(revenue), f"across {orders:,} orders"),
        kpi_card("Total Profit", fmt_currency(profit), f"margin {profit_margin:.1%}"),
        kpi_card("Orders", f"{orders:,}", "completed"),
        kpi_card("Customers", f"{customers:,}", "unique buyers"),
        kpi_card("Avg Order Value", f"${aov:,.2f}", "net of discounts"),
        kpi_card("Return Rate", f"{return_rate:.1%}", "by item"),
        kpi_card("Profit Margin", f"{profit_margin:.1%}", "profit / revenue"),
    ]

    # Monthly trend
    monthly_df = (
        df.groupby("year_month", as_index=False)
        .agg(revenue=("net_revenue", "sum"),
             profit=("profit", "sum"),
             orders=("order_id", "nunique"))
        .sort_values("year_month")
    )

    fig_rev = px.line(monthly_df, x="year_month", y="revenue", markers=True,
                      title=None)
    fig_rev.update_traces(line_color=COLOR_REVENUE, line_width=3)
    fig_rev.update_layout(margin=dict(l=10, r=10, t=10, b=40),
                          xaxis_title="Month", yaxis_title="Revenue (USD)")

    fig_prof = px.line(monthly_df, x="year_month", y="profit", markers=True,
                       title=None, color_discrete_sequence=[COLOR_PROFIT])
    fig_prof.update_traces(line_color=COLOR_PROFIT, line_width=3)
    fig_prof.update_layout(margin=dict(l=10, r=10, t=10, b=40),
                           xaxis_title="Month", yaxis_title="Profit (USD)")

    # Category
    cat_df = (
        df.groupby("category", as_index=False)
        .agg(revenue=("net_revenue", "sum"), profit=("profit", "sum"),
             units=("quantity", "sum"))
        .sort_values("revenue", ascending=False)
    )
    fig_cat = go.Figure(data=[
        go.Bar(name="Revenue", x=cat_df["category"], y=cat_df["revenue"],
               marker_color=COLOR_REVENUE),
        go.Bar(name="Profit", x=cat_df["category"], y=cat_df["profit"],
               marker_color=COLOR_PROFIT),
    ])
    fig_cat.update_layout(barmode="group", margin=dict(l=10, r=10, t=10, b=70),
                          xaxis_tickangle=-25)

    # Region
    reg_df = (
        df.groupby("region", as_index=False)
        .agg(revenue=("net_revenue", "sum"),
             customers=("customer_id", "nunique"),
             orders=("order_id", "nunique"))
        .sort_values("revenue", ascending=False)
    )
    fig_reg = px.bar(reg_df, x="region", y="revenue", color="region",
                     color_discrete_sequence=PALETTE, text="revenue")
    fig_reg.update_traces(texttemplate="%{text:$,.0f}", textposition="outside")
    fig_reg.update_layout(showlegend=False, margin=dict(l=10, r=10, t=10, b=40),
                          yaxis_title="Revenue (USD)")

    # Top products
    top_df = (
        df.groupby(["product_id", "product_name", "category"], as_index=False)
        .agg(revenue=("net_revenue", "sum"), profit=("profit", "sum"),
             units=("quantity", "sum"))
        .sort_values("revenue", ascending=False)
        .head(15)
    )
    top_df["profit_margin"] = (top_df["profit"] / top_df["revenue"]).fillna(0)
    fig_top = px.bar(top_df.sort_values("revenue"), y="product_name", x="revenue",
                     color="category", orientation="h",
                     color_discrete_sequence=PALETTE)
    fig_top.update_layout(margin=dict(l=10, r=10, t=10, b=10),
                          yaxis_title=None, xaxis_title="Revenue (USD)",
                          height=420)

    # Segments (RFM)
    seg_df = (
        df.drop_duplicates("customer_id")
        .merge(rfm[["customer_id", "segment", "clv", "revenue"]], on="customer_id", how="left",
               suffixes=("_fact", "_rfm"))
    )
    seg_summary = (
        seg_df.groupby("segment_rfm", as_index=False)
        .agg(customers=("customer_id", "count"),
             revenue=("revenue", "sum"),
             avg_clv=("clv", "mean"))
        .sort_values("revenue", ascending=False)
    )
    fig_seg = go.Figure(data=[
        go.Bar(name="Customers", x=seg_summary["segment_rfm"], y=seg_summary["customers"],
               marker_color=COLOR_NEUTRAL, yaxis="y", offsetgroup=1),
        go.Bar(name="Revenue", x=seg_summary["segment_rfm"], y=seg_summary["revenue"],
               marker_color=COLOR_REVENUE, yaxis="y2", offsetgroup=2),
    ])
    fig_seg.update_layout(
        margin=dict(l=10, r=10, t=10, b=70), xaxis_tickangle=-25,
        yaxis=dict(title="Customers"),
        yaxis2=dict(title="Revenue (USD)", overlaying="y", side="right"),
        legend=dict(orientation="h", y=-0.25),
    )

    # Returns
    ret_df = (
        df.groupby("category", as_index=False)
        .agg(items=("returned_flag", "size"),
             returned=("returned_flag", "sum"))
    )
    ret_df["return_rate"] = ret_df["returned"] / ret_df["items"]
    ret_df = ret_df.sort_values("return_rate", ascending=False)
    fig_ret = px.bar(ret_df, x="category", y="return_rate",
                     color="return_rate", color_continuous_scale="Reds",
                     text="return_rate")
    fig_ret.update_traces(texttemplate="%{text:.1%}", textposition="outside")
    fig_ret.update_layout(margin=dict(l=10, r=10, t=10, b=70),
                          xaxis_tickangle=-25,
                          yaxis_tickformat=".0%",
                          coloraxis_showscale=False)

    # Channel
    ch_df = (
        df.groupby("channel", as_index=False)
        .agg(revenue=("net_revenue", "sum"),
             orders=("order_id", "nunique"),
             customers=("customer_id", "nunique"))
        .sort_values("revenue", ascending=False)
    )
    fig_ch = go.Figure(data=[
        go.Bar(name="Revenue", x=ch_df["channel"], y=ch_df["revenue"],
               marker_color=COLOR_REVENUE),
        go.Bar(name="Orders", x=ch_df["channel"], y=ch_df["orders"],
               marker_color=COLOR_NEUTRAL),
    ])
    fig_ch.update_layout(barmode="group", margin=dict(l=10, r=10, t=10, b=40))

    # Table
    table_df = top_df.sort_values("revenue", ascending=False).head(15).copy()
    table_df["revenue"] = table_df["revenue"].round(0).astype(int)
    table_df["profit"] = table_df["profit"].round(0).astype(int)
    table_df["profit_margin"] = (table_df["profit_margin"] * 100).round(1)
    columns = [{"name": c, "id": c} for c in
               ["product_id", "product_name", "category", "units",
                "revenue", "profit", "profit_margin"]]
    data = table_df.to_dict("records")

    return (kpis, fig_rev, fig_prof, fig_cat, fig_reg,
            fig_top, fig_seg, fig_ret, fig_ch, data, columns)


server = app.server

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=8050)
