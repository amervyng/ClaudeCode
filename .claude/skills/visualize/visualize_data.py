import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from datetime import datetime
import numpy as np

# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (14, 10)

# Define paths
data_dir = Path("C:/ClaudeCode/.claude/skills/migrate/data/2026-09-17_21-40-06")
viz_dir = Path("C:/ClaudeCode/.claude/skills/visualize/visualizations")
viz_dir.mkdir(parents=True, exist_ok=True)

# Create timestamp for file naming
timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

# Read Parquet files
print("Reading Parquet files...")
dim_customer = pd.read_parquet(data_dir / "dim_customer.parquet")
dim_date = pd.read_parquet(data_dir / "dim_date.parquet")
dim_product = pd.read_parquet(data_dir / "dim_product.parquet")
dim_store = pd.read_parquet(data_dir / "dim_store.parquet")
fact_sales = pd.read_parquet(data_dir / "fact_sales.parquet")
fact_returns = pd.read_parquet(data_dir / "fact_returns.parquet")

print("\nData shapes:")
print(f"dim_customer: {dim_customer.shape}")
print(f"dim_date: {dim_date.shape}")
print(f"dim_product: {dim_product.shape}")
print(f"dim_store: {dim_store.shape}")
print(f"fact_sales: {fact_sales.shape}")
print(f"fact_returns: {fact_returns.shape}")

# Build KPIs
print("\n=== Building KPIs ===")

# Merge sales with dimensions
sales_merged = fact_sales.merge(dim_date, on='date_sk', how='left')
sales_merged = sales_merged.merge(dim_customer, on='customer_sk', how='left')
sales_merged = sales_merged.merge(dim_product, on='product_sk', how='left')
sales_merged = sales_merged.merge(dim_store, on='store_sk', how='left')

# Calculate KPIs
total_revenue = fact_sales['net_amount'].sum()
total_orders = fact_sales['sales_id'].nunique()
total_customers = fact_sales['customer_sk'].nunique()
average_order_value = total_revenue / total_orders if total_orders > 0 else 0
total_quantity_sold = fact_sales['quantity'].sum()
total_returns = fact_returns.shape[0]
return_rate = (total_returns / total_orders * 100) if total_orders > 0 else 0

print(f"Total Revenue: ${total_revenue:,.2f}")
print(f"Total Orders: {total_orders:,}")
print(f"Total Customers: {total_customers:,}")
print(f"Average Order Value: ${average_order_value:,.2f}")
print(f"Total Quantity Sold: {total_quantity_sold:,}")
print(f"Total Returns: {total_returns:,}")
print(f"Return Rate: {return_rate:.2f}%")

# Create comprehensive visualizations
fig = plt.figure(figsize=(16, 12))

# 1. KPI Summary (top section)
ax1 = plt.subplot(3, 3, 1)
ax1.axis('off')
kpi_text = f"""
KEY PERFORMANCE INDICATORS

Total Revenue: ${total_revenue:,.0f}
Total Orders: {total_orders:,}
Total Customers: {total_customers:,}
Avg Order Value: ${average_order_value:,.2f}
Quantity Sold: {total_quantity_sold:,}
Return Rate: {return_rate:.2f}%
"""
ax1.text(0.1, 0.5, kpi_text, fontsize=11, verticalalignment='center',
         family='monospace', bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.5))

# 2. Revenue by Store
ax2 = plt.subplot(3, 3, 2)
revenue_by_store = sales_merged.groupby('store_name')['net_amount'].sum().sort_values(ascending=False)
revenue_by_store.plot(kind='barh', ax=ax2, color='steelblue')
ax2.set_title('Revenue by Store', fontweight='bold', fontsize=12)
ax2.set_xlabel('Revenue ($)')

# 3. Revenue by Product Category
ax3 = plt.subplot(3, 3, 3)
revenue_by_category = sales_merged.groupby('category')['net_amount'].sum().sort_values(ascending=False)
revenue_by_category.plot(kind='bar', ax=ax3, color='coral')
ax3.set_title('Revenue by Product Category', fontweight='bold', fontsize=12)
ax3.set_ylabel('Revenue ($)')
ax3.tick_params(axis='x', rotation=45)

# 4. Orders Over Time
ax4 = plt.subplot(3, 3, 4)
orders_by_date = sales_merged.groupby('date')['sales_id'].nunique()
orders_by_date.plot(ax=ax4, color='green', linewidth=2)
ax4.set_title('Orders Over Time', fontweight='bold', fontsize=12)
ax4.set_xlabel('Date')
ax4.set_ylabel('Number of Orders')
plt.setp(ax4.xaxis.get_majorticklabels(), rotation=45)

