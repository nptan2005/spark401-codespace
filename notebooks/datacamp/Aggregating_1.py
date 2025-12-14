import pandas as pd
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, max, min
from pyspark.sql.types import (
                               DoubleType,
                               IntegerType,
                               StringType,
                               StructField,
                               StructType,
)

# --- Khởi tạo Spark Session ---
spark = SparkSession.builder \
    .appName("SalaryAggregation") \
    .getOrCreate()

print("--- BẮT ĐẦU: Phân tích Tổng hợp Lương theo Địa điểm và Quy mô ---")

# --- 1. Tạo DataFrame mẫu (salaries_df) với cột company_size ---
# S: Small, M: Medium, L: Large
data = [
    ("Data Scientist", 120000, "CA", "M"), 
    ("Data Engineer", 140000, "US", "S"), 
    ("ML Engineer", 130000, "CA", "L"), 
    ("Analyst", 80000, "US", "S"),
    ("Data Engineer", 150000, "US", "L"),
    ("Senior Data Scientist", 160000, "CA", "L"),
    ("Data Analyst", 90000, "US", "S"),
    ("Research Scientist", 220000, "US", "L") 
]
schema = StructType([
    StructField("job_title", StringType(), True),
    StructField("salary_in_usd", IntegerType(), True),
    StructField("company_location", StringType(), True),
    StructField("company_size", StringType(), True) # Cột mới
])

# DataFrame được tạo: salaries_df
salaries_df = spark.createDataFrame(data, schema)
print("-> DataFrame Gốc (salaries_df):")
salaries_df.show()

# --- 2. TÌM LƯƠNG TỐI THIỂU (MIN) TẠI CÔNG TY MỸ NHỎ ("US", "S") ---
print("\n--- KẾT QUẢ 1: Lương Tối thiểu tại US, Small Company ---")
# Find the minimum salary at a US, Small company
min_salary_us_small = salaries_df \
    .filter((col("company_location") == "US") & (col("company_size") == "S")) \
    .agg(min("salary_in_usd"))

min_salary_us_small.show()

# --- 3. TÌM LƯƠNG TỐI ĐA (MAX) TẠI CÔNG TY MỸ LỚN ("US", "L") ---
print("\n--- KẾT QUẢ 2: Lương Tối đa tại US, Large Company ---")
# Find the maximum salary at a US, Large company
max_salary_us_large = salaries_df \
    .filter((col("company_location") == "US") & (col("company_size") == "L")) \
    .agg(max("salary_in_usd"))

max_salary_us_large.show()

spark.stop()