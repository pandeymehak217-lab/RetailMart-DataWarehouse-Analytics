"""
RetailMart Data Warehouse — Python Analytics
Author : Mehak Pandey
Email  : pandeymehak.217@gmail.com
"""
import duckdb
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import warnings
warnings.filterwarnings('ignore')

DIMS  = '/Users/mehekpandey/datawarehouse_project/data/dimensions'
FACTS = '/Users/mehekpandey/datawarehouse_project/data/facts'
OUT   = '/Users/mehekpandey/datawarehouse_project/outputs'

con = duckdb.connect()
con.execute(f"CREATE TABLE dim_date      AS SELECT * FROM read_csv_auto('{DIMS}/dim_date.csv')")
con.execute(f"CREATE TABLE dim_customer  AS SELECT * FROM read_csv_auto('{DIMS}/dim_customer.csv')")
con.execute(f"CREATE TABLE dim_product   AS SELECT * FROM read_csv_auto('{DIMS}/dim_product.csv')")
con.execute(f"CREATE TABLE dim_store     AS SELECT * FROM read_csv_auto('{DIMS}/dim_store.csv')")
con.execute(f"CREATE TABLE dim_promotion AS SELECT * FROM read_csv_auto('{DIMS}/dim_promotion.csv')")
con.execute(f"CREATE TABLE fact_sales    AS SELECT * FROM read_csv_auto('{FACTS}/fact_sales.csv')")
print("Star schema loaded.")

def q(sql): return con.execute(sql).df()

RED    = '#C0392B'
YELLOW = '#F39C12'
GREEN  = '#27AE60'
DARK   = '#2C3E50'
LIGHT  = '#F5F6FA'
BLUE   = '#2980B9'

# ── Analytics Queries ──────────────────────────────────────
kpi = q("""
    SELECT COUNT(DISTINCT f.sales_key) AS txns,
           COUNT(DISTINCT f.customer_key) AS customers,
           ROUND(SUM(f.gross_revenue)/10000000,2) AS gmv_crore,
           ROUND(SUM(f.gross_profit)/10000000,2) AS profit_crore,
           ROUND(AVG(f.profit_margin_pct),2) AS avg_margin,
           ROUND(AVG(f.gross_revenue),0) AS avg_basket,
           ROUND(SUM(f.return_flag)*100.0/COUNT(*),2) AS return_rate
    FROM fact_sales f WHERE f.return_flag=0
""")

yearly = q("""
    SELECT d.year,
           ROUND(SUM(f.gross_revenue)/10000000,2) AS revenue_crore,
           ROUND(SUM(f.gross_profit)/10000000,2) AS profit_crore,
           ROUND(AVG(f.profit_margin_pct),2) AS avg_margin,
           COUNT(DISTINCT f.customer_key) AS customers
    FROM fact_sales f JOIN dim_date d ON f.date_key=d.date_key
    WHERE f.return_flag=0 GROUP BY d.year ORDER BY d.year
""")

category_perf = q("""
    SELECT p.category,
           ROUND(SUM(f.gross_revenue)/10000000,2) AS revenue_crore,
           ROUND(AVG(f.profit_margin_pct),2) AS avg_margin,
           ROUND(SUM(f.return_flag)*100.0/COUNT(*),2) AS return_rate
    FROM fact_sales f JOIN dim_product p ON f.product_key=p.product_key
    GROUP BY p.category ORDER BY revenue_crore DESC
""")

monthly_trend = q("""
    SELECT d.year_month, d.year, d.month_num,
           ROUND(SUM(f.gross_revenue)/10000000,3) AS revenue_crore
    FROM fact_sales f JOIN dim_date d ON f.date_key=d.date_key
    WHERE f.return_flag=0 GROUP BY d.year_month, d.year, d.month_num
    ORDER BY d.year, d.month_num
""")

region_perf = q("""
    SELECT s.region,
           ROUND(SUM(f.gross_revenue)/10000000,2) AS revenue_crore,
           ROUND(AVG(f.profit_margin_pct),2) AS avg_margin,
           COUNT(DISTINCT f.store_key) AS stores
    FROM fact_sales f JOIN dim_store s ON f.store_key=s.store_key
    WHERE f.return_flag=0 GROUP BY s.region ORDER BY revenue_crore DESC
""")

