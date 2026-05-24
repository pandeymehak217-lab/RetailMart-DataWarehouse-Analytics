"""
RetailMart Data Warehouse — Staging Data Generator
Author : Mehak Pandey
Email  : pandeymehak.217@gmail.com

Architecture : Kimball Star Schema
               1 Fact Table (fact_sales)
               6 Dimension Tables (dim_date, dim_customer,
                 dim_product, dim_store, dim_promotion, dim_employee)
               Staging layer for ETL simulation
"""
import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta, date

random.seed(33)
np.random.seed(33)

STAGING = '/Users/mehekpandey/datawarehouse_project/data/staging'
DIMS    = '/Users/mehekpandey/datawarehouse_project/data/dimensions'
FACTS   = '/Users/mehekpandey/datawarehouse_project/data/facts'

# ── Reference Data ─────────────────────────────────────────
STATES = ['Maharashtra','Karnataka','Delhi','Tamil Nadu','Telangana',
          'Gujarat','Rajasthan','West Bengal','Uttar Pradesh','Kerala']

CITIES = {
    'Maharashtra':  ['Mumbai','Pune','Nagpur'],
    'Karnataka':    ['Bengaluru','Mysuru','Hubli'],
    'Delhi':        ['New Delhi','Noida','Gurgaon'],
    'Tamil Nadu':   ['Chennai','Coimbatore','Madurai'],
    'Telangana':    ['Hyderabad','Warangal','Karimnagar'],
    'Gujarat':      ['Ahmedabad','Surat','Vadodara'],
    'Rajasthan':    ['Jaipur','Jodhpur','Udaipur'],
    'West Bengal':  ['Kolkata','Howrah','Durgapur'],
    'Uttar Pradesh':['Lucknow','Kanpur','Agra'],
    'Kerala':       ['Kochi','Thiruvananthapuram','Kozhikode'],
}

CATEGORIES = {
    'Electronics':    ['Mobile Phones','Laptops','Tablets','Headphones','Smart TV'],
    'Fashion':        ['Men Clothing','Women Clothing','Footwear','Accessories'],
    'Home & Kitchen': ['Cookware','Furniture','Appliances','Bedding'],
    'Grocery':        ['Staples','Beverages','Snacks','Dairy'],
    'Sports':         ['Fitness Equipment','Outdoor','Cricket','Football'],
    'Beauty':         ['Skincare','Haircare','Makeup','Fragrances'],
}

STORE_FORMATS = ['Hypermarket','Supermarket','Express','Online']
STORE_TIERS   = ['Tier 1','Tier 2','Tier 3']

PROMOTIONS = [
    ('Diwali Sale','Festival',40),
    ('Republic Day','National Holiday',25),
    ('End of Season','Clearance',50),
    ('Weekend Special','Regular',15),
    ('New Year Sale','Festival',30),
    ('Flash Sale','Flash',60),
    ('Member Exclusive','Loyalty',20),
    ('No Promotion','None',0),
    ('No Promotion','None',0),
    ('No Promotion','None',0),
]

PAYMENT_METHODS = ['Cash','Credit Card','Debit Card','UPI','EMI','Gift Card']
CHANNELS        = ['In-Store','Online','Mobile App']

first_names = ['Aarav','Aditi','Aditya','Akash','Ananya','Anjali','Arjun',
               'Deepika','Divya','Ishaan','Isha','Karan','Kavya','Meera',
               'Priya','Rahul','Riya','Rohit','Sanjay','Shreya','Tanvi',
               'Varun','Vikram','Yash','Amit','Pooja','Rajesh','Sunita']
last_names  = ['Sharma','Patel','Singh','Gupta','Kumar','Verma','Joshi',
               'Nair','Reddy','Mehta','Shah','Iyer','Rao','Malhotra']

