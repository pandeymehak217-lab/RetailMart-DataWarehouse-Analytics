-- ================================================================
-- RetailMart Data Warehouse — DDL Schema
-- Author      : Mehak Pandey
-- Email       : pandeymehak.217@gmail.com
-- Architecture: Kimball Star Schema
-- Database    : PostgreSQL / DuckDB
-- ================================================================

-- ----------------------------------------------------------------
-- STAGING SCHEMA — Raw source data landing zone
-- ----------------------------------------------------------------

CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS dimensions;
CREATE SCHEMA IF NOT EXISTS facts;
CREATE SCHEMA IF NOT EXISTS analytics;

-- Staging: Customers (source: CRM system)
CREATE TABLE staging.stg_customers (
    src_customer_id      INT,
    full_name            VARCHAR(100),
    email                VARCHAR(100),
    phone                VARCHAR(20),
    dob                  DATE,
    gender               CHAR(1),
    city                 VARCHAR(50),
    state                VARCHAR(50),
    pincode              INT,
    registration_date    DATE,
    loyalty_tier         VARCHAR(20),
    annual_income_bracket VARCHAR(10),
    is_active            INT,
    etl_load_date        DATE
);

-- Staging: Products (source: ERP system)
CREATE TABLE staging.stg_products (
    src_product_id       INT,
    product_name         VARCHAR(200),
    category             VARCHAR(50),
    subcategory          VARCHAR(50),
    brand                VARCHAR(50),
    mrp                  DECIMAL(12,2),
    standard_cost        DECIMAL(12,2),
    weight_kg            DECIMAL(6,2),
    is_perishable        INT,
    reorder_level        INT,
    supplier_code        VARCHAR(20),
    launch_date          DATE,
    is_active            INT,
    etl_load_date        DATE
);

-- Staging: Stores (source: Retail Management System)
CREATE TABLE staging.stg_stores (
    src_store_id         INT,
    store_name           VARCHAR(100),
    store_format         VARCHAR(30),
    city                 VARCHAR(50),
    state                VARCHAR(50),
    store_tier           VARCHAR(10),
    area_sqft            INT,
    opening_date         DATE,
    manager_name         VARCHAR(100),
    staff_count          INT,
    monthly_rent_lakh    DECIMAL(8,2),
    has_parking          INT,
    is_active            INT,
    etl_load_date        DATE
);

-- Staging: Sales (source: POS system)
CREATE TABLE staging.stg_sales (
    src_txn_id           INT,
    sale_date            DATE,
    sale_time            TIME,
    src_customer_id      INT,
    src_product_id       INT,
    src_store_id         INT,
    promotion_name       VARCHAR(50),
    quantity             INT,
    unit_price           DECIMAL(12,2),
    discount_pct         DECIMAL(5,2),
    gross_revenue        DECIMAL(14,2),
    standard_cost        DECIMAL(14,2),
    gross_profit         DECIMAL(14,2),
    payment_method       VARCHAR(30),
    channel              VARCHAR(20),
    return_flag          INT,
    etl_load_date        DATE
);

-- ----------------------------------------------------------------
-- DIMENSION TABLES — Conformed dimensions (Kimball methodology)
-- ----------------------------------------------------------------

-- Dimension: Date (pre-populated, no ETL needed)
CREATE TABLE dimensions.dim_date (
    date_key             INT         PRIMARY KEY,
    full_date            DATE        NOT NULL,
    day_of_week          VARCHAR(10),
    day_of_week_num      INT,
    day_of_month         INT,
    day_of_year          INT,
    week_of_year         INT,
    month_num            INT,
    month_name           VARCHAR(10),
    month_short          VARCHAR(3),
    quarter              VARCHAR(2),
    quarter_num          INT,
    year                 INT,
    year_month           VARCHAR(7),
    is_weekend           INT,
    is_month_start       INT,
    is_month_end         INT,
    fiscal_year          INT,
    fiscal_quarter       VARCHAR(3),
    season               VARCHAR(10),
    is_festival_month    INT
);

-- Dimension: Customer (SCD Type 2)
CREATE TABLE dimensions.dim_customer (
    customer_key         INT         PRIMARY KEY,
    customer_id          INT         NOT NULL,
    full_name            VARCHAR(100),
    gender               CHAR(1),
    age                  INT,
    age_group            VARCHAR(10),
    city                 VARCHAR(50),
    state                VARCHAR(50),
    pincode              INT,
    loyalty_tier         VARCHAR(20),
    income_bracket       VARCHAR(10),
    registration_year    INT,
    is_active            INT,
    -- SCD Type 2 columns
    scd_start_date       DATE,
    scd_end_date         DATE,
    is_current           INT
);

-- Dimension: Product
CREATE TABLE dimensions.dim_product (
    product_key          INT         PRIMARY KEY,
    product_id           INT         NOT NULL,
    product_name         VARCHAR(200),
    category             VARCHAR(50),
    subcategory          VARCHAR(50),
    brand                VARCHAR(50),
    mrp                  DECIMAL(12,2),
    standard_cost        DECIMAL(12,2),
    standard_margin_pct  DECIMAL(6,2),
    price_band           VARCHAR(20),
    is_perishable        INT,
    is_active            INT,
    launch_year          INT
);