promo_perf = q("""
    SELECT p.promotion_name, p.discount_pct,
           ROUND(SUM(f.gross_revenue)/10000000,2) AS revenue_crore,
           ROUND(AVG(f.profit_margin_pct),2) AS avg_margin,
           COUNT(*) AS txns
    FROM fact_sales f JOIN dim_promotion p ON f.promotion_key=p.promotion_key
    GROUP BY p.promotion_name, p.discount_pct ORDER BY revenue_crore DESC
""")

loyalty_perf = q("""
    SELECT c.loyalty_tier,
           COUNT(DISTINCT f.customer_key) AS customers,
           ROUND(SUM(f.gross_revenue)/10000000,2) AS revenue_crore,
           ROUND(AVG(f.gross_revenue),0) AS avg_basket
    FROM fact_sales f JOIN dim_customer c ON f.customer_key=c.customer_key
    WHERE f.return_flag=0 GROUP BY c.loyalty_tier ORDER BY revenue_crore DESC
""")

festival = q("""
    SELECT CASE WHEN d.is_festival_month=1 THEN 'Festival' ELSE 'Regular' END AS period,
           ROUND(AVG(f.gross_revenue),0) AS avg_basket,
           ROUND(SUM(f.gross_revenue)/10000000,2) AS revenue_crore,
           ROUND(AVG(f.discount_pct),2) AS avg_discount
    FROM fact_sales f JOIN dim_date d ON f.date_key=d.date_key
    WHERE f.return_flag=0 GROUP BY d.is_festival_month
""")

price_band = q("""
    SELECT p.price_band,
           ROUND(SUM(f.gross_revenue)/10000000,2) AS revenue_crore,
           ROUND(AVG(f.profit_margin_pct),2) AS avg_margin,
           COUNT(*) AS txns
    FROM fact_sales f JOIN dim_product p ON f.product_key=p.product_key
    WHERE f.return_flag=0 GROUP BY p.price_band ORDER BY revenue_crore DESC
""")

print("All queries done.")

# ── DASHBOARD ──────────────────────────────────────────────
fig = plt.figure(figsize=(22, 26), facecolor='#FFFFFF')
gs  = gridspec.GridSpec(4, 3, figure=fig, hspace=0.48, wspace=0.38)

# KPI Banner
ax0 = fig.add_subplot(gs[0,:])
ax0.set_facecolor(DARK); ax0.set_xlim(0,10); ax0.set_ylim(0,1); ax0.axis('off')
ax0.text(5, 0.85, 'RetailMart Data Warehouse — Star Schema Analytics 2020-2024',
         ha='center', fontsize=15, fontweight='bold', color='white')
kpi_items = [
    (f"Rs {kpi['gmv_crore'].iloc[0]}Cr", 'Total GMV'),
    (f"Rs {kpi['profit_crore'].iloc[0]}Cr", 'Total Profit'),
    (f"{kpi['avg_margin'].iloc[0]}%", 'Avg Margin'),
    (f"{kpi['customers'].iloc[0]:,}", 'Customers'),
    (f"{kpi['txns'].iloc[0]:,}", 'Transactions'),
    (f"Rs {kpi['avg_basket'].iloc[0]:,}", 'Avg Basket'),
    (f"{kpi['return_rate'].iloc[0]}%", 'Return Rate'),
]
for i,(v,l) in enumerate(kpi_items):
    x = 0.7 + i*1.23
    ax0.text(x, 0.50, v, ha='center', fontsize=11, fontweight='bold', color=YELLOW)
    ax0.text(x, 0.22, l, ha='center', fontsize=8, color='#BDC3C7')

# Yearly trend
ax1 = fig.add_subplot(gs[1,0])
ax1.set_facecolor(LIGHT)
bar_colors = [RED,YELLOW,GREEN,RED,YELLOW]
bars = ax1.bar(yearly['year'].astype(str), yearly['revenue_crore'],
               color=bar_colors, edgecolor='white')
ax1_t = ax1.twinx()
ax1_t.plot(yearly['year'].astype(str), yearly['avg_margin'],
           color=DARK, marker='o', linewidth=2, markersize=5)
