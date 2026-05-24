-- ================================================================
-- RetailMart Data Warehouse — Analytics Queries
-- Author      : Mehak Pandey
-- Email       : pandeymehak.217@gmail.com
-- Description : Business intelligence queries on star schema
--               Demonstrates advanced DWH SQL patterns
-- ================================================================

-- ----------------------------------------------------------------
-- SECTION 1: STANDARD STAR SCHEMA QUERIES
-- Fact + Dimension joins — bread and butter of DWH analytics
-- ----------------------------------------------------------------

-- 1.1 Year-quarter revenue by category (slice and dice)
SELECT
    d.year,
    d.quarter,
    p.category,
    COUNT(DISTINCT f.sales_key)              AS transactions,
    SUM(f.quantity)                          AS units_sold,
    ROUND(SUM(f.gross_revenue)/10000000,2)   AS revenue_crore,
    ROUND(SUM(f.gross_profit)/10000000,2)    AS profit_crore,
    ROUND(AVG(f.profit_margin_pct),2)        AS avg_margin_pct,
    -- Revenue share within year
    ROUND(SUM(f.gross_revenue)*100.0
        / SUM(SUM(f.gross_revenue)) OVER (PARTITION BY d.year), 2) AS revenue_share_pct
FROM fact_sales f
JOIN dim_date    d ON f.date_key    = d.date_key
JOIN dim_product p ON f.product_key = p.product_key
WHERE f.return_flag = 0
GROUP BY d.year, d.quarter, p.category
ORDER BY d.year, d.quarter, revenue_crore DESC;


-- 1.2 Store performance with regional rollup (drill up/down)
SELECT
    s.region,
    s.state,
    s.city,
    s.store_format,
    s.store_tier,
    COUNT(DISTINCT f.sales_key)              AS transactions,
    COUNT(DISTINCT f.customer_key)           AS unique_customers,
    ROUND(SUM(f.gross_revenue)/10000000,2)   AS revenue_crore,
    ROUND(SUM(f.gross_profit)/10000000,2)    AS profit_crore,
    ROUND(AVG(f.profit_margin_pct),2)        AS avg_margin,
    ROUND(SUM(f.gross_revenue)/s.area_sqft,0) AS revenue_per_sqft,
    RANK() OVER (PARTITION BY s.region
                 ORDER BY SUM(f.gross_revenue) DESC) AS rank_in_region
FROM fact_sales f
JOIN dim_store s ON f.store_key = s.store_key
WHERE f.return_flag = 0
GROUP BY s.region, s.state, s.city, s.store_format,
         s.store_tier, s.area_sqft
ORDER BY s.region, revenue_crore DESC;


-- 1.3 Customer loyalty tier analysis
SELECT
    c.loyalty_tier,
    c.age_group,
    c.income_bracket,
    COUNT(DISTINCT f.customer_key)           AS customers,
    COUNT(DISTINCT f.sales_key)              AS transactions,
    ROUND(AVG(f.gross_revenue),0)            AS avg_basket_size,
    ROUND(SUM(f.gross_revenue)/10000000,2)   AS revenue_crore,
    ROUND(SUM(f.gross_revenue)/10000000,2)
        / COUNT(DISTINCT f.customer_key)     AS revenue_per_customer_crore,
    ROUND(AVG(f.profit_margin_pct),2)        AS avg_margin,
    -- Percentage of total revenue
    ROUND(SUM(f.gross_revenue)*100.0
        / SUM(SUM(f.gross_revenue)) OVER(), 2) AS revenue_share_pct
FROM fact_sales f
JOIN dim_customer c ON f.customer_key = c.customer_key
WHERE f.return_flag = 0
GROUP BY c.loyalty_tier, c.age_group, c.income_bracket
ORDER BY revenue_crore DESC;


-- 1.4 Promotion effectiveness analysis
SELECT
    p.promotion_name,
    p.promotion_type,
    p.discount_pct,
    COUNT(DISTINCT f.sales_key)              AS transactions,
    SUM(f.quantity)                          AS units_sold,
    ROUND(SUM(f.gross_revenue)/10000000,2)   AS revenue_crore,
    ROUND(AVG(f.gross_revenue),0)            AS avg_basket_size,
    ROUND(AVG(f.profit_margin_pct),2)        AS avg_margin_pct,
    ROUND(SUM(f.return_flag)*100.0/COUNT(*),2) AS return_rate_pct,
    -- Revenue lift vs no promotion
    ROUND(AVG(f.gross_revenue) /
        AVG(AVG(f.gross_revenue)) OVER() * 100, 1) AS basket_index
FROM fact_sales f
JOIN dim_promotion p ON f.promotion_key = p.promotion_key
GROUP BY p.promotion_name, p.promotion_type, p.discount_pct
ORDER BY revenue_crore DESC;


