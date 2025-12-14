import pandas as pd
from pyspark.sql import SparkSession
from pyspark.sql.functions import col
from pyspark.sql.types import (
                               DoubleType,
                               IntegerType,
                               StringType,
                               StructField,
                               StructType,
)

# --- Khởi tạo Spark Session ---
spark = SparkSession.builder \
    .appName("QuerySQLSalaries") \
    .getOrCreate()

print("--- BẮT ĐẦU: Truy vấn SQL trên DataFrame - Lương theo Địa điểm ---")

# --- 1. Tạo DataFrame mẫu (mô phỏng salaries_df đã có sẵn) ---
data = [
    ("Data Scientist", 120000, "CA"), 
    ("Data Engineer", 140000, "US"), 
    ("ML Engineer", 130000, "CA"), 
    ("Analyst", 80000, "CA"),
    ("Data Engineer", 150000, "US"),
    ("Senior Data Scientist", 160000, "CA")
]
schema = StructType([
    StructField("job_title", StringType(), True),
    StructField("salary_in_usd", IntegerType(), True),
    StructField("company_location", StringType(), True)
])

# DataFrame được tạo: salaries_df
salaries_df = spark.createDataFrame(data, schema)
print("-> DataFrame Gốc (salaries_df):")
salaries_df.show()

# --- 2. Tạo một Temporary Table "salaries_table" ---
# Create a temporary view of salaries_table
salaries_df.createOrReplaceTempView('salaries_table')
print("\n-> DataFrame đã được đăng ký thành Temporary Table: 'salaries_table'")

# --- 3. Construct và Apply SQL Query ---
print("\n--- KẾT QUẢ: Công việc tại Canada (CA) ---")

# Construct the "query"
query = '''SELECT job_title, salary_in_usd FROM salaries_table WHERE company_location == "CA"'''

# Apply the SQL "query"
canada_titles = spark.sql(query)

# --- 4. Get a summary of the table ---
print("\n--- TÓM TẮT THỐNG KÊ (Summary Statistics) ---")
# Generate basic statistics
canada_titles.describe().show()

# Show final DataFrame for clarity
print("\n-> DataFrame đã lọc (canada_titles):")
canada_titles.show()


spark.stop()