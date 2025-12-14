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
    .appName("QuerySQLOnDataFrame") \
    .getOrCreate()

print("--- BẮT ĐẦU: Truy vấn SQL trên DataFrame ---")

# --- 1. Tạo DataFrame mẫu (mô phỏng df đã có sẵn) ---
data = [
    ("Alice", "Data Scientist", 120000), 
    ("Bob", "Data Engineer", 140000), 
    ("Charlie", "Data Scientist", 130000), 
    ("David", "Analyst", 80000),
    ("Eve", "Data Engineer", 150000),
    ("Frank", "Analyst", 95000),
    ("Grace", "Data Scientist", 125000),
    ("Heidi", "Data Engineer", 145000),
    ("Ivan", "Analyst", 88000),
    ("Judy", "Data Scientist", 135000),
    ("Kevin", "Data Engineer", 155000)
]
schema = StructType([
    StructField("name", StringType(), True),
    StructField("Position", StringType(), True),
    StructField("Salary", IntegerType(), True)
])

df = spark.createDataFrame(data, schema)
print("-> DataFrame Gốc (df):")
df.show()
df.printSchema()

# --- 2. Tạo một Temporary Table "people" ---
# Create a temporary table "people"
df.createOrReplaceTempView("people")
print("\n-> DataFrame đã được đăng ký thành Temporary Table: 'people'")

# --- 3. Chọn cột tên từ bảng tạm ---
print("\n--- KẾT QUẢ: Danh sách 10 Tên (SQL Query) ---")

# Select the names from the temporary table people
query = """SELECT name FROM people"""

# Assign the result of Spark's query to people_df_names
people_df_names = spark.sql(query)

# Print the top 10 names of the people
people_df_names.show(10, truncate=False)

spark.stop()