-- ----------------------------------------------------------------
-- SECTION 2: ADVANCED DWH ANALYTICS
-- ----------------------------------------------------------------

-- 2.1 YoY comparison using date dimension
WITH yearly AS (
    SELECT
        d.year,
        p.category,
        ROUND(SUM(f.gross_revenue)/10000000,2)   AS revenue_crore,
        ROUND(SUM(f.gross_profit)/10000000,2)    AS profit_crore
    FROM fact_sales f
    JOIN dim_date    d ON f.date_key    = d.date_key
    JOIN dim_product p ON f.product_key = p.product_key
    WHERE f.return_flag = 0
    GROUP BY d.year, p.category
)
SELECT
    y.year,
    y.category,
    y.revenue_crore,
    y.profit_crore,
    LAG(y.revenue_crore) OVER (PARTITION BY y.category ORDER BY y.year) AS prev_year,
    ROUND((y.revenue_crore - LAG(y.revenue_crore)
           OVER (PARTITION BY y.category ORDER BY y.year))
          / NULLIF(LAG(y.revenue_crore)
           OVER (PARTITION BY y.category ORDER BY y.year), 0) * 100, 2) AS yoy_growth
FROM yearly y
ORDER BY y.category, y.year;


-- 2.2 Rolling 3-month revenue using date dimension
WITH monthly AS (
    SELECT
        d.year_month,
        d.year,
        d.month_num,
        ROUND(SUM(f.gross_revenue)/10000000,3)  AS monthly_revenue
    FROM fact_sales f
    JOIN dim_date d ON f.date_key = d.date_key
    WHERE f.return_flag = 0
    GROUP BY d.year_month, d.year, d.month_num
)
SELECT
    year_month,
    monthly_revenue,
    ROUND(AVG(monthly_revenue) OVER (
        ORDER BY year, month_num
        ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
    ), 3)                                        AS rolling_3m_avg,
    ROUND(SUM(monthly_revenue) OVER (
        PARTITION BY year
        ORDER BY month_num
    ), 2)                                        AS ytd_revenue
FROM monthly
ORDER BY year, month_num;


-- 2.3 Product affinity — what categories appear in same transaction
-- (Simulated at store-day level for star schema)
WITH store_day_cats AS (
    SELECT
        f.store_key,
        d.full_date,
        p.category,
        ROUND(SUM(f.gross_revenue),2) AS daily_rev
    FROM fact_sales f
    JOIN dim_date    d ON f.date_key    = d.date_key
    JOIN dim_product p ON f.product_key = p.product_key
    WHERE f.return_flag = 0
    GROUP BY f.store_key, d.full_date, p.category
)
SELECT
    a.category AS category_a,
    b.category AS category_b,
    COUNT(*)   AS co_occurrence_days,
    ROUND(AVG(a.daily_rev + b.daily_rev)/10000,2) AS avg_combined_rev_lac
FROM store_day_cats a
JOIN store_day_cats b
    ON a.store_key = b.store_key
   AND a.full_date = b.full_date
   AND a.category  < b.category
GROUP BY a.category, b.category
ORDER BY co_occurrence_days DESC
LIMIT 15;


-- 2.4 Festival month vs non-festival uplift
SELECT
    d.is_festival_month,
    CASE WHEN d.is_festival_month=1 THEN 'Festival Month'
         ELSE 'Regular Month' END      AS period_type,
    COUNT(DISTINCT f.sales_key)        AS transactions,
    COUNT(DISTINCT f.customer_key)     AS unique_customers,
    ROUND(AVG(f.gross_revenue),0)      AS avg_basket_size,
    ROUND(SUM(f.gross_revenue)/10000000,2) AS revenue_crore,
    ROUND(AVG(f.profit_margin_pct),2)  AS avg_margin,
    ROUND(AVG(f.discount_pct),2)       AS avg_discount
FROM fact_sales f
JOIN dim_date d ON f.date_key = d.date_key
WHERE f.return_flag = 0
GROUP BY d.is_festival_month
ORDER BY d.is_festival_month DESC;


-- 2.5 Weekend vs weekday performance
SELECT
    d.day_of_week,
    d.is_weekend,
    COUNT(DISTINCT f.sales_key)          AS transactions,
    ROUND(AVG(f.gross_revenue),0)        AS avg_basket_size,
    ROUND(SUM(f.gross_revenue)/10000000,2) AS revenue_crore,
    ROUND(AVG(f.profit_margin_pct),2)    AS avg_margin,
    RANK() OVER (ORDER BY SUM(f.gross_revenue) DESC) AS day_rank
FROM fact_sales f
JOIN dim_date d ON f.date_key = d.date_key
WHERE f.return_flag = 0
GROUP BY d.day_of_week, d.is_weekend
ORDER BY revenue_crore DESC;