def rand_date(s, e):
    s = datetime.strptime(s,'%Y-%m-%d')
    e = datetime.strptime(e,'%Y-%m-%d')
    return s + timedelta(seconds=random.randint(0,int((e-s).total_seconds())))

# ════════════════════════════════════════════════════════════
# STAGING LAYER — Raw source data (simulates source systems)
# ════════════════════════════════════════════════════════════

# Staging: raw customers (simulates CRM export)
stg_customers = []
for cid in range(1, 5001):
    state = random.choice(STATES)
    city  = random.choice(CITIES[state])
    reg   = rand_date('2018-01-01','2023-12-31')
    stg_customers.append({
        'src_customer_id':   cid,
        'full_name':         f'{random.choice(first_names)} {random.choice(last_names)}',
        'email':             f'cust{cid}@mail.com',
        'phone':             f'+91{random.randint(7000000000,9999999999)}',
        'dob':               rand_date('1965-01-01','2005-12-31').strftime('%Y-%m-%d'),
        'gender':            random.choices(['M','F','O'],weights=[52,46,2])[0],
        'city':              city,
        'state':             state,
        'pincode':           random.randint(100000,999999),
        'registration_date': reg.strftime('%Y-%m-%d'),
        'loyalty_tier':      random.choices(['Bronze','Silver','Gold','Platinum'],
                                            weights=[40,30,20,10])[0],
        'annual_income_bracket': random.choices(
            ['<3L','3-6L','6-10L','10-20L','>20L'],
            weights=[20,30,25,15,10])[0],
        'is_active':         random.choices([1,0],weights=[90,10])[0],
        'etl_load_date':     datetime.now().strftime('%Y-%m-%d'),
    })
stg_cust_df = pd.DataFrame(stg_customers)

# Staging: raw products (simulates ERP export)
stg_products = []
for pid in range(1, 1001):
    cat    = random.choice(list(CATEGORIES.keys()))
    subcat = random.choice(CATEGORIES[cat])
    price_ranges = {
        'Electronics':(500,120000), 'Fashion':(200,15000),
        'Home & Kitchen':(150,50000), 'Grocery':(50,2000),
        'Sports':(200,30000), 'Beauty':(100,5000),
    }
    lo,hi = price_ranges[cat]
    mrp   = round(random.uniform(lo,hi),0)
    cost  = round(mrp*random.uniform(0.4,0.65),0)
    stg_products.append({
        'src_product_id':    pid,
        'product_name':      f'{subcat} Model {random.randint(100,999)}',
        'category':          cat,
        'subcategory':       subcat,
        'brand':             f'Brand{random.randint(1,50):02d}',
        'mrp':               mrp,
        'standard_cost':     cost,
        'weight_kg':         round(random.uniform(0.1,20.0),2),
        'is_perishable':     1 if cat=='Grocery' else 0,
        'reorder_level':     random.randint(10,100),
        'supplier_code':     f'SUP{random.randint(1,100):03d}',
        'launch_date':       rand_date('2015-01-01','2023-01-01').strftime('%Y-%m-%d'),
        'is_active':         random.choices([1,0],weights=[93,7])[0],
        'etl_load_date':     datetime.now().strftime('%Y-%m-%d'),
    })
stg_prod_df = pd.DataFrame(stg_products)

# Staging: raw stores
stg_stores = []
for sid in range(1, 101):
    state = random.choice(STATES)
    city  = random.choice(CITIES[state])
    fmt   = random.choice(STORE_FORMATS)
    stg_stores.append({
        'src_store_id':      sid,
        'store_name':        f'RetailMart {city} {fmt}',
        'store_format':      fmt,
        'city':              city,
        'state':             state,
        'store_tier':        random.choice(STORE_TIERS),
        'area_sqft':         random.randint(500,50000),
        'opening_date':      rand_date('2005-01-01','2022-01-01').strftime('%Y-%m-%d'),
        'manager_name':      f'{random.choice(first_names)} {random.choice(last_names)}',
        'staff_count':       random.randint(10,200),
        'monthly_rent_lakh': round(random.uniform(0.5,20.0),2),
        'has_parking':       random.choice([1,0]),
        'is_active':         random.choices([1,0],weights=[92,8])[0],
        'etl_load_date':     datetime.now().strftime('%Y-%m-%d'),
    })
