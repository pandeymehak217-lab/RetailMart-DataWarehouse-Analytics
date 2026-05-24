# RetailMart Data Warehouse

I built this project because I kept seeing "data warehousing" and "star schema" 
in job descriptions and had no idea what they actually meant. Most tutorials 
explain it in theory but never show you a full working example. So I decided 
to build one from scratch and figure it out myself.

It took longer than I expected. The concept sounds simple until you actually 
sit down and try to do it.

---

## What This Project Is

A retail data warehouse built on Kimball star schema methodology.

The idea is that instead of querying raw messy tables directly, you build 
a clean structured warehouse where one central fact table connects to 
multiple dimension tables. Business analysts and BI tools can then query 
this warehouse without worrying about joins across 20 different source tables.

I simulated the full pipeline:

- Raw source data landing in a staging layer (the way it would arrive 
  from a real CRM or POS system)
- ETL process that cleans, transforms, and loads it into the warehouse
- Dimension and fact tables following star schema design
- Analytics queries that a BI team would actually run
- Dashboard and Excel report on top

---

## The Part That Confused Me The Most

SCD Type 2. Slowly Changing Dimensions.

I read the definition three times and still did not fully get it. The basic 
idea is that dimensions like customers change over time. A customer might 
start as a Silver loyalty member and get upgraded to Gold six months later. 
If you just overwrite the record you lose the history. If you never update 
it you have stale data.

SCD Type 2 solves this by keeping both records. When something changes, 
you close the old record by setting an end date and insert a new row 
with the updated values and a new start date. You also add an is_current 
flag so you always know which record is active.

Once I understood why it exists the implementation made sense. It is 
annoying to manage but the alternative is worse.

The dim_customer table in this project uses SCD Type 2 to track 
loyalty tier changes across time.

---

## Dataset

I generated the data myself using Python to simulate a realistic retail 
environment. Everything flows through three layers.

Staging layer — raw source data exactly as it would arrive from 
source systems, no cleaning done here

Dimension tables — cleaned, transformed, with surrogate keys assigned

Fact table — 80,000 rows, one per line item, connected to all 
five dimensions via foreign keys

| Table | Layer | Rows |
|-------|-------|------|
| stg_sales | Staging | 80,000 |
| stg_customers | Staging | 5,000 |
| stg_products | Staging | 1,000 |
| stg_stores | Staging | 100 |
| dim_date | Dimension | 1,827 |
| dim_customer | Dimension SCD2 | 5,000 |
| dim_product | Dimension | 1,000 |
| dim_store | Dimension | 100 |
| dim_promotion | Dimension | 8 |
| fact_sales | Fact | 80,000 |

Period: January 2020 to December 2024
Total GMV: Rs 203.6 Crore

---

## Folder Structure

```
datawarehouse-analytics/
|
|-- data/
|   |-- staging/          raw source files
|   |-- dimensions/       cleaned dimension tables
|   |-- facts/            central fact table
|
|-- sql/
|   |-- ddl/              schema creation, indexes, views
|   |-- etl/              data quality checks and load logic
|   |-- analytics/        business intelligence queries
|
|-- python/
|   |-- analysis.py       analytics, charts, Excel report
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

## SQL Work

I split the SQL into three separate files because mixing DDL, ETL, 
and analytics in one file is a mess to maintain.

create_schema.sql creates all the tables, foreign keys, indexes, 
and three analytics views that act as a semantic layer between the 
warehouse and BI tools.

etl_pipeline.sql covers the ETL logic including data quality 
checks before loading. I added checks for null critical fields, 
duplicate detection, negative revenue, orphan records, and date 
range validation. In a real warehouse you would fail the pipeline 
if these checks do not pass. I also added an etl_audit_log table 
that records each batch run with record counts and status.

dwh_analytics.sql has 25+ queries covering the actual business 
questions a BI team would ask. Things like year-over-year growth 
by category, store performance ranked within region, festival month 
uplift, promotion effectiveness, and price band analysis.

The most interesting pattern I learned here is using the date 
dimension instead of date functions on the fact table. Instead of 
writing EXTRACT(YEAR FROM sale_date), you join to dim_date and 
filter on d.year. Sounds like a small thing but it makes queries 
faster and easier to read.

---

## What I Built On Top

Python — ran the star schema queries using DuckDB and built 
a matplotlib dashboard with 8 panels covering revenue trend, 
category performance, regional breakdown, promotion analysis, 
loyalty tier split, price band, festival uplift, and an 
architecture summary panel.

Excel — 5 sheet report with the key tables formatted with 
alternating row colours and the dashboard image embedded 
on the first sheet.

---

## Key Numbers

Total GMV: Rs 203.6 Crore across 80,000 transactions

Electronics is the highest revenue category but has the lowest 
margin at around 18%. Grocery has the best margin at 38% but 
smallest basket size.

Festival months (October and November) show 34% higher average 
basket size than regular months.

Platinum loyalty members are 10% of customers but contribute 
31% of revenue. Average basket for Platinum is Rs 8,240 compared 
to Rs 2,100 for Bronze.

---

## How To Run

```bash
pip3 install duckdb pandas numpy matplotlib xlsxwriter

python3 generate_data.py
python3 run_queries.py
python3 python/analysis.py
```

Outputs will appear in the outputs/ folder.

---

## What I Would Do Differently

The staging layer is too clean. In a real project source data 
comes in with encoding issues, inconsistent date formats, 
extra whitespace, and duplicate transactions from system retries. 
I would add a proper data profiling step before the quality checks.

I also want to add an incremental load pattern eventually. Right now 
the ETL does a full reload every time. Real warehouses use 
watermark-based incremental loads so you only process new records 
since the last run.

---

## What I Learned

Star schema is not complicated once you understand what problem 
it solves. The whole point is to separate what happened (fact table) 
from the context around it (dimension tables). Once that clicked 
everything else followed.

SCD Type 2 is annoying to implement but I understand now why 
data teams care about it. Losing historical dimension data causes 
wrong reports. A customer who churned from Gold to Bronze should 
not have all their old Gold purchases re-attributed to Bronze just 
because you overwrote the record.

The ETL audit log is something I had never thought about before. 
In production you need to know which batch ran, how many records 
loaded, and whether anything got rejected. Without that you are 
flying blind when something breaks.

---

Mehak Pandey
pandeymehak.217@gmail.com
