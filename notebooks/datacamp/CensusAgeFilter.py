from pyspark.sql import SparkSession
from pyspark.sql.functions import col  # Chỉ cần 'col' cho việc lọc

# --- Khởi tạo Spark Session ---
# Tạo một phiên Spark, đặt tên ứng dụng là CensusAgeFilter
spark = SparkSession.builder \
    .appName("CensusAgeFilter") \
    .getOrCreate()

print("--- BẮT ĐẦU: Phân tích Dữ liệu Dân số - Lọc theo Tuổi ---")

# --- 1. Thiết lập đường dẫn tệp JSON ---
file_path = "adults.json"

# --- 2. Tải PySpark DataFrame từ tệp JSON ---
try:
    # Load the dataframe
    # JSON file thường tự động inferSchema và không cần header
    census_df = spark.read.json(file_path)

    print(f"-> Tải thành công tệp: {file_path}")
    print(f"-> Tổng số bản ghi (rows - trước khi lọc): {census_df.count()}")
    
    # Hiển thị schema để xác nhận 'age'
    print("\n--- SCHEMA CỦA DATAFRAME ---")
    census_df.printSchema()

    # --- 3. Lọc dữ liệu: Người lớn trên 40 tuổi (age > 40) ---
    print("\n--- LỌC: Dữ liệu người lớn trên 40 tuổi ---")
    
    # Filter rows based on age condition
    # Sử dụng col("age") > 40 để lọc chính xác
    filtered_census = census_df.filter(col("age") > 40)
    
    # Show the result (Hiển thị 10 hàng đầu tiên)
    filtered_count = filtered_census.count()
    print(f"-> Tổng số bản ghi sau khi lọc (Tuổi > 40): {filtered_count}")
    
    print("\n--- 10 DÒNG DỮ LIỆU ĐÃ LỌC (Tuổi > 40) ---")
    filtered_census.show(10, truncate=False)

except Exception as e:
    print(f"\n[LỖI]: Không thể tải tệp JSON. Vui lòng đảm bảo tệp '{file_path}' nằm trong thư mục hiện tại.")
    print(f"Chi tiết lỗi: {e}")

spark.stop()