import pandas as pd
from pyspark.sql import SparkSession
from pyspark.sql.functions import col
from pyspark.sql.types import DoubleType, IntegerType, StringType

# --- Khởi tạo Spark Session ---
spark = SparkSession.builder \
    .appName("RDDvsDataFrameAggregation") \
    .getOrCreate()

print("--- BẮT ĐẦU: So sánh RDD và DataFrame cho Aggregation ---")

# --- 1. Tạo DataFrame mẫu (mô phỏng df_salaries đã có sẵn) ---
data = {
    'experience_level': ['EN', 'MI', 'SE', 'EN', 'MI', 'SE', 'EN', 'MI'], 
    'salary_in_usd': [50000, 85000, 150000, 55000, 90000, 160000, 60000, 100000]
}
df_pandas = pd.DataFrame(data)
df_salaries = spark.createDataFrame(df_pandas)

print("-> DataFrame Gốc (df_salaries):")
df_salaries.show()
df_salaries.printSchema()

# --- 2. Tạo RDD từ DataFrame và Thu thập kết quả ---
# Create an RDD from the df_salaries
rdd_salaries = df_salaries.rdd

# Collect and print the results
print("\n--- KẾT QUẢ 1: RDD sau khi Collect (dạng Row objects) ---")
print(rdd_salaries.collect())

# --- 3. Nhóm và tính Lương Tối đa bằng DataFrame Methods ---
print("\n--- KẾT QUẢ 2: Lương Tối đa theo Cấp độ Kinh nghiệm (DataFrame) ---")
# Group by the experience level and calculate the maximum salary
dataframe_results = df_salaries.groupBy("experience_level").agg({"salary_in_usd": 'max'})

# Show the results
dataframe_results.show()

print(f"\nKiểu dữ liệu của DataFrame Results: {type(dataframe_results)}")
print(f"Kiểu dữ liệu của RDD: {type(rdd_salaries)}")

spark.stop()