from pyspark.sql import SparkSession
from pyspark.sql.functions import avg, col  # Đã thêm 'col' để lọc rõ ràng hơn

# --- Khởi tạo Spark Session ---
# Tạo một phiên Spark, đặt tên ứng dụng là CensusDataLoader
spark = SparkSession.builder \
    .appName("SalaryAggregationAnalysis") \
    .getOrCreate()

print("--- BẮT ĐẦU: Phân tích Lương Data Scientist ---")

# --- 1. Thiết lập đường dẫn tệp ---
file_path = "salaries.csv"

# --- 2. Tạo PySpark DataFrame từ tệp CSV ---
# Tải file CSV với header và inferSchema
try:
    salaries_df = spark.read.csv(
        file_path,
        header=True,
        inferSchema=True
    )
    
    # --- 3. Đếm tổng số hàng ---
    row_count = salaries_df.count()
    print(f"-> Tải thành công tệp: {file_path}")
    print(f"-> Tổng số bản ghi (rows): {row_count}")

    # Hiển thị schema để xác nhận 'salary_in_usd' là kiểu số
    print("\n--- SCHEMA CỦA DATAFRAME ---")
    salaries_df.printSchema()
    
    # --- 4. NHIỆM VỤ TRƯỚC: Lương Trung bình theo Quy mô Công ty ---
    print("\n--- LƯƠNG TRUNG BÌNH THEO QUY MÔ CÔNG TY (USD) ---")
    salaries_df.groupBy("company_size") \
               .agg(avg("salary_in_usd").alias("average_salary_usd")) \
               .show(truncate=False)

    # --- 5. NHIỆM VỤ MỚI: Lọc theo Địa điểm & Cấp độ Kinh nghiệm ---
    print("\n--- LỌC: Lương Trung bình (Entry Level - EN) tại Canada (CA) ---")

    # Lọc DataFrame: company_location == "CA" VÀ experience_level == "EN"
    # Dùng hàm col() và toán tử & (AND) để kết hợp các điều kiện lọc.
    ca_en_jobs_df = salaries_df.filter(
        (col("company_location") == "CA") & (col("experience_level") == "EN")
    )
    
    # Tính toán mức lương trung bình cho DataFrame đã lọc
    # Note: Khi không có groupBy(), .agg() sẽ tính toán trên toàn bộ DataFrame đã lọc.
    avg_salary_ca_en = ca_en_jobs_df.agg(
        avg("salary_in_usd").alias("average_salary_ca_en_usd")
    )
    
    # Hiển thị kết quả
    avg_salary_ca_en.show(truncate=False)
    
    filtered_count = ca_en_jobs_df.count()
    print(f"-> Tổng số công việc Entry Level (EN) tại Canada (CA) được lọc: {filtered_count}")

    # Hiển thị vài dòng dữ liệu gốc để kiểm tra
    print("\n--- 5 DÒNG DỮ LIỆU GỐC ---")
    salaries_df.show(5, truncate=False)

except Exception as e:
    print(f"\n[LỖI]: Không thể tải tệp CSV. Vui lòng đảm bảo tệp '{file_path}' nằm trong thư mục hiện tại.")
    print(f"Chi tiết lỗi: {e}")

spark.stop()