ax1.set_title('Yearly Revenue and Margin', fontweight='bold', color=DARK, fontsize=10)
ax1.set_ylabel('Revenue (Rs Crore)', fontsize=8)
ax1_t.set_ylabel('Avg Margin %', fontsize=8)
for bar in bars:
    ax1.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.2,
             f'{bar.get_height():.1f}', ha='center', fontsize=7, color=DARK)

# Category performance
ax2 = fig.add_subplot(gs[1,1])
ax2.set_facecolor(LIGHT)
cat_colors = [GREEN if m>=30 else YELLOW if m>=20 else RED
              for m in category_perf['avg_margin']]
ax2.barh(category_perf['category'], category_perf['revenue_crore'],
         color=cat_colors, edgecolor='white')
ax2.set_title('Category Revenue (Rs Crore)', fontweight='bold', color=DARK, fontsize=10)
ax2.set_xlabel('Rs Crore', fontsize=8)
for i,(v,r) in enumerate(zip(category_perf['revenue_crore'], category_perf['avg_margin'])):
    ax2.text(v+0.1, i, f'{r}%', va='center', fontsize=6.5, color=DARK)

# Monthly trend
ax3 = fig.add_subplot(gs[1,2])
ax3.set_facecolor(LIGHT)
monthly_trend['color'] = monthly_trend['revenue_crore'].apply(
    lambda x: GREEN if x >= monthly_trend['revenue_crore'].quantile(0.75)
              else YELLOW if x >= monthly_trend['revenue_crore'].median()
              else RED)
ax3.plot(range(len(monthly_trend)), monthly_trend['revenue_crore'],
         color=BLUE, linewidth=1.5)
ax3.fill_between(range(len(monthly_trend)), monthly_trend['revenue_crore'],
                 alpha=0.15, color=BLUE)
ax3.set_title('Monthly Revenue Trend', fontweight='bold', color=DARK, fontsize=10)
ax3.set_ylabel('Rs Crore', fontsize=8)
ax3.set_xticks(range(0,len(monthly_trend),6))
ax3.set_xticklabels([monthly_trend['year_month'].iloc[i]
                     for i in range(0,len(monthly_trend),6)],
                    rotation=45, fontsize=6.5)

# Region performance
ax4 = fig.add_subplot(gs[2,0])
ax4.set_facecolor(LIGHT)
reg_colors = [GREEN,YELLOW,RED,BLUE][:len(region_perf)]
ax4.bar(region_perf['region'], region_perf['revenue_crore'],
        color=reg_colors, edgecolor='white')
ax4.set_title('Region Revenue (Rs Crore)', fontweight='bold', color=DARK, fontsize=10)
ax4.set_ylabel('Rs Crore', fontsize=8)
for i,(r,v) in enumerate(zip(region_perf['region'], region_perf['revenue_crore'])):
    ax4.text(i, v+0.2, f'Rs {v}Cr', ha='center', fontsize=7.5, color=DARK)

# Promotion effectiveness
ax5 = fig.add_subplot(gs[2,1])
ax5.set_facecolor(LIGHT)
promo_colors = [RED if d>=40 else YELLOW if d>=20 else GREEN
                for d in promo_perf['discount_pct']]
ax5.barh(promo_perf['promotion_name'], promo_perf['revenue_crore'],
         color=promo_colors, edgecolor='white')
ax5.set_title('Promotion Revenue vs Discount', fontweight='bold', color=DARK, fontsize=10)
ax5.set_xlabel('Rs Crore', fontsize=8)
for i,(v,d) in enumerate(zip(promo_perf['revenue_crore'], promo_perf['discount_pct'])):
    ax5.text(v+0.1, i, f'{d}% disc', va='center', fontsize=6.5, color=DARK)

# Loyalty tier
ax6 = fig.add_subplot(gs[2,2])
ax6.set_facecolor(LIGHT)
loyalty_colors = [GREEN,'#F39C12','#E67E22','#C0392B'][:len(loyalty_perf)]
wedges,texts,pcts = ax6.pie(loyalty_perf['revenue_crore'],
                             labels=loyalty_perf['loyalty_tier'],
                             autopct='%1.1f%%', colors=loyalty_colors,
                             pctdistance=0.75, textprops={'fontsize':8})
