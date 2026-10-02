import pandas as pd
from pathlib import Path

# Define paths
data_dir = Path("C:/ClaudeCode/.claude/skills/migrate/data/2026-09-17_21-40-06")

# Read Parquet files
dim_customer = pd.read_parquet(data_dir / "dim_customer.parquet")
dim_date = pd.read_parquet(data_dir / "dim_date.parquet")
dim_product = pd.read_parquet(data_dir / "dim_product.parquet")
dim_store = pd.read_parquet(data_dir / "dim_store.parquet")
fact_sales = pd.read_parquet(data_dir / "fact_sales.parquet")
fact_returns = pd.read_parquet(data_dir / "fact_returns.parquet")

print("=== dim_customer columns ===")
print(dim_customer.columns.tolist())
print("\n=== dim_date columns ===")
print(dim_date.columns.tolist())
print("\n=== dim_product columns ===")
print(dim_product.columns.tolist())
print("\n=== dim_store columns ===")
print(dim_store.columns.tolist())
print("\n=== fact_sales columns ===")
print(fact_sales.columns.tolist())
print("\n=== fact_returns columns ===")
print(fact_returns.columns.tolist())

print("\n=== Sample data ===")
print("\nfact_sales head:")
print(fact_sales.head())
print("\ndim_date head:")
print(dim_date.head())
