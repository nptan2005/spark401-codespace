from pyspark.sql import SparkSession
from pyspark.sql.types import IntegerType, StringType, StructField, StructType

# --- Khởi tạo Spark Session ---
# Tạo một phiên Spark, đặt tên ứng dụng là DefinedSchemaLoader
spark = SparkSession.builder \
    .appName("DefinedSchemaLoader") \
    .getOrCreate()

print("--- BẮT ĐẦU: Định nghĩa Schema và Tải Dữ liệu CSV ---")

# --- 1. Định nghĩa Schema (Instructions 1) ---
# Xác định kiểu dữ liệu và thứ tự cột.
schema = StructType([
    StructField("age", IntegerType()),
    StructField("education_num", IntegerType()),
    StructField("marital_status", StringType()),
    StructField("occupation", StringType()),
    StructField("income", StringType()),
])

# --- 2. Thiết lập đường dẫn tệp CSV ---
file_path = "adult_reduced_100.csv"

# --- 3. Tải PySpark DataFrame từ tệp CSV sử dụng Schema đã định nghĩa (Instructions 2) ---
try:
    # Đọc tệp CSV:
    # - sep=',' để chỉ định dấu phân cách.
    # - header=False vì chúng ta đang cung cấp schema đã bao gồm tên cột.
    # - schema=schema để áp dụng cấu trúc đã định nghĩa.
    census_adult = spark.read.csv(
        file_path, 
        sep=',', 
        header=False, 
        schema=schema
    )

    print(f"-> Tải thành công tệp: {file_path}")
    
    # --- 4. In ra Schema của DataFrame (Instructions 3) ---
    print("\n--- SCHEMA ĐƯỢC ĐỊNH NGHĨA BỞI NGƯỜI DÙNG ---")
    # Print out the schema
    census_adult.printSchema()

    # Hiển thị vài dòng dữ liệu để kiểm tra
    print("\n--- 10 DÒNG DỮ LIỆU ĐÃ TẢI ---")
    census_adult.show(10, truncate=False)

    # Lưu lại số lượng hàng ban đầu để so sánh
    initial_count = census_adult.count()
    print(f"-> Số hàng ban đầu: {initial_count}")

    # --- 5. Xử lý Dữ liệu Thiếu (Handling Missing Data) ---
    print("\n--- BẮT ĐẦU: Xử lý Dữ liệu Thiếu (Drop Nulls) ---")
    
    # Drop rows with any nulls (Loại bỏ các hàng có bất kỳ giá trị null nào)
    census_cleaned = census_adult.na.drop()
    
    # Lấy số lượng hàng đã được làm sạch
    cleaned_count = census_cleaned.count()
    
    print(f"-> Số hàng sau khi drop nulls: {cleaned_count}")
    print(f"-> Số hàng đã bị loại bỏ: {initial_count - cleaned_count}")

    # Show the result
    print("\n--- 10 DÒNG DỮ LIỆU ĐÃ LÀM SẠCH ---")
    census_cleaned.show(10, truncate=False)


except Exception as e:
    print(f"\n[LỖI]: Không thể tải tệp CSV. Vui lòng đảm bảo tệp '{file_path}' nằm trong thư mục hiện tại.")
    print(f"Chi tiết lỗi: {e}")

spark.stop()