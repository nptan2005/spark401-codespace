from pyspark.sql import SparkSession
from pyspark.sql.functions import avg, col, desc, rank, sum
from pyspark.sql.types import IntegerType, StringType, StructField, StructType
from pyspark.sql.window import Window

# --- KHỞI TẠO SPARK VÀ TẠO DATAFRAME ---

my_spark = SparkSession.builder.appName("DataOptimizationDemo").getOrCreate()

print("--- 1. XÁC MINH SPARK SESSION ---")
print(my_spark)

# Dữ liệu mẫu
data = [
    ("Alice", "HR", 50000),
    ("Bob", "IT", 80000),
    ("Charlie", "Finance", 60000)
]

columns = StructType([
    StructField("Name", StringType(), True),
    StructField("Department", StringType(), True),
    StructField("Salary", IntegerType(), True),
])

df = my_spark.createDataFrame(data, schema=columns)

print("\n--- 2. DATAFRAME GỐC (Dữ liệu Lương) ---")
df.show()

# --- CHỦ ĐỀ 3: TỐI ƯU HÓA VỚI ĐỊNH DẠNG PARQUET ---

PARQUET_PATH = "data/employees_parquet"

# --- 3. GHI DATAFRAME SANG ĐỊNH DẠNG PARQUET ---
# .mode("overwrite") đảm bảo ghi đè nếu thư mục đã tồn tại
try:
    df.write.mode("overwrite").parquet(PARQUET_PATH)
    print(f"\n--- 3. GHI DATAFRAME THÀNH CÔNG SANG ĐỊNH DẠNG PARQUET TẠI: {PARQUET_PATH} ---")
except Exception as e:
    print(f"\nLỖI khi ghi file Parquet: {e}")

# --- 4. ĐỌC LẠI DATAFRAME TỪ PARQUET ---
try:
    df_parquet = my_spark.read.parquet(PARQUET_PATH)
    print("\n--- 4. ĐỌC LẠI DATAFRAME TỪ PARQUET (Nhanh hơn CSV) ---")
    df_parquet.show()
    df_parquet.printSchema()
except Exception as e:
    print(f"\nLỖI khi đọc file Parquet: {e}")

# --- DỪNG SPARK SESSION ---
my_spark.stop()