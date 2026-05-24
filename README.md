# RetailMart Data Warehouse — End-to-End BI System

Author : Mehak Pandey
Email  : pandeymehak.217@gmail.com
Tools  : SQL, Python, Power BI, Star Schema, ETL, Kimball Methodology
Period : 2020 - 2024

---

## Project Overview

RetailMart Data Warehouse is a full enterprise-grade BI system built on
Kimball star schema methodology. It covers the complete data engineering
and analytics pipeline from raw source data in the staging layer through
ETL transformation into dimension and fact tables, finishing with SQL
analytics queries and Power BI dashboards.

This project demonstrates the advanced topics that distinguish senior
data analysts from freshers: data warehousing concepts, ETL design,
SCD Type 2 implementation, star schema joins, and BI-optimised SQL patterns.

---

## Architecture

```
Source Systems (CRM, ERP, POS)
        |
        v
STAGING LAYER (raw CSVs, no transformation)
  stg_customers.csv   5,000 rows
  stg_products.csv    1,000 rows
  stg_stores.csv        100 rows
  stg_sales.csv       80,000 rows
        |
        v
ETL PIPELINE (data quality -> transform -> load)
  Data quality checks, null handling, deduplication
        |
        v
DIMENSION TABLES (conformed, reusable)
  dim_date.csv        1,827 rows  (date intelligence)
  dim_customer.csv    5,000 rows  (SCD Type 2)
  dim_product.csv     1,000 rows  (price band hierarchy)
  dim_store.csv         100 rows  (regional hierarchy)
  dim_promotion.csv       8 rows  (promotion types)
        |
        v
FACT TABLE (star schema centre)
  fact_sales.csv     80,000 rows  (grain: 1 per line item)
        |
        v
ANALYTICS VIEWS + BI DASHBOARDS
  v_daily_sales, v_category_performance, v_store_performance
```

---

## Project Structure

```
datawarehouse-analytics/
|
|-- data/
|   |-- staging/           (raw source data)
|   |-- dimensions/        (conformed dimension tables)
|   |-- facts/             (central fact table)
|
|-- sql/
|   |-- ddl/
|   |   |-- create_schema.sql    (schema, tables, indexes, views)
|   |-- etl/
|   |   |-- etl_pipeline.sql     (data quality, transform, load)
|   |-- analytics/
|       |-- dwh_analytics.sql    (25+ BI queries on star schema)
|
|-- python/
|   |-- analysis.py              (analytics, dashboard, Excel)
|
|-- powerbi/
|   |-- POWERBI_GUIDE.md         (DAX, relationships, 4 pages)
|
|-- outputs/
|   |-- dwh_dashboard.png
|   |-- RetailMart_DWH_Report.xlsx
|
|-- generate_data.py
|-- run_queries.py
|-- README.md
```

---

## Key DWH Concepts Demonstrated

Kimball Star Schema
Single central fact table (fact_sales) connected to 5 dimension tables
via integer surrogate keys. Optimised for BI tool performance.

Grain Definition
fact_sales grain is one row per line item per transaction.
This allows flexible aggregation at any level.

Conformed Dimensions
dim_date is reusable across any future fact table (sales, inventory,
returns). dim_customer and dim_store follow the same pattern.

SCD Type 2 — Slowly Changing Dimension
dim_customer tracks historical loyalty tier changes using
scd_start_date, scd_end_date, and is_current columns.
When a customer is upgraded from Silver to Gold, a new row is inserted
with is_current=1 and the old row gets scd_end_date set.

Surrogate Keys
Natural source keys (src_customer_id) are replaced with integer
surrogate keys (customer_key) in the warehouse. This isolates the
warehouse from source system changes.

Date Dimension
Standalone dim_date with 1,827 rows (one per day 2020-2024).
Contains fiscal year, season, festival month, weekend flags.
Enables time intelligence queries without date functions on fact table.

ETL Audit Log
etl_audit_log table tracks every ETL batch: records extracted,
loaded, rejected, duration, and status. This is standard in
production data warehouses.

Analytics Views
Pre-built views (v_daily_sales, v_category_performance,
v_store_performance) act as semantic layer between fact/dimension
tables and BI tools. Power BI connects to views, not raw tables.

---

## SQL Concepts Used

Star schema joins (fact + multiple dimensions),
Date dimension slicing (year, quarter, month, season, festival),
RANK() and DENSE_RANK() with PARTITION BY region/category,
LAG() for YoY comparison within category,
Rolling 3-month average using ROWS BETWEEN,
YTD running total using SUM() OVER PARTITION BY year,
CASE-based pivot for payment method analysis,
Co-occurrence analysis using self-join,
Data quality scorecard using conditional COUNT,
ETL lineage tracking using GROUP BY on batch_id

---

## ETL Pipeline Steps

Step 1 - Data Quality Checks
Null check on critical fields, duplicate detection, range validation,
orphan record check (sales with no matching customer).

Step 2 - Transform and Load Dimensions
Clean null values using COALESCE, trim whitespace, derive calculated
columns (age, age_group, margin_pct, price_band), assign surrogate keys.

Step 3 - Load Fact Table
Join staging sales to all dimensions to resolve surrogate keys,
calculate derived measures (profit_margin_pct), stamp ETL metadata.

Step 4 - Audit Log
Insert into etl_audit_log with record counts, batch ID, status.

---

## Key Business Findings

Electronics generates the highest revenue at Rs 52.4 Crore but has
the lowest profit margin at 18.3% due to thin margins on branded items.
Grocery has the highest margin at 38.2% but lowest ticket size.

Festival months (October and November) show 34% higher average basket
size compared to regular months. Promotional discount of 40%+ reduces
margins to near-zero but drives 2.8x transaction volume.

South region leads in total revenue at Rs 68.2 Crore, driven by
Bengaluru and Hyderabad hypermarkets. West region has the highest
revenue per square foot due to smaller store formats.

Platinum loyalty tier customers represent 10% of customers but
contribute 31% of total revenue. Average basket size for Platinum
members is Rs 8,240 vs Rs 2,100 for Bronze members.

Mid-Range price band (Rs 500 to Rs 5,000) is the largest revenue
driver at 38% share, confirming Indian retail sweet spot is aspirational
but affordable products.

---

## How to Run

```bash
pip3 install duckdb pandas numpy matplotlib xlsxwriter
python3 generate_data.py
python3 run_queries.py
python3 python/analysis.py
```

---

## Resume Bullet Points

Built end-to-end Kimball star schema data warehouse on 80,000 retail
transactions using staging, dimension, and fact layers with ETL pipeline.

Designed SCD Type 2 on dim_customer to track loyalty tier changes,
with scd_start_date, scd_end_date, and is_current columns following
industry-standard data warehousing methodology.

Created date dimension (dim_date) with 1,827 rows containing fiscal
year, season, festival month, and weekend flags enabling time
intelligence queries without date functions on the fact table.

Implemented ETL data quality checks covering null detection, duplicate
identification, orphan record validation, and date range verification
before loading 80,000 rows into fact_sales.

Built 25+ analytics queries on star schema covering YoY comparison,
rolling averages, co-occurrence analysis, promotional uplift, and
SCD audit queries — all optimised for BI tool consumption.

---

About
Mehak Pandey — Fresher Data Analyst
Email: pandeymehak.217@gmail.com
Dataset is synthetically generated to simulate real retail data warehouse.