# 5. Sales Amount Distribution
ax5 = plt.subplot(3, 3, 5)
ax5.hist(fact_sales['net_amount'], bins=30, color='purple', edgecolor='black', alpha=0.7)
ax5.set_title('Sales Amount Distribution', fontweight='bold', fontsize=12)
ax5.set_xlabel('Sales Amount ($)')
ax5.set_ylabel('Frequency')

# 6. Top 5 Products by Revenue
ax6 = plt.subplot(3, 3, 6)
top_products = sales_merged.groupby('product_name')['net_amount'].sum().sort_values(ascending=False).head(5)
top_products.plot(kind='barh', ax=ax6, color='orange')
ax6.set_title('Top 5 Products by Revenue', fontweight='bold', fontsize=12)
ax6.set_xlabel('Revenue ($)')

# 7. Quantity Sold by Category
ax7 = plt.subplot(3, 3, 7)
qty_by_category = sales_merged.groupby('category')['quantity'].sum().sort_values(ascending=False)
qty_by_category.plot(kind='bar', ax=ax7, color='teal')
ax7.set_title('Quantity Sold by Category', fontweight='bold', fontsize=12)
ax7.set_ylabel('Quantity')
ax7.tick_params(axis='x', rotation=45)

# 8. Customer Count by Store
ax8 = plt.subplot(3, 3, 8)
customers_by_store = sales_merged.groupby('store_name')['customer_sk'].nunique().sort_values(ascending=False)
customers_by_store.plot(kind='bar', ax=ax8, color='pink')
ax8.set_title('Unique Customers by Store', fontweight='bold', fontsize=12)
ax8.set_ylabel('Number of Customers')
ax8.tick_params(axis='x', rotation=45)

# 9. Returns by Product Category
ax9 = plt.subplot(3, 3, 9)
if 'product_sk' in fact_returns.columns:
    returns_merged = fact_returns.merge(dim_product, on='product_sk', how='left')
    returns_by_category = returns_merged.groupby('category').size().sort_values(ascending=False)
    returns_by_category.plot(kind='bar', ax=ax9, color='red', alpha=0.7)
ax9.set_title('Returns by Product Category', fontweight='bold', fontsize=12)
ax9.set_ylabel('Number of Returns')
ax9.tick_params(axis='x', rotation=45)

plt.tight_layout()
viz_path = viz_dir / f"{timestamp}.png"
plt.savefig(viz_path, dpi=300, bbox_inches='tight')
print(f"\n✓ Comprehensive visualization saved: {viz_path}")

# Create a second figure for additional insights
fig2, axes = plt.subplots(2, 2, figsize=(14, 10))

# Revenue trend by month
ax = axes[0, 0]
if 'month' in sales_merged.columns:
    revenue_by_month = sales_merged.groupby('month')['net_amount'].sum()
    revenue_by_month.plot(kind='line', ax=ax, marker='o', color='darkblue', linewidth=2)
    ax.set_title('Revenue Trend by Month', fontweight='bold', fontsize=12)
    ax.set_xlabel('Month')
    ax.set_ylabel('Revenue ($)')
    ax.grid(True, alpha=0.3)

# Average Order Value by Store
ax = axes[0, 1]
aov_by_store = (sales_merged.groupby('store_name')['net_amount'].sum() /
                sales_merged.groupby('store_name')['sales_id'].nunique()).sort_values(ascending=False)
aov_by_store.plot(kind='barh', ax=ax, color='darkgreen')
ax.set_title('Average Order Value by Store', fontweight='bold', fontsize=12)
ax.set_xlabel('AOV ($)')

# Quantity Distribution by Category (Box Plot)
ax = axes[1, 0]
categories = [cat for cat in sales_merged['category'].unique() if pd.notna(cat)]
category_data = [sales_merged[sales_merged['category'] == cat]['quantity'].values for cat in categories]
bp = ax.boxplot(category_data)
ax.set_xticklabels(categories)
ax.set_title('Quantity Distribution by Category', fontweight='bold', fontsize=12)
ax.set_ylabel('Quantity')
ax.tick_params(axis='x', rotation=45)

# Customer Purchase Frequency Distribution
ax = axes[1, 1]
customer_orders = sales_merged.groupby('customer_sk')['sales_id'].nunique()
ax.hist(customer_orders, bins=30, color='darkred', edgecolor='black', alpha=0.7)
ax.set_title('Customer Purchase Frequency Distribution', fontweight='bold', fontsize=12)
ax.set_xlabel('Number of Orders per Customer')
ax.set_ylabel('Frequency')

plt.tight_layout()
viz_path2 = viz_dir / f"{timestamp}_insights.png"
plt.savefig(viz_path2, dpi=300, bbox_inches='tight')
print(f"✓ Insights visualization saved: {viz_path2}")

print("\n=== Visualization Complete ===")
print(f"Visualizations saved to: {viz_dir}")
