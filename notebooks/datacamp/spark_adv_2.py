from pyspark.sql import SparkSession
from pyspark.sql.functions import avg, col, sum  # Import hàm sum
from pyspark.sql.types import (
                               DoubleType,
                               IntegerType,
                               StringType,
                               StructField,
                               StructType,
)

# --- BÀI TẬP 1: KHỞI TẠO SPARK VÀ TẠO DATAFRAME ---

# 1. Import SparkSession from pyspark.sql
# Đã thực hiện ở đầu file

# 2. Tạo my_spark (Tôi sẽ dùng 'my_spark' như gợi ý)
my_spark = SparkSession.builder.appName("BringingItAllTogetherII").getOrCreate()

# 3. Print my_spark để xác minh
print("--- 1. XÁC MINH SPARK SESSION ---")
print(my_spark)

# Dữ liệu và Schema được điều chỉnh để khớp với yêu cầu GroupBy("Department").sum("Salary")
data = [
    ("HR", 50000, "M"),
    ("IT", 80000, "S"),
    ("Finance", 60000, "L"),
    ("IT", 90000, "M"),
    ("HR", 70000, "S")
]

columns = StructType([
    StructField("Department", StringType(), True),
    StructField("Salary", IntegerType(), True),
    StructField("Company_Size", StringType(), True)
])

# 4. Load dataset into a DataFrame
df = my_spark.createDataFrame(data, schema=columns)

print("\n--- 2. DATAFRAME GỐC ĐÃ TẠO ---")
df.show()
df.printSchema()

# --- BÀI TẬP 2: CACHING, EXPLAIN VÀ UNPERSIST ---

# Cache the DataFrame
print("\n--- 3. CACHING DATAFRAME ---")
# Cache DataFrame vào bộ nhớ đệm (RAM) của các executors.
df.cache()
print("DataFrame 'df' đã được cache.")


# Perform aggregation
print("\n--- 4. KẾT QUẢ TỔNG LƯƠNG THEO PHÒNG BAN ---")
agg_result = df.groupBy("Department").sum("Salary")
agg_result.show()


# Analyze the execution plan
print("\n--- 5. PHÂN TÍCH KẾ HOẠCH THỰC THI (.EXPLAIN()) ---")
# .explain() giúp bạn thấy các bước Spark sẽ thực hiện.
# Bạn sẽ thấy lệnh 'InMemoryTableScan' nếu cache hoạt động.
agg_result.explain(extended=True)


# Uncache the DataFrame
print("\n--- 6. UNPERSIST (GIẢI PHÓNG BỘ NHỚ) ---")
# Giải phóng bộ nhớ RAM mà cache đã chiếm dụng.
df.unpersist()
print("DataFrame 'df' đã được unpersist và giải phóng bộ nhớ.")


# --- 7. DỪNG SPARK SESSION ---
print("\n--- 7. DỪNG SPARK SESSION ---")
my_spark.stop()