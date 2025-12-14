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
    .appName("QueryTempViewExample") \
    .getOrCreate()

print("--- BẮT ĐẦU: Truy vấn SQL trên Temporary View ---")

# --- 1. Tạo DataFrame mẫu (mô phỏng df đã có sẵn) ---
data = [
    ("Data Scientist", 120000), 
    ("Data Engineer", 140000), 
    ("Data Scientist", 130000), 
    ("Analyst", 80000),
    ("Data Engineer", 150000),
    ("Analyst", 95000)
]
schema = StructType([
    StructField("Position", StringType(), True),
    StructField("Salary", IntegerType(), True)
])

df = spark.createDataFrame(data, schema)
print("-> DataFrame Gốc (df):")
df.show()
df.printSchema()

# --- 2. Đăng ký DataFrame thành Temporary View ---
# df.createOrReplaceTempView("data_view")
df.createOrReplaceTempView("data_view")
print("\n-> DataFrame đã được đăng ký thành View: 'data_view'")

# --- 3. Chạy truy vấn SQL trên View ---
print("\n--- KẾT QUẢ: Tổng Lương theo Vị trí (SQL Query) ---")

# Advanced SQL query: Calculate total salary by Position
result = spark.sql("""
    SELECT Position, SUM(Salary) AS Total_Salary
    FROM data_view
    GROUP BY Position
    ORDER BY Total_Salary DESC
    """
)
result.show()

spark.stop()