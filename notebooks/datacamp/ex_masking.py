import random
import uuid

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, lit, rand, sha2, udf, when
from pyspark.sql.types import DoubleType, StringType

# Khởi tạo Spark Session
# Trong môi trường Cloudera CDE, SparkSession thường được tự động cấu hình.
spark = SparkSession.builder \
    .appName("BankDataMaskingAndTokenization") \
    .getOrCreate()

print("--- 1. Bắt đầu phiên Spark để xử lý Masking/Tokenization ---")

# Dữ liệu mẫu mô phỏng dữ liệu thô (Raw Data) từ Core Banking
data = [
    (1001, "Nguyễn Văn A", "1234567890", 55000000.0, "Hồ Chí Minh"),
    (1002, "Trần Thị B", "0987654321", 120000000.0, "Hà Nội"),
    (1003, "Lê Văn C", "1122334455", 85000000.0, "Đà Nẵng")
]
columns = ["Customer_ID", "Customer_Name", "Account_Number", "Monthly_Income", "City"]

df_raw = spark.createDataFrame(data, columns)
df_raw.show()

# --- 2. ẨN DANH (TOKENIZATION) CHO CÁC TRƯỜNG NHẬN DẠNG CÁ NHÂN (PII) ---
# Sử dụng SHA-256 (sha2) để tạo mã Token không thể đảo ngược (Non-reversible Hashing)
# Điều này là cần thiết để bảo vệ danh tính, nhưng vẫn cho phép theo dõi cùng một khách hàng
# trong các bộ dữ liệu khác nhau.

df_tokenized = df_raw.withColumn(
    "Customer_Token",  # Token mới cho Khách hàng
    sha2(col("Customer_ID").cast(StringType()), 256)
).withColumn(
    "Account_Token", # Token mới cho Số tài khoản
    sha2(col("Account_Number"), 256)
)

print("--- 3. CHE GIẤU DỮ LIỆU SỐ (MASKING) CHO PHÂN TÍCH THỐNG KÊ ---")

# Mục đích: Thay đổi giá trị thực tế nhưng vẫn giữ được ý nghĩa thống kê (ví dụ: Tỷ lệ, Xu hướng)
# và định dạng dữ liệu số.

# Định nghĩa Hàm UDF (User Defined Function) cho Masking
# Ví dụ: Nhân thu nhập với một hệ số ngẫu nhiên nhỏ (ví dụ: 1.05 hoặc 0.95)
# để thay đổi giá trị nhưng giữ gần với giá trị gốc (Format-Preserving Masking - FPM)
def mask_income(income):
    if income is None:
        return None
    # Tạo ngẫu nhiên một hệ số trong khoảng [0.9, 1.1]
    factor = 0.9 + (random.random() * 0.2)
    return float(income * factor)

# Đăng ký UDF
mask_income_udf = udf(mask_income, DoubleType())

df_masked = df_tokenized.withColumn(
    "Masked_Income",
    mask_income_udf(col("Monthly_Income"))
)

# --- 4. TẠO DATASET ĐÃ LÀM SẠCH (CURATED/SAFE DATASET) ĐỂ ĐỒNG BỘ LÊN PUBLIC CLOUD ---
# Chỉ chọn các cột an toàn để tuân thủ quy định.

df_safe = df_masked.select(
    "Customer_Token",
    "Account_Token",
    "City",
    "Masked_Income"
)

print("--- DỮ LIỆU GỐC (ON-PREM PII) ---")
df_raw.show(truncate=False)

print("--- DỮ LIỆU AN TOÀN (SAFE DATASET) ĐỂ ĐỒNG BỘ LÊN PUBLIC CLOUD ---")
# Lưu ý: Tên, ID, Số tài khoản đã được thay thế bằng Token, Thu nhập đã bị Mask.
df_safe.show(truncate=False)

# Giả lập việc ghi dữ liệu đã làm sạch vào lớp Curated Data Lake On-prem
# df_safe.write.mode("overwrite").parquet("/curated/banking_safe_data")

spark.stop()