from pyspark.sql import SparkSession
from pyspark.sql.functions import col  # Cần import col để thực hiện phép tính cột
from pyspark.sql.types import (
    DoubleType,
    IntegerType,
    StringType,
    StructField,
    StructType,
)

# --- Khởi tạo Spark Session ---
# Tạo một phiên Spark, đặt tên ứng dụng là DefinedSchemaLoader
spark = SparkSession.builder \
    .appName("DefinedSchemaLoader") \
    .getOrCreate()

print("--- BẮT ĐẦU: Định nghĩa Schema và Tải Dữ liệu CSV ---")

# --- 1. Định nghĩa Schema ---
schema = StructType([
    StructField("age", IntegerType()),
    StructField("education_num", IntegerType()),
    StructField("marital_status", StringType()),
    StructField("occupation", StringType()),
    StructField("income", StringType()), # Vẫn giữ StringType ở đây để phù hợp với CSV đầu vào
])

# --- 2. Thiết lập đường dẫn tệp CSV ---
file_path = "adult_reduced_100.csv"

# --- 3. Tải PySpark DataFrame từ tệp CSV sử dụng Schema đã định nghĩa ---
try:
    census_adult = spark.read.csv(
        file_path, 
        sep=',', 
        header=False, 
        schema=schema
    )

    print(f"-> Tải thành công tệp: {file_path}")
    
    # --- 4. Chuyển đổi kiểu dữ liệu cho tính toán ---
    # Chuyển cột 'income' sang DoubleType để có thể chia số
    census_df = census_adult.withColumn("income", col("income").cast(DoubleType()))
    
    # --- 5. Column Operations (Tạo và Đổi tên Cột) ---
    print("\n--- BẮT ĐẦU: Tạo và Đổi tên Cột (weekly_salary & years) ---")

    # Create a new column 'weekly_salary' bằng cách chia cột 'income' đã được cast cho 52
    # Create a new column 'weekly_salary'
    census_df_weekly = census_df.withColumn("weekly_salary", col("income") / 52)

    # Rename the 'age' column to 'years'
    census_df_weekly = census_df_weekly.withColumnRenamed("age", "years")

    # Show the result
    print("--- SCHEMA VỚI CỘT ĐÃ ĐỔI TÊN VÀ CỘT MỚI ---")
    census_df_weekly.printSchema()
    
    print("\n--- 10 DÒNG DỮ LIỆU ĐÃ CHỈNH SỬA (Có 'weekly_salary' và 'years') ---")
    census_df_weekly.show(10, truncate=False)
    
    # Giữ lại logic làm sạch để tham khảo, áp dụng trên DataFrame mới
    initial_count = census_df_weekly.count()
    print(f"\n-> Số hàng ban đầu (sau khi tạo cột): {initial_count}")

    # Xử lý Dữ liệu Thiếu (Drop Nulls) trên DataFrame mới
    print("\n--- Xử lý Dữ liệu Thiếu (Drop Nulls) sau khi tạo cột ---")
    census_cleaned = census_df_weekly.na.drop()
    cleaned_count = census_cleaned.count()
    
    print(f"-> Số hàng sau khi drop nulls: {cleaned_count}")
    print(f"-> Số hàng đã bị loại bỏ: {initial_count - cleaned_count}")

    print("\n--- 10 DÒNG DỮ LIỆU ĐÃ LÀM SẠCH VÀ CÓ CỘT MỚI ---")
    census_cleaned.show(10, truncate=False)


except Exception as e:
    print(f"\n[LỖI]: Không thể tải tệp CSV. Vui lòng đảm bảo tệp '{file_path}' nằm trong thư mục hiện tại.")
    print(f"Chi tiết lỗi: {e}")

spark.stop()