ax6.set_title('Revenue by Loyalty Tier', fontweight='bold', color=DARK, fontsize=10)

# Price band
ax7 = fig.add_subplot(gs[3,0])
ax7.set_facecolor(LIGHT)
pb_colors = [GREEN,YELLOW,RED,BLUE][:len(price_band)]
ax7.bar(price_band['price_band'], price_band['revenue_crore'],
        color=pb_colors, edgecolor='white')
ax7.set_title('Revenue by Price Band', fontweight='bold', color=DARK, fontsize=10)
ax7.set_ylabel('Rs Crore', fontsize=8)

# Festival uplift
ax8 = fig.add_subplot(gs[3,1])
ax8.set_facecolor(LIGHT)
fest_colors = [RED if p=='Regular' else GREEN for p in festival['period']]
bars8 = ax8.bar(festival['period'], festival['avg_basket'],
                color=fest_colors, edgecolor='white', width=0.5)
ax8.set_title('Festival vs Regular Avg Basket (Rs)', fontweight='bold', color=DARK, fontsize=10)
ax8.set_ylabel('Avg Basket Size (Rs)', fontsize=8)
for bar in bars8:
    ax8.text(bar.get_x()+bar.get_width()/2, bar.get_height()+10,
             f'Rs {int(bar.get_height()):,}', ha='center', fontsize=9, color=DARK)

# DWH architecture note
ax9 = fig.add_subplot(gs[3,2])
ax9.set_facecolor(LIGHT)
ax9.axis('off')
arch_text = (
    f"Star Schema Architecture\n"
    f"{'─'*32}\n\n"
    f"Fact Table\n"
    f"fact_sales: 80,000 rows\n"
    f"Grain: 1 row per line item\n\n"
    f"Dimension Tables\n"
    f"dim_date      : 1,827 rows\n"
    f"dim_customer  : 5,000 rows\n"
    f"dim_product   : 1,000 rows\n"
    f"dim_store     :   100 rows\n"
    f"dim_promotion :     8 rows\n\n"
    f"ETL Layers\n"
    f"Staging -> Dimensions -> Facts\n"
    f"SCD Type 2 on dim_customer\n"
    f"ETL audit log included\n\n"
    f"BI Views Created\n"
    f"v_daily_sales\n"
    f"v_category_performance\n"
    f"v_store_performance"
)
ax9.text(0.05, 0.95, arch_text, transform=ax9.transAxes,
         va='top', ha='left', fontsize=8.5, color=DARK, linespacing=1.5,
         bbox=dict(boxstyle='round,pad=0.6', facecolor='#EBF5FB',
                   edgecolor=GREEN, linewidth=1.5))
ax9.set_title('DWH Architecture Summary', fontweight='bold', color=DARK, fontsize=10)

plt.suptitle('RetailMart Data Warehouse — Complete BI Analytics Dashboard',
             fontsize=16, fontweight='bold', y=0.995, color=DARK)
plt.savefig(f'{OUT}/dwh_dashboard.png', dpi=150, bbox_inches='tight', facecolor='#FFFFFF')
plt.close()
print("Dashboard saved.")

# ── EXCEL REPORT ──────────────────────────────────────────
excel_path = f'{OUT}/RetailMart_DWH_Report.xlsx'
writer = pd.ExcelWriter(excel_path, engine='xlsxwriter')
wb = writer.book

hdr = wb.add_format({'bold':True,'font_color':'#FFFFFF','bg_color':DARK,
                     'border':1,'align':'center','font_name':'Arial','font_size':9})
alt1= wb.add_format({'bg_color':'#EBF5FB','border':1,'font_name':'Arial','font_size':9})
alt2= wb.add_format({'bg_color':'#FFFFFF','border':1,'font_name':'Arial','font_size':9})
ttl = wb.add_format({'bold':True,'font_size':13,'font_color':'#FFFFFF',
                     'bg_color':DARK,'align':'center','font_name':'Arial'})
kpi_fmt = wb.add_format({'bold':True,'font_size':14,'font_color':RED,
                          'align':'center','border':2,'bg_color':'#FDEDEC','font_name':'Arial'})
