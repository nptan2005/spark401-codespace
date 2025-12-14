import pandas as pd
from pyspark.sql import SparkSession
from pyspark.sql.functions import col
from pyspark.sql.types import DoubleType, IntegerType, StringType

# --- Khởi tạo Spark Session ---
spark = SparkSession.builder \
    .appName("RDDConversionExample") \
    .getOrCreate()

print("--- BẮT ĐẦU: Tạo RDD từ DataFrame ---")

# --- 1. Tạo DataFrame từ dữ liệu mẫu (mô phỏng salaries.csv) ---
# Dữ liệu mô phỏng tập tin salaries.csv
data = {
    'experience_level': ['EN', 'MI', 'SE', 'EN', 'MI'], 
    'salary_in_usd': [50000, 85000, 150000, 55000, 90000]
}
df_pandas = pd.DataFrame(data)
# Create a DataFrame
df = spark.createDataFrame(df_pandas)

print("-> DataFrame Gốc (df):")
df.show()
df.printSchema()

# --- 2. Convert DataFrame to RDD ---
# .rdd chuyển DataFrame thành RDD. Mỗi phần tử trong RDD là một Row object.
rdd = df.rdd

# --- 3. Collect and print the resulting RDD ---
rdd_contents = rdd.collect()

print("\n--- KẾT QUẢ: Nội dung RDD (dạng Row objects) ---")
# Show the RDD's contents
for row in rdd_contents:
    print(row)

print(f"\nKiểu dữ liệu của biến 'rdd': {type(rdd)}")

spark.stop()