from pyspark.sql import SparkSession
from pyspark.sql.functions import col
from pyspark.sql.types import (  # Import các kiểu dữ liệu cần thiết
    IntegerType,
    StringType,
    StructField,
    StructType,
)

# Khởi tạo Spark Session
spark = SparkSession.builder \
    .appName("SMSDataLoaderWithSchema") \
    .getOrCreate()

print("--- 1. Bắt đầu phiên Spark để tải dữ liệu SMS ---")

# --- BÀI TẬP: ĐỊNH NGHĨA VÀ SỬ DỤNG SCHEMA ---

# Dữ liệu mẫu SMS (Mô phỏng dữ liệu phân cách bằng dấu ';')
sms_data = [
    (1, "URGENT! You have won a 1 week free holiday.", 1), # spam
    (2, "Hey, what's up?", 0), # ham
    (3, "FREE entry to a contest...", 1), # spam
    (4, "Call me when you get a chance.", 0), # ham
]

# Ghi ra CSV tạm thời (với dấu ';' là delimiter) để mô phỏng việc đọc từ file
temp_path = "temp_sms.csv"
temp_sms_df = spark.createDataFrame(sms_data, ["id", "text", "label"])
temp_sms_df.write.mode("overwrite").csv(temp_path, header=False, sep=';')


# Specify column names and types
schema = StructType([
    StructField("id", IntegerType()),
    StructField("text", StringType()),
    StructField("label", IntegerType())
])

# Load data from a delimited file
file_path = temp_path # Dùng thư mục tạm thời đã tạo
sms = spark.read.csv(file_path,
                     sep=';', # Dấu phân cách là dấu chấm phẩy
                     header=False, # Không có header
                     schema=schema) # Áp dụng Schema đã định nghĩa

print(f"\n--- 2. Tải thành công tệp từ đường dẫn: {file_path} ---")
sms.show(5, truncate=False)

# Print schema of DataFrame
print("\n--- 3. SCHEMA ĐÃ ÁP DỤNG ---")
sms.printSchema()


# Dừng Spark Session
spark.stop()