stg_store_df = pd.DataFrame(stg_stores)

# Staging: raw sales transactions
stg_sales = []
for tid in range(1, 80001):
    sale_dt = rand_date('2020-01-01','2024-12-31')
    prod    = random.choice(stg_products)
    cust    = random.choice(stg_customers)
    store   = random.choice(stg_stores)
    promo   = random.choice(PROMOTIONS)
    qty     = random.choices([1,2,3,4,5],weights=[55,25,10,7,3])[0]
    disc_pct= promo[2]
    unit_price = round(prod['mrp']*(1-disc_pct/100),2)
    revenue    = round(unit_price*qty,2)
    cost       = round(prod['standard_cost']*qty,2)
    profit     = round(revenue-cost,2)

    stg_sales.append({
        'src_txn_id':        tid,
        'sale_date':         sale_dt.strftime('%Y-%m-%d'),
        'sale_time':         sale_dt.strftime('%H:%M:%S'),
        'src_customer_id':   cust['src_customer_id'],
        'src_product_id':    prod['src_product_id'],
        'src_store_id':      store['src_store_id'],
        'promotion_name':    promo[0],
        'quantity':          qty,
        'unit_price':        unit_price,
        'discount_pct':      disc_pct,
        'gross_revenue':     revenue,
        'standard_cost':     cost,
        'gross_profit':      profit,
        'payment_method':    random.choice(PAYMENT_METHODS),
        'channel':           random.choices(CHANNELS,weights=[50,30,20])[0],
        'return_flag':       random.choices([0,1],weights=[91,9])[0],
        'etl_load_date':     datetime.now().strftime('%Y-%m-%d'),
    })
stg_sales_df = pd.DataFrame(stg_sales)

# Save staging
stg_cust_df.to_csv(f'{STAGING}/stg_customers.csv',index=False)
stg_prod_df.to_csv(f'{STAGING}/stg_products.csv',index=False)
stg_store_df.to_csv(f'{STAGING}/stg_stores.csv',index=False)
stg_sales_df.to_csv(f'{STAGING}/stg_sales.csv',index=False)

print("STAGING LAYER:")
print(f"  stg_customers : {len(stg_cust_df):,} rows")
print(f"  stg_products  : {len(stg_prod_df):,} rows")
print(f"  stg_stores    : {len(stg_store_df):,} rows")
print(f"  stg_sales     : {len(stg_sales_df):,} rows")

# ════════════════════════════════════════════════════════════
# DIMENSION TABLES — Conformed dimensions (Kimball methodology)
# ════════════════════════════════════════════════════════════

# DIM DATE — Date dimension (standard in every DWH)
dates = []
start = date(2020,1,1)
end   = date(2024,12,31)
d     = start
while d <= end:
    dates.append({
        'date_key':       int(d.strftime('%Y%m%d')),
        'full_date':      d.strftime('%Y-%m-%d'),
        'day_of_week':    d.strftime('%A'),
        'day_of_week_num':d.isoweekday(),
        'day_of_month':   d.day,
        'day_of_year':    d.timetuple().tm_yday,
        'week_of_year':   d.isocalendar()[1],
        'month_num':      d.month,
        'month_name':     d.strftime('%B'),
        'month_short':    d.strftime('%b'),
        'quarter':        f'Q{(d.month-1)//3+1}',
        'quarter_num':    (d.month-1)//3+1,
        'year':           d.year,
        'year_month':     d.strftime('%Y-%m'),
        'is_weekend':     1 if d.isoweekday() >= 6 else 0,
        'is_month_start': 1 if d.day == 1 else 0,
        'is_month_end':   1 if (d+timedelta(days=1)).month != d.month else 0,
        'fiscal_year':    d.year if d.month >= 4 else d.year-1,
        'fiscal_quarter': f'FQ{((d.month-4)%12)//3+1}',
        'season':         ('Winter' if d.month in [12,1,2]
                           else 'Spring' if d.month in [3,4,5]
                           else 'Summer' if d.month in [6,7,8]
                           else 'Autumn'),
        'is_festival_month': 1 if d.month in [10,11] else 0,
    })
    d += timedelta(days=1)
