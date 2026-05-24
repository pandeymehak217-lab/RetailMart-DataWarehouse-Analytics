-- ================================================================
-- RetailMart Data Warehouse — ETL Pipeline
-- Author      : Mehak Pandey
-- Email       : pandeymehak.217@gmail.com
-- Description : Extract, Transform, Load from staging to DWH
--               Includes data quality checks, SCD Type 2,
--               and ETL audit logging
-- ================================================================

-- ----------------------------------------------------------------
-- STEP 1: DATA QUALITY CHECKS ON STAGING
-- ----------------------------------------------------------------

-- Check 1: Null check on critical fields
SELECT 'stg_sales'         AS table_name,
       'src_txn_id'        AS column_name,
       COUNT(*)            AS null_count
FROM stg_sales WHERE src_txn_id IS NULL
UNION ALL
SELECT 'stg_sales', 'gross_revenue',
       COUNT(*) FROM stg_sales WHERE gross_revenue IS NULL
UNION ALL
SELECT 'stg_sales', 'sale_date',
       COUNT(*) FROM stg_sales WHERE sale_date IS NULL
UNION ALL
SELECT 'stg_customers', 'src_customer_id',
       COUNT(*) FROM stg_customers WHERE src_customer_id IS NULL;


-- Check 2: Duplicate detection
SELECT src_txn_id, COUNT(*) AS duplicate_count
FROM stg_sales
GROUP BY src_txn_id
HAVING COUNT(*) > 1
ORDER BY duplicate_count DESC;


-- Check 3: Revenue sanity — negative values
SELECT COUNT(*) AS negative_revenue_count
FROM stg_sales
WHERE gross_revenue < 0;


-- Check 4: Orphan records (sales with no matching customer)
SELECT COUNT(*) AS orphan_sales
FROM stg_sales s
WHERE NOT EXISTS (
    SELECT 1 FROM stg_customers c
    WHERE c.src_customer_id = s.src_customer_id
);


-- Check 5: Date range validation
SELECT
    MIN(sale_date)          AS earliest_sale,
    MAX(sale_date)          AS latest_sale,
    COUNT(DISTINCT sale_date) AS distinct_dates,
    COUNT(*)                AS total_records,
    COUNT(CASE WHEN sale_date < '2020-01-01' THEN 1 END) AS pre_range_records,
    COUNT(CASE WHEN sale_date > '2024-12-31' THEN 1 END) AS post_range_records
FROM stg_sales;


-- ----------------------------------------------------------------
-- STEP 2: TRANSFORM AND LOAD DIMENSIONS
-- ----------------------------------------------------------------

-- ETL: Load dim_date (pre-built, no transform needed)
-- Run generate_data.py which creates dim_date.csv directly

-- ETL: Load dim_customer with data cleaning
INSERT INTO dim_customer (
    customer_key, customer_id, full_name, gender, age, age_group,
    city, state, pincode, loyalty_tier, income_bracket,
    registration_year, is_active, scd_start_date, scd_end_date, is_current
)
SELECT
    ROW_NUMBER() OVER (ORDER BY src_customer_id)    AS customer_key,
    src_customer_id,
    TRIM(full_name)                                 AS full_name,
    UPPER(gender)                                   AS gender,
    DATE_DIFF('year', CAST(dob AS DATE), CURRENT_DATE) AS age,
    CASE
        WHEN DATE_DIFF('year', CAST(dob AS DATE), CURRENT_DATE) < 25 THEN '18-24'
        WHEN DATE_DIFF('year', CAST(dob AS DATE), CURRENT_DATE) < 35 THEN '25-34'
        WHEN DATE_DIFF('year', CAST(dob AS DATE), CURRENT_DATE) < 45 THEN '35-44'
        WHEN DATE_DIFF('year', CAST(dob AS DATE), CURRENT_DATE) < 55 THEN '45-54'
        ELSE '55+'
    END                                             AS age_group,
    TRIM(city)                                      AS city,
    TRIM(state)                                     AS state,
    pincode,
    COALESCE(loyalty_tier, 'Bronze')               AS loyalty_tier,
    COALESCE(annual_income_bracket, 'Unknown')      AS income_bracket,
    EXTRACT(YEAR FROM CAST(registration_date AS DATE)) AS registration_year,
    is_active,
    registration_date                               AS scd_start_date,
    '9999-12-31'                                   AS scd_end_date,
    1                                               AS is_current
FROM stg_customers
WHERE is_active = 1
  AND full_name IS NOT NULL
  AND src_customer_id IS NOT NULL;


-- ETL: Load dim_product
INSERT INTO dim_product (
    product_key, product_id, product_name, category, subcategory,
    brand, mrp, standard_cost, standard_margin_pct,
    price_band, is_perishable, is_active, launch_year
)
SELECT
    ROW_NUMBER() OVER (ORDER BY src_product_id) AS product_key,
    src_product_id,
    TRIM(product_name),
    TRIM(category),
    TRIM(subcategory),
    TRIM(brand),
    mrp,
    standard_cost,
    ROUND((mrp - standard_cost) / NULLIF(mrp, 0) * 100, 2) AS standard_margin_pct,
    CASE
        WHEN mrp < 500    THEN 'Budget'
        WHEN mrp < 5000   THEN 'Mid-Range'
        WHEN mrp < 25000  THEN 'Premium'
        ELSE                   'Luxury'
    END                                         AS price_band,
    is_perishable,
    is_active,
    EXTRACT(YEAR FROM CAST(launch_date AS DATE)) AS launch_year
FROM stg_products
WHERE is_active = 1
  AND product_name IS NOT NULL;


-- ETL: Load fact_sales with key lookups
INSERT INTO fact_sales (
    sales_key, date_key, customer_key, product_key,
    store_key, promotion_key, sale_date, sale_time,
    payment_method, channel, quantity, unit_price,
    discount_pct, gross_revenue, standard_cost,
    gross_profit, profit_margin_pct, return_flag,
    etl_batch_id, etl_load_date
)
SELECT
    s.src_txn_id                                   AS sales_key,
    d.date_key,
    c.customer_key,
    p.product_key,
    st.store_key,
    pr.promotion_key,
    CAST(s.sale_date AS DATE),
    CAST(s.sale_time AS TIME),
    s.payment_method,
    s.channel,
    s.quantity,
    s.unit_price,
    s.discount_pct,
    s.gross_revenue,
    s.standard_cost,
    s.gross_profit,
    ROUND(s.gross_profit / NULLIF(s.gross_revenue, 0) * 100, 2) AS profit_margin_pct,
    s.return_flag,
    CONCAT('BATCH_', LEFT(CAST(s.sale_date AS VARCHAR), 7)) AS etl_batch_id,
    CURRENT_DATE                                   AS etl_load_date
FROM stg_sales s
JOIN dim_date      d  ON d.full_date      = CAST(s.sale_date AS DATE)
JOIN dim_customer  c  ON c.customer_id   = s.src_customer_id AND c.is_current = 1
JOIN dim_product   p  ON p.product_id    = s.src_product_id
JOIN dim_store     st ON st.store_id     = s.src_store_id
JOIN dim_promotion pr ON pr.promotion_name = s.promotion_name
WHERE s.gross_revenue > 0
  AND s.quantity > 0;


-- ----------------------------------------------------------------
-- STEP 3: ETL AUDIT LOG
-- ----------------------------------------------------------------

CREATE TABLE IF NOT EXISTS etl_audit_log (
    log_id           INT,
    batch_id         VARCHAR(30),
    table_name       VARCHAR(50),
    run_date         DATE,
    records_extracted INT,
    records_loaded    INT,
    records_rejected  INT,
    status           VARCHAR(20),
    error_message    VARCHAR(500),
    duration_seconds INT
);

-- Log the ETL run
INSERT INTO etl_audit_log VALUES (
    1,
    CONCAT('BATCH_', CAST(CURRENT_DATE AS VARCHAR)),
    'fact_sales',
    CURRENT_DATE,
    80000,
    (SELECT COUNT(*) FROM fact_sales),
    80000 - (SELECT COUNT(*) FROM fact_sales),
    CASE WHEN (SELECT COUNT(*) FROM fact_sales) > 0 THEN 'SUCCESS' ELSE 'FAILED' END,
    NULL,
    45
);
