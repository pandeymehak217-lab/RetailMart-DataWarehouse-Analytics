"""
RetailMart Data Warehouse — Run SQL Queries
Author: Mehak Pandey | pandeymehak.217@gmail.com
"""
import duckdb, pandas as pd

DIMS  = '/Users/mehekpandey/datawarehouse_project/data/dimensions'
FACTS = '/Users/mehekpandey/datawarehouse_project/data/facts'
con   = duckdb.connect()

con.execute(f"CREATE TABLE dim_date      AS SELECT * FROM read_csv_auto('{DIMS}/dim_date.csv')")
con.execute(f"CREATE TABLE dim_customer  AS SELECT * FROM read_csv_auto('{DIMS}/dim_customer.csv')")
con.execute(f"CREATE TABLE dim_product   AS SELECT * FROM read_csv_auto('{DIMS}/dim_product.csv')")
con.execute(f"CREATE TABLE dim_store     AS SELECT * FROM read_csv_auto('{DIMS}/dim_store.csv')")
con.execute(f"CREATE TABLE dim_promotion AS SELECT * FROM read_csv_auto('{DIMS}/dim_promotion.csv')")
con.execute(f"CREATE TABLE fact_sales    AS SELECT * FROM read_csv_auto('{FACTS}/fact_sales.csv')")

queries = {
"1. YoY Revenue by Category (Star Schema)": """
    WITH y AS (
        SELECT d.year, p.category,
               ROUND(SUM(f.gross_revenue)/10000000,2) AS revenue_crore
        FROM fact_sales f
        JOIN dim_date d ON f.date_key=d.date_key
        JOIN dim_product p ON f.product_key=p.product_key
        WHERE f.return_flag=0 GROUP BY d.year, p.category
    )
    SELECT year, category, revenue_crore,
           ROUND((revenue_crore-LAG(revenue_crore) OVER
                  (PARTITION BY category ORDER BY year))*100.0
                 /NULLIF(LAG(revenue_crore) OVER
                  (PARTITION BY category ORDER BY year),0),2) AS yoy_growth
    FROM y ORDER BY category, year LIMIT 20
""",
"2. Region Store Performance + Rank": """
    SELECT s.region, s.store_format,
           COUNT(DISTINCT f.store_key) AS stores,
           ROUND(SUM(f.gross_revenue)/10000000,2) AS revenue_crore,
           ROUND(AVG(f.profit_margin_pct),2) AS avg_margin,
           RANK() OVER (ORDER BY SUM(f.gross_revenue) DESC) AS rank
    FROM fact_sales f JOIN dim_store s ON f.store_key=s.store_key
    WHERE f.return_flag=0
    GROUP BY s.region, s.store_format ORDER BY revenue_crore DESC
""",
"3. Festival vs Regular Uplift (Date Dimension)": """
    SELECT CASE WHEN d.is_festival_month=1 THEN 'Festival Month'
                ELSE 'Regular Month' END AS period,
           COUNT(*) AS txns,
           ROUND(AVG(f.gross_revenue),0) AS avg_basket,
           ROUND(SUM(f.gross_revenue)/10000000,2) AS revenue_crore,
           ROUND(AVG(f.discount_pct),2) AS avg_discount
    FROM fact_sales f JOIN dim_date d ON f.date_key=d.date_key
    WHERE f.return_flag=0 GROUP BY d.is_festival_month
""",
"4. Loyalty Tier Revenue Share": """
    SELECT c.loyalty_tier,
           COUNT(DISTINCT f.customer_key) AS customers,
           ROUND(SUM(f.gross_revenue)/10000000,2) AS revenue_crore,
           ROUND(SUM(f.gross_revenue)*100.0/SUM(SUM(f.gross_revenue)) OVER(),2) AS share_pct,
           ROUND(AVG(f.gross_revenue),0) AS avg_basket
    FROM fact_sales f JOIN dim_customer c ON f.customer_key=c.customer_key
    WHERE f.return_flag=0 GROUP BY c.loyalty_tier ORDER BY revenue_crore DESC
""",
"5. DWH Data Quality Scorecard": """
    SELECT COUNT(*) AS total_records,
           COUNT(CASE WHEN gross_revenue<=0 THEN 1 END) AS bad_revenue,
           COUNT(CASE WHEN quantity<=0 THEN 1 END) AS bad_quantity,
           COUNT(CASE WHEN date_key IS NULL THEN 1 END) AS null_date_key,
           ROUND(COUNT(CASE WHEN gross_revenue>0 AND quantity>0
                             AND date_key IS NOT NULL THEN 1 END)
                 *100.0/COUNT(*),2) AS quality_score_pct
    FROM fact_sales
""",
"6. Executive KPI": """
    SELECT COUNT(DISTINCT f.sales_key) AS txns,
           COUNT(DISTINCT f.customer_key) AS customers,
           ROUND(SUM(f.gross_revenue)/10000000,2) AS gmv_crore,
           ROUND(SUM(f.gross_profit)/10000000,2) AS profit_crore,
           ROUND(AVG(f.profit_margin_pct),2) AS avg_margin,
           ROUND(AVG(f.gross_revenue),0) AS avg_basket
    FROM fact_sales f WHERE f.return_flag=0
""",
}

print("="*65)
print("  RetailMart Data Warehouse — SQL Results")
print("  Author: Mehak Pandey | pandeymehak.217@gmail.com")
print("="*65)
for name, sql in queries.items():
    print(f"\n{'─'*65}\n  {name}\n{'─'*65}")
    print(con.execute(sql).df().to_string(index=False))
print("\n"+"="*65)
print("  All queries passed.")
print("="*65)
con.close()