dim_date_df = pd.DataFrame(dates)

# DIM CUSTOMER — SCD Type 2 simulation
dim_customers = []
for i, row in stg_cust_df.iterrows():
    dob = datetime.strptime(row['dob'],'%Y-%m-%d')
    age = (datetime(2024,12,31)-dob).days // 365
    dim_customers.append({
        'customer_key':     i+1,
        'customer_id':      row['src_customer_id'],
        'full_name':        row['full_name'],
        'gender':           row['gender'],
        'age':              age,
        'age_group':        ('18-24' if age<25 else '25-34' if age<35
                             else '35-44' if age<45 else '45-54' if age<55 else '55+'),
        'city':             row['city'],
        'state':            row['state'],
        'pincode':          row['pincode'],
        'loyalty_tier':     row['loyalty_tier'],
        'income_bracket':   row['annual_income_bracket'],
        'registration_year':datetime.strptime(row['registration_date'],'%Y-%m-%d').year,
        'is_active':        row['is_active'],
        'scd_start_date':   row['registration_date'],
        'scd_end_date':     '9999-12-31',
        'is_current':       1,
    })
dim_cust_df = pd.DataFrame(dim_customers)

# DIM PRODUCT
dim_products = []
for i, row in stg_prod_df.iterrows():
    margin = round((row['mrp']-row['standard_cost'])/row['mrp']*100,2)
    dim_products.append({
        'product_key':      i+1,
        'product_id':       row['src_product_id'],
        'product_name':     row['product_name'],
        'category':         row['category'],
        'subcategory':      row['subcategory'],
        'brand':            row['brand'],
        'mrp':              row['mrp'],
        'standard_cost':    row['standard_cost'],
        'standard_margin_pct': margin,
        'price_band':       ('Budget' if row['mrp']<500
                             else 'Mid-Range' if row['mrp']<5000
                             else 'Premium' if row['mrp']<25000
                             else 'Luxury'),
        'is_perishable':    row['is_perishable'],
        'is_active':        row['is_active'],
        'launch_year':      datetime.strptime(row['launch_date'],'%Y-%m-%d').year,
    })
dim_prod_df = pd.DataFrame(dim_products)

# DIM STORE
dim_stores = []
for i, row in stg_store_df.iterrows():
    dim_stores.append({
        'store_key':        i+1,
        'store_id':         row['src_store_id'],
        'store_name':       row['store_name'],
        'store_format':     row['store_format'],
        'city':             row['city'],
        'state':            row['state'],
        'store_tier':       row['store_tier'],
        'area_sqft':        row['area_sqft'],
        'opening_year':     datetime.strptime(row['opening_date'],'%Y-%m-%d').year,
        'staff_count':      row['staff_count'],
        'monthly_rent_lakh':row['monthly_rent_lakh'],
        'has_parking':      row['has_parking'],
        'is_active':        row['is_active'],
        'region':           ('West'   if row['state'] in ['Maharashtra','Gujarat','Rajasthan']
                             else 'South' if row['state'] in ['Karnataka','Tamil Nadu','Telangana','Kerala']
                             else 'North' if row['state'] in ['Delhi','Uttar Pradesh']
                             else 'East'),
    })
dim_store_df = pd.DataFrame(dim_stores)

