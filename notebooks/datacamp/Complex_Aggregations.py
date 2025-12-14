import pandas as pd
from pyspark.sql import SparkSession
from pyspark.sql.functions import avg, col, sum
from pyspark.sql.types import (
                               DoubleType,
                               IntegerType,
                               StringType,
                               StructField,
                               StructType,
)

# --- Khởi tạo Spark Session ---
spark = SparkSession.builder \
    .appName("ComplexAggregation") \
    .getOrCreate()

print("--- BẮT ĐẦU: Phân tích Tổng hợp Phức tạp (Lương US, Large Companies) ---")

# --- 1. Tạo DataFrame Mẫu (salaries_df) ---
# S: Small, M: Medium, L: Large
data = [
    ("Data Scientist", 120000, "CA", "M"), 
    ("Data Engineer", 180000, "US", "L"), 
    ("ML Engineer", 130000, "CA", "L"), 
    ("Analyst", 80000, "US", "S"),
    ("Data Engineer", 210000, "US", "L"), # Bản ghi US, L thứ 2
    ("Senior Data Scientist", 160000, "CA", "L"),
    ("Data Architect", 250000, "US", "L"), # Bản ghi US, L thứ 3
    ("Data Analyst", 90000, "US", "S")
]
schema = StructType([
    StructField("job_title", StringType(), True),
    StructField("salary_in_usd", IntegerType(), True),
    StructField("company_location", StringType(), True),
    StructField("company_size", StringType(), True)
])

salaries_df = spark.createDataFrame(data, schema)
print("-> DataFrame Gốc (salaries_df):")
salaries_df.show()


# --- 2. LỌC: Large US Companies ---
# set a large companies variable for other analytics
large_us_companies = salaries_df \
    .filter(col("company_size") == "L") \
    .filter(col("company_location") == "US")

print("\n-> Dữ liệu đã lọc (Large US Companies):")
large_us_companies.show()


# --- 3. TÍNH TOÁN TỔNG HỢP PHỨC HỢP (Average và Sum) ---
print("\n--- KẾT QUẢ: Mức Lương Trung Bình và Tổng Lương ---")

# Áp dụng agg() để tính nhiều phép tổng hợp cùng lúc
large_us_companies \
    .agg(
        avg("salary_in_usd").alias("Average_Salary_US_L"),
        sum("salary_in_usd").alias("Total_Salary_US_L")
    ) \
    .show()


spark.stop()