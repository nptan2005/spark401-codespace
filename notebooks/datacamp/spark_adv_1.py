from pyspark.sql import SparkSession
from pyspark.sql.functions import avg, col  # Import hàm phân tích tổng hợp
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
my_spark = SparkSession.builder.appName("FinalProjectApp").getOrCreate()

# 3. Print my_spark để xác minh
print("--- 1. XÁC MINH SPARK SESSION ---")
print(my_spark)

# Dữ liệu và Schema định nghĩa trước
data = [
    ("Alice", 30, 150000.0, "M"),
    ("Bob", 25, 100000.0, "S"),
    ("Charlie", 35, 220000.0, "L"),
    ("David", 40, 180000.0, "M")
]

columns = StructType([
    StructField("Name", StringType(), True),
    StructField("Age", IntegerType(), True),
    StructField("Salary", DoubleType(), True),
    StructField("Company_Size", StringType(), True)
])

# 4. Load dataset into a DataFrame
df = my_spark.createDataFrame(data, schema=columns)

print("\n--- 2. DATAFRAME ĐÃ TẠO ---")
df.show()
df.printSchema()

# --- BÀI TẬP 2: CACHING VÀ PHÂN TÍCH TỔNG HỢP ---

print("\n--- 3. CACHING DATAFRAME ---")
# Cache DataFrame vào bộ nhớ đệm (RAM) của các executors.
# Mục đích: Tăng tốc độ truy cập dữ liệu cho các phép tính lặp lại (ví dụ: khi chạy mô hình ML).
df.cache()
print("DataFrame 'df' đã được cache (lưu vào bộ nhớ đệm).")


# --- 4. TIẾN HÀNH PHÂN TÍCH ---
print("\n--- 4. KẾT QUẢ PHÂN TÍCH: Lương Trung Bình theo Quy mô Công ty ---")

# Tính toán mức lương trung bình theo cột Company_Size
avg_salary_by_size = df.groupBy(col("Company_Size")).agg(avg(col("Salary")).alias("Average_Salary"))

# Hiển thị kết quả
avg_salary_by_size.show()


# --- 5. DỪNG SPARK SESSION ---
print("\n--- 5. DỪNG SPARK SESSION ---")
my_spark.stop()