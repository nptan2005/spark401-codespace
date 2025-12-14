from pyspark.sql import SparkSession

# --- Khởi tạo Spark Session ---
# Tạo một phiên Spark, đặt tên ứng dụng là CensusDataLoader
spark = SparkSession.builder \
    .appName("CensusDataLoader") \
    .getOrCreate()

print("--- BẮT ĐẦU: Tải Dữ liệu Dân số (Census Data) ---")

# --- 1. Thiết lập đường dẫn tệp ---
file_path = "adult_reduced.csv"

# --- 2. Tạo PySpark DataFrame từ tệp CSV ---
# - header=True: Dùng dòng đầu tiên trong CSV làm tên cột.
# - inferSchema=True: Spark sẽ tự động quét dữ liệu để xác định kiểu dữ liệu
#                     phù hợp cho từng cột (ví dụ: 'age' là Integer, 'income' là String).
try:
    df_census = spark.read.csv(
        file_path,
        header=True,
        inferSchema=True
    )
    
    print(f"-> Tải thành công tệp: {file_path}")
    print(f"-> Tổng số bản ghi (groups): {df_census.count()}")

    # --- 3. Hiển thị Schema (Cấu trúc dữ liệu) ---
    print("\n--- SCHEMA CỦA DATAFRAME ---")
    df_census.printSchema()
    
    # --- 4. Hiển thị 5 dòng đầu tiên của DataFrame ---
    print("\n--- 5 DÒNG DỮ LIỆU ĐẦU TIÊN (SHOW) ---")
    df_census.show(5, truncate=False)

except Exception as e:
    print(f"\n[LỖI]: Không thể tải tệp CSV. Vui lòng đảm bảo tệp '{file_path}' nằm trong thư mục hiện tại.")
    print(f"Chi tiết lỗi: {e}")

spark.stop()