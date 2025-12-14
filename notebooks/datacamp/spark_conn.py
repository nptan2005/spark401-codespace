from pyspark.sql import SparkSession

# Các import khác (như VectorAssembler, LinearRegression) đã được xóa để giữ mã tập trung vào yêu cầu hiện tại.

# --- BÀI TẬP: TẠO VÀ QUẢN LÝ SPARK SESSION ---

# Import the SparkSession class (Đã thực hiện ở đầu file)

# Create SparkSession object
print("--- 1. KHỞI TẠO SPARK SESSION ---")
spark = SparkSession.builder \
                    .master("local[*]") \
                    .appName("test") \
                    .getOrCreate()

print(f"Phiên SparkSession có tên: {spark.sparkContext.appName}")
print(f"Địa chỉ Master: {spark.sparkContext.master}")

# What version of Spark?
print("\n--- 2. PHIÊN BẢN CỦA SPARK ---")
print(f"Phiên bản Spark đang chạy: {spark.version}")

# Terminate the cluster
print("\n--- 3. DỪNG CLUSTER ---")
spark.stop()
print("Cluster đã được dừng và tài nguyên đã được giải phóng.")

# Mã mô hình ML cũ đã được xóa vì yêu cầu hiện tại là tạo SparkSession.
# Để tránh lỗi, không có mã DataFrame hoặc MLlib nào được chạy sau khi spark.stop()