-- ----------------------------------------------------------------
-- SECTION 3: DWH-SPECIFIC PATTERNS
-- ----------------------------------------------------------------

-- 3.1 SCD Type 2 — Customer tier change tracking
-- Shows how customers moved across loyalty tiers
SELECT
    customer_id,
    full_name,
    loyalty_tier,
    scd_start_date,
    scd_end_date,
    is_current,
    -- Flag multi-record customers (had tier changes)
    COUNT(*) OVER (PARTITION BY customer_id) AS version_count
FROM dim_customer
ORDER BY customer_id, scd_start_date;


-- 3.2 Slowly Changing Dimension audit
SELECT
    loyalty_tier,
    COUNT(*) AS customer_versions,
    COUNT(CASE WHEN is_current=1 THEN 1 END) AS current_customers,
    COUNT(CASE WHEN scd_end_date='9999-12-31' THEN 1 END) AS active_records
FROM dim_customer
GROUP BY loyalty_tier
ORDER BY customer_versions DESC;


-- 3.3 ETL data lineage — row counts by batch
SELECT
    etl_batch_id,
    COUNT(*)                               AS records_loaded,
    ROUND(SUM(gross_revenue)/10000000,2)   AS revenue_crore,
    MIN(sale_date)                         AS earliest_sale,
    MAX(sale_date)                         AS latest_sale,
    COUNT(CASE WHEN return_flag=1 THEN 1 END) AS returns
FROM fact_sales
GROUP BY etl_batch_id
ORDER BY etl_batch_id
LIMIT 20;


-- 3.4 Data quality scorecard on fact table
SELECT
    COUNT(*)                                             AS total_records,
    COUNT(CASE WHEN gross_revenue <= 0 THEN 1 END)      AS zero_revenue,
    COUNT(CASE WHEN quantity <= 0 THEN 1 END)           AS zero_quantity,
    COUNT(CASE WHEN profit_margin_pct < -10 THEN 1 END) AS negative_margin,
    COUNT(CASE WHEN date_key IS NULL THEN 1 END)        AS null_date_key,
    COUNT(CASE WHEN customer_key IS NULL THEN 1 END)    AS null_customer_key,
    ROUND(COUNT(CASE WHEN gross_revenue > 0
                      AND quantity > 0
                      AND date_key IS NOT NULL THEN 1 END)
          *100.0/COUNT(*), 2)                           AS data_quality_score_pct
FROM fact_sales;


-- ----------------------------------------------------------------
-- SECTION 4: EXECUTIVE BI QUERIES
-- ----------------------------------------------------------------

-- 4.1 Executive KPI dashboard — single query
SELECT
    COUNT(DISTINCT f.sales_key)              AS total_transactions,
    COUNT(DISTINCT f.customer_key)           AS unique_customers,
    COUNT(DISTINCT f.store_key)              AS active_stores,
    COUNT(DISTINCT f.product_key)            AS products_sold,
    ROUND(SUM(f.gross_revenue)/10000000,2)   AS total_gmv_crore,
    ROUND(SUM(f.gross_profit)/10000000,2)    AS total_profit_crore,
    ROUND(AVG(f.profit_margin_pct),2)        AS avg_margin_pct,
    ROUND(AVG(f.gross_revenue),0)            AS avg_basket_size,
    SUM(f.return_flag)                       AS total_returns,
    ROUND(SUM(f.return_flag)*100.0/COUNT(*),2) AS return_rate_pct
FROM fact_sales f
WHERE f.return_flag = 0;


-- 4.2 Top 10 stores by revenue
SELECT
    s.store_name,
    s.city,
    s.state,
    s.store_format,
    ROUND(SUM(f.gross_revenue)/10000000,2)   AS revenue_crore,
    COUNT(DISTINCT f.customer_key)           AS customers,
    ROUND(AVG(f.profit_margin_pct),2)        AS avg_margin,
    RANK() OVER (ORDER BY SUM(f.gross_revenue) DESC) AS rank
FROM fact_sales f
JOIN dim_store s ON f.store_key = s.store_key
WHERE f.return_flag = 0
GROUP BY s.store_name, s.city, s.state, s.store_format
ORDER BY revenue_crore DESC
LIMIT 10;


-- 4.3 Price band analysis
SELECT
    p.price_band,
    p.category,
    COUNT(DISTINCT f.sales_key)              AS transactions,
    ROUND(AVG(f.gross_revenue),0)            AS avg_revenue,
    ROUND(SUM(f.gross_revenue)/10000000,2)   AS revenue_crore,
    ROUND(AVG(f.profit_margin_pct),2)        AS avg_margin,
    ROUND(SUM(f.return_flag)*100.0/COUNT(*),2) AS return_rate
FROM fact_sales f
JOIN dim_product p ON f.product_key = p.product_key
GROUP BY p.price_band, p.category
ORDER BY p.price_band, revenue_crore DESC;