# DIM PROMOTION
dim_promotions = []
promo_seen = {}
for name, promo_type, disc in PROMOTIONS:
    if name not in promo_seen:
        dim_promotions.append({
            'promotion_key':    len(dim_promotions)+1,
            'promotion_name':   name,
            'promotion_type':   promo_type,
            'discount_pct':     disc,
            'is_active_promo':  0 if name=='No Promotion' else 1,
            'channel':          random.choices(['All','Online','In-Store'],weights=[60,25,15])[0],
        })
        promo_seen[name] = len(dim_promotions)
dim_promo_df = pd.DataFrame(dim_promotions)

# FACT SALES — Central fact table with foreign keys
date_key_map   = {row['full_date']:row['date_key'] for _,row in dim_date_df.iterrows()}
cust_key_map   = {row['customer_id']:row['customer_key'] for _,row in dim_cust_df.iterrows()}
prod_key_map   = {row['product_id']:row['product_key'] for _,row in dim_prod_df.iterrows()}
store_key_map  = {row['store_id']:row['store_key'] for _,row in dim_store_df.iterrows()}
promo_key_map  = {row['promotion_name']:row['promotion_key'] for _,row in dim_promo_df.iterrows()}

fact_sales = []
for _, row in stg_sales_df.iterrows():
    fact_sales.append({
        'sales_key':        row['src_txn_id'],
        'date_key':         date_key_map.get(row['sale_date'],20200101),
        'customer_key':     cust_key_map.get(row['src_customer_id'],1),
        'product_key':      prod_key_map.get(row['src_product_id'],1),
        'store_key':        store_key_map.get(row['src_store_id'],1),
        'promotion_key':    promo_key_map.get(row['promotion_name'],1),
        'sale_date':        row['sale_date'],
        'sale_time':        row['sale_time'],
        'quantity':         row['quantity'],
        'unit_price':       row['unit_price'],
        'discount_pct':     row['discount_pct'],
        'gross_revenue':    row['gross_revenue'],
        'standard_cost':    row['standard_cost'],
        'gross_profit':     row['gross_profit'],
        'profit_margin_pct':round(row['gross_profit']/row['gross_revenue']*100,2) if row['gross_revenue']>0 else 0,
        'payment_method':   row['payment_method'],
        'channel':          row['channel'],
        'return_flag':      row['return_flag'],
        'etl_batch_id':     f'BATCH_{row["sale_date"][:7]}',
        'etl_load_date':    row['etl_load_date'],
    })
fact_df = pd.DataFrame(fact_sales)

# Save dimensions and facts
dim_date_df.to_csv(f'{DIMS}/dim_date.csv',index=False)
dim_cust_df.to_csv(f'{DIMS}/dim_customer.csv',index=False)
dim_prod_df.to_csv(f'{DIMS}/dim_product.csv',index=False)
dim_store_df.to_csv(f'{DIMS}/dim_store.csv',index=False)
dim_promo_df.to_csv(f'{DIMS}/dim_promotion.csv',index=False)
fact_df.to_csv(f'{FACTS}/fact_sales.csv',index=False)

print("\nDIMENSION TABLES:")
print(f"  dim_date      : {len(dim_date_df):,} rows")
print(f"  dim_customer  : {len(dim_cust_df):,} rows")
print(f"  dim_product   : {len(dim_prod_df):,} rows")
print(f"  dim_store     : {len(dim_store_df):,} rows")
print(f"  dim_promotion : {len(dim_promo_df):,} rows")
print(f"\nFACT TABLE:")
print(f"  fact_sales    : {len(fact_df):,} rows")
print(f"\nTotal GMV     : Rs {fact_df['gross_revenue'].sum()/10000000:.1f} Crore")
print(f"Total Profit  : Rs {fact_df['gross_profit'].sum()/10000000:.1f} Crore")
print(f"Avg Margin    : {fact_df['profit_margin_pct'].mean():.1f}%")
