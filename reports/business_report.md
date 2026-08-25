# E-Commerce Analytics Platform - Business Report

> **Author:** Mateo - Data Analyst portfolio project
> **Dataset:** Synthetic e-commerce data (5,000 customers, 300 products, 25,000 orders, 70,000 line items, 5,600 returns).
> **Period simulated:** Jan 2022 - Dec 2024 (3 fiscal years).

---

## 1. Executive summary

Across the three simulated fiscal years the platform processed **~$19M of net revenue** across **~25K orders** placed by **~5K active customers**, with an overall **profit margin of ~38%** and an **item-level return rate of ~8%**.

Three structural patterns drive performance:

1. **Concentration** - revenue and profit are highly concentrated in a small number of categories, products and customers.
2. **Seasonality** - Q4 is materially stronger than any other quarter.
3. **Customer heterogeneity** - a small "Champions / Loyal" group is responsible for the bulk of the platform's revenue.

Acting on these patterns offers a realistic path to **5-15% revenue lift and 2-4pt margin expansion** without additional acquisition spend.

---

## 2. Key metrics at a glance

| Metric                    | Value (3y total) |
|---------------------------|-----------------:|
| Total Revenue             | ~$19.4M |
| Total Profit              | ~$7.4M |
| Profit Margin             | ~38% |
| Orders                    | ~25,000 |
| Customers (unique)        | ~5,000 |
| Average Order Value (AOV) | ~$775 |
| Return Rate (item level)  | ~8% |
| 3-yr Customer Lifetime Value (avg) | ~$2,300 |

---

## 3. Top findings

### Finding 1 - Top categories earn a disproportionate share of profit
**Evidence:** Category-level revenue and profit shares show the top 2-3 categories generate ~50% of revenue but ~65% of profit.

**Impact:** Some "big" categories are not actually big contributors to profit. Merchandising investment decisions made on revenue alone misallocate capital.

**Recommendation:** Rebalance inventory and promo dollars toward the categories with the highest profit share (e.g., Electronics + Home & Kitchen), and review the SKU mix of categories with profit_share < revenue_share.

### Finding 2 - Pareto distribution: top 20% of products drive ~80% of revenue
**Evidence:** Cumulative revenue curve on the product table.

**Impact:** Inventory policies should be tiered. Stock-outs on hero SKUs have an outsized impact.

**Recommendation:** Implement differentiated safety-stock and replenishment rules: tight for top 20%, lean for the rest.

### Finding 3 - High-volume / low-margin products are a profit leak
**Evidence:** Several products sit in the top quartile of revenue but contribute margin < 15%.

**Impact:** They tie up warehouse space and customer service capacity for thin profit.

**Recommendation:** Renegotiate supplier cost, reduce discount depth, or replace with higher-margin alternatives.

### Finding 4 - Q4 seasonality is material
**Evidence:** November and December run 25-40% above the monthly average.

**Impact:** Inventory and ad spend that miss the Q4 window cannot be recovered.

**Recommendation:** Lock Q4 inventory by September, media by October. Plan a focused Cyber Week promo in week 48.

### Finding 5 - Regional revenue is uneven
**Evidence:** 2 regions contribute ~60% of revenue.

**Impact:** Under-penetrated regions are the highest-marginal-return growth lever.

**Recommendation:** Run a localized promo + acquisition campaign in the bottom 2 regions and measure incrementality.

### Finding 6 - Returns are concentrated
**Evidence:** Return rate by category varies from ~5% to ~13%.

**Impact:** Each 1pt reduction in category-level return rate improves margin by a measurable amount.

**Recommendation:** For high-return categories, enrich product descriptions, add sizing/fit guides, and review supplier quality.

### Finding 7 - Champions + Loyal Customers = <20% of base, >50% of revenue
**Evidence:** RFM segment economics.

**Impact:** Retention of these cohorts is worth more than equivalent new acquisition.

**Recommendation:** Launch a loyalty program (early access, free shipping, points). Monitor churn signals weekly.

### Finding 8 - "At Risk" segment is a win-back opportunity
**Evidence:** Thousands of customers with high historical spend and long recency.

**Impact:** Reactivation is cheaper than acquisition; we already know their preferences.

**Recommendation:** Trigger personalized win-back emails with a time-limited discount tied to past categories.

### Finding 9 - Channel mix is shifting
**Evidence:** Mobile share has grown year over year at the expense of web.

**Impact:** Marketing budget allocation should follow the channel mix.

**Recommendation:** Re-balance paid media by channel every quarter; invest in the channel with the highest marginal growth.

### Finding 10 - Slow-moving SKUs tie up working capital
**Evidence:** Hundreds of products sold <5 units over 3 years.

**Impact:** Each slow SKU carries carrying cost with no turn.

**Recommendation:** Run a clearance campaign, bundle them with fast-movers, or delist.

---

## 4. Proposed 90-day action plan

| Action | Owner (illustrative) | Horizon |
|--------|---------------------|---------|
| Q4 inventory lock for top 20% SKUs | Merchandising | 30 days |
| Renegotiate cost on top-10 high-volume / low-margin SKUs | Procurement | 60 days |
| Loyalty program MVP for Champions + Loyal segments | CRM | 60 days |
| Win-back campaign for "At Risk" segment | CRM | 30 days |
| Regional acquisition test in bottom 2 regions | Marketing | 90 days |
| Clearance for slow movers | Merchandising | 45 days |
| Sizing/fit guide rollout for top return-rate category | Content | 45 days |

---

## 5. Limitations of this analysis

- The dataset is **synthetic**, so absolute numbers are not externally comparable.
- The CLV proxy uses a flat 3-year horizon; real-world CLV modelling would use BG/NBD or Pareto/NBD with discount rate.
- Return reason attribution is limited by the reasons captured in the source data.
- No causal inference was performed: all correlations are observational and should be validated with controlled experiments.

---

## 6. Next steps

- Add a survival / churn model to score customers monthly.
- Add market-basket analysis to surface cross-sell bundles.
- Wire the dashboard to a live database (Postgres / BigQuery) instead of CSV snapshots.
- Build A/B test infrastructure so recommendations can be tested, not just shipped.
