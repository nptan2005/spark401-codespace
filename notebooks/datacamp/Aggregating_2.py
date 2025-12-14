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
    .appName("RDDAggregation") \
    .getOrCreate()

print("--- BẮT ĐẦU: Tổng hợp Dữ liệu bằng RDD ---")

# --- 1. Tạo DataFrame Mẫu ---
# DataFrame Creation
data = [("HR", "3000"), ("IT", "4000"), ("Finance", "3500"), ("HR", "5000"), ("IT", "6000")]
columns = ["Department", "Salary"]
df = spark.createDataFrame(data, schema=columns)

print("-> DataFrame Gốc (df):")
df.show()

# --- 2. Map DataFrame sang RDD dạng Key-Value ---
# rdd.map(lambda row: (Key, Value))
# Ở đây, chúng ta chuyển đổi Salary từ chuỗi sang số nguyên để có thể tính tổng.
rdd = df.rdd.map(lambda row: (row["Department"], int(row["Salary"])))
print("-> RDD đã Map thành công.")

# --- 3. Áp dụng reduceByKey để tính tổng ---
# reduceByKey(lambda x, y: x + y) thực hiện tính tổng (x + y) cho tất cả các giá trị có cùng Key.
# Apply a lambda function to get the sum of the DataFrame
rdd_aggregated = rdd.reduceByKey(lambda x, y: x + y)

# --- 4. Thu thập và Hiển thị Kết quả ---
print("\n--- KẾT QUẢ: Tổng Lương theo Phòng Ban (RDD) ---")
# Show the collected Results
print(rdd_aggregated.collect())

spark.stop()