kpi_lbl = wb.add_format({'font_size':8,'font_color':'#7F8C8D',
                          'align':'center','bg_color':LIGHT,'font_name':'Arial'})

def write_sheet(ws, df, row_start=1):
    for c, col in enumerate(df.columns):
        ws.write(row_start, c, col, hdr)
    for r, row in enumerate(df.itertuples(index=False), row_start+1):
        fmt = alt1 if r%2==0 else alt2
        for c, val in enumerate(row):
            ws.write(r, c, val, fmt)
    for c in range(len(df.columns)):
        ws.set_column(c, c, 18)

ws1 = wb.add_worksheet('Executive Summary')
ws1.set_tab_color(RED)
ws1.merge_range('A1:G2','RetailMart DWH — Executive BI Dashboard 2020-2024',ttl)
ws1.set_row(0,22); ws1.set_row(1,22)
kpi_list = [
    (f"Rs {kpi['gmv_crore'].iloc[0]}Cr",'Total GMV'),
    (f"Rs {kpi['profit_crore'].iloc[0]}Cr",'Total Profit'),
    (f"{kpi['avg_margin'].iloc[0]}%",'Avg Margin'),
    (f"{kpi['customers'].iloc[0]:,}",'Customers'),
    (f"{kpi['txns'].iloc[0]:,}",'Transactions'),
    (f"Rs {kpi['avg_basket'].iloc[0]:,}",'Avg Basket'),
    (f"{kpi['return_rate'].iloc[0]}%",'Return Rate'),
]
for i,(v,l) in enumerate(kpi_list):
    ws1.merge_range(3,i,3,i,v,kpi_fmt)
    ws1.merge_range(4,i,4,i,l,kpi_lbl)
    ws1.set_row(3,32); ws1.set_row(4,18)
ws1.merge_range('A7:G7','Yearly Performance',ttl)
write_sheet(ws1, yearly, 7)
ws1.insert_image('A18', f'{OUT}/dwh_dashboard.png',{'x_scale':0.55,'y_scale':0.55})

ws2 = wb.add_worksheet('Category Analytics')
ws2.set_tab_color(YELLOW)
ws2.merge_range('A1:D1','Category Performance',ttl)
write_sheet(ws2, category_perf, 1)

ws3 = wb.add_worksheet('Region and Store')
ws3.set_tab_color(GREEN)
ws3.merge_range('A1:D1','Regional Performance',ttl)
write_sheet(ws3, region_perf, 1)
top_stores = q("""
    SELECT s.store_name, s.city, s.state, s.store_format, s.region,
           ROUND(SUM(f.gross_revenue)/10000000,2) AS revenue_crore,
           ROUND(AVG(f.profit_margin_pct),2) AS avg_margin
    FROM fact_sales f JOIN dim_store s ON f.store_key=s.store_key
    WHERE f.return_flag=0 GROUP BY s.store_name,s.city,s.state,s.store_format,s.region
    ORDER BY revenue_crore DESC LIMIT 20
""")
ws3.merge_range('A8:G8','Top 20 Stores',ttl)
write_sheet(ws3, top_stores, 8)

ws4 = wb.add_worksheet('Promotion Analytics')
ws4.set_tab_color(BLUE)
ws4.merge_range('A1:F1','Promotion Performance',ttl)
write_sheet(ws4, promo_perf, 1)

ws5 = wb.add_worksheet('DWH Schema Info')
ws5.set_tab_color('#8E44AD')
schema_info = pd.DataFrame([
    ('fact_sales','Facts','80,000','Central fact table - Kimball star schema'),
    ('dim_date','Dimension','1,827','Date dimension with fiscal, season, festival flags'),
    ('dim_customer','Dimension','5,000','SCD Type 2 - tracks loyalty tier changes'),
    ('dim_product','Dimension','1,000','Product hierarchy with price band'),
    ('dim_store','Dimension','100','Store with region, format, tier'),
    ('dim_promotion','Dimension','8','Promotion type and discount'),
], columns=['Table','Layer','Rows','Description'])
ws5.merge_range('A1:D1','Data Warehouse Schema Reference',ttl)
write_sheet(ws5, schema_info, 1)

writer.close()
print(f"Excel saved: {excel_path}")
con.close()
print("All outputs complete.")
