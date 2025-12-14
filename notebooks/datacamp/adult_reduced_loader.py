from pyspark.sql import SparkSession
from pyspark.sql.functions import avg  # Cần import hàm avg cho phép tính toán

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
    
    # --- 3. Đếm tổng số hàng (Instructions 2) ---
    row_count = salaries_df.count()
    print(f"-> Tải thành công tệp: {file_path}")
    print(f"-> Tổng số bản ghi (rows): {row_count}")

    # Hiển thị schema để xác nhận 'salary_in_usd' là kiểu số (ví dụ: Integer, Double)
    print("\n--- SCHEMA CỦA DATAFRAME ---")
    salaries_df.printSchema()
    
    # --- 4. Nhóm theo 'company_size' và tính mức lương trung bình (Instructions 3) ---
    print("\n--- LƯƠNG TRUNG BÌNH THEO QUY MÔ CÔNG TY (USD) ---")
    salaries_df.groupBy("company_size") \
               .agg(avg("salary_in_usd").alias("average_salary_usd")) \
               .show(truncate=False)

    # Hiển thị vài dòng dữ liệu gốc để kiểm tra
    print("\n--- 5 DÒNG DỮ LIỆU GỐC ---")
    salaries_df.show(5, truncate=False)

except Exception as e:
    print(f"\n[LỖI]: Không thể tải tệp CSV. Vui lòng đảm bảo tệp '{file_path}' nằm trong thư mục hiện tại.")
    print(f"Chi tiết lỗi: {e}")

spark.stop()