-- Dimension: Store
CREATE TABLE dimensions.dim_store (
    store_key            INT         PRIMARY KEY,
    store_id             INT         NOT NULL,
    store_name           VARCHAR(100),
    store_format         VARCHAR(30),
    city                 VARCHAR(50),
    state                VARCHAR(50),
    store_tier           VARCHAR(10),
    region               VARCHAR(10),
    area_sqft            INT,
    opening_year         INT,
    staff_count          INT,
    monthly_rent_lakh    DECIMAL(8,2),
    has_parking          INT,
    is_active            INT
);

-- Dimension: Promotion
CREATE TABLE dimensions.dim_promotion (
    promotion_key        INT         PRIMARY KEY,
    promotion_name       VARCHAR(50),
    promotion_type       VARCHAR(30),
    discount_pct         DECIMAL(5,2),
    is_active_promo      INT,
    channel              VARCHAR(20)
);

-- ----------------------------------------------------------------
-- FACT TABLE — Central fact table (grain: one row per line item)
-- ----------------------------------------------------------------

CREATE TABLE facts.fact_sales (
    sales_key            INT         PRIMARY KEY,
    -- Foreign keys to dimensions
    date_key             INT         REFERENCES dimensions.dim_date(date_key),
    customer_key         INT         REFERENCES dimensions.dim_customer(customer_key),
    product_key          INT         REFERENCES dimensions.dim_product(product_key),
    store_key            INT         REFERENCES dimensions.dim_store(store_key),
    promotion_key        INT         REFERENCES dimensions.dim_promotion(promotion_key),
    -- Degenerate dimensions
    sale_date            DATE,
    sale_time            TIME,
    payment_method       VARCHAR(30),
    channel              VARCHAR(20),
    -- Measures (additive facts)
    quantity             INT,
    unit_price           DECIMAL(12,2),
    discount_pct         DECIMAL(5,2),
    gross_revenue        DECIMAL(14,2),
    standard_cost        DECIMAL(14,2),
    gross_profit         DECIMAL(14,2),
    profit_margin_pct    DECIMAL(6,2),
    return_flag          INT,
    -- ETL metadata
    etl_batch_id         VARCHAR(20),
    etl_load_date        DATE
);

-- Indexes for query performance
CREATE INDEX idx_fact_date_key     ON facts.fact_sales(date_key);
CREATE INDEX idx_fact_customer_key ON facts.fact_sales(customer_key);
CREATE INDEX idx_fact_product_key  ON facts.fact_sales(product_key);
CREATE INDEX idx_fact_store_key    ON facts.fact_sales(store_key);
CREATE INDEX idx_fact_sale_date    ON facts.fact_sales(sale_date);

-- ----------------------------------------------------------------
-- ANALYTICS VIEWS — Pre-built for BI tools
-- ----------------------------------------------------------------

-- View: Daily sales summary
CREATE VIEW analytics.v_daily_sales AS
SELECT
    d.full_date,
    d.year,
    d.month_name,
    d.quarter,
    d.is_weekend,
    d.is_festival_month,
    COUNT(DISTINCT f.sales_key)          AS transactions,
    SUM(f.quantity)                      AS units_sold,
    ROUND(SUM(f.gross_revenue),2)        AS gross_revenue,
    ROUND(SUM(f.gross_profit),2)         AS gross_profit,
    ROUND(AVG(f.profit_margin_pct),2)    AS avg_margin_pct,
    SUM(f.return_flag)                   AS returns
FROM facts.fact_sales f
JOIN dimensions.dim_date d ON f.date_key = d.date_key
GROUP BY d.full_date, d.year, d.month_name, d.quarter,
         d.is_weekend, d.is_festival_month;

-- View: Category performance
CREATE VIEW analytics.v_category_performance AS
SELECT
    p.category,
    p.subcategory,
    d.year,
    d.quarter,
    COUNT(DISTINCT f.sales_key)          AS transactions,
    ROUND(SUM(f.gross_revenue)/10000000,2) AS revenue_crore,
    ROUND(SUM(f.gross_profit)/10000000,2)  AS profit_crore,
    ROUND(AVG(f.profit_margin_pct),2)    AS avg_margin_pct
FROM facts.fact_sales f
JOIN dimensions.dim_product p ON f.product_key = p.product_key
JOIN dimensions.dim_date d    ON f.date_key    = d.date_key
GROUP BY p.category, p.subcategory, d.year, d.quarter;

-- View: Store performance
CREATE VIEW analytics.v_store_performance AS
SELECT
    s.store_name, s.city, s.state, s.region,
    s.store_format, s.store_tier,
    d.year,
    COUNT(DISTINCT f.sales_key)             AS transactions,
    ROUND(SUM(f.gross_revenue)/10000000,2)  AS revenue_crore,
    ROUND(SUM(f.gross_profit)/10000000,2)   AS profit_crore,
    ROUND(AVG(f.profit_margin_pct),2)       AS avg_margin_pct,
    COUNT(DISTINCT f.customer_key)          AS unique_customers
FROM facts.fact_sales f
JOIN dimensions.dim_store s ON f.store_key = s.store_key
JOIN dimensions.dim_date d  ON f.date_key  = d.date_key
GROUP BY s.store_name, s.city, s.state, s.region,
         s.store_format, s.store_tier, d.year;
