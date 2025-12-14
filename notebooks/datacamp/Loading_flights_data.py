from pyspark.sql import SparkSession
from pyspark.sql.functions import col
from pyspark.sql.types import (
                               DoubleType,
                               IntegerType,
                               StringType,
                               StructField,
                               StructType,
)

# Khởi tạo Spark Session
# Trong môi trường thực tế, bạn sẽ dùng getOrCreate()
spark = SparkSession.builder \
    .appName("FlightDataLoader") \
    .getOrCreate()

print("--- 1. Bắt đầu phiên Spark để tải dữ liệu Chuyến bay ---")

# --- MÔ PHỎNG DỮ LIỆU CHUYẾN BAY ---
# Vì file 'flights.csv' không có sẵn, chúng ta tạo DataFrame mẫu.
# Nếu bạn có file flights.csv, bạn chỉ cần thay đổi đường dẫn trong bước 2.
flight_data = [
    (10, 15, 3, "UA", 123, "SFO", 847, 10.5, 120, 5, 'NA'),
    (10, 16, 4, "AA", 456, "JFK", 250, 12.0, 55, 0, 'NA'),
    (11, 20, 1, "DL", 789, "ORD", 600, 8.0, 90, 15, '10'),
    (11, 21, 2, "WN", 101, "ATL", 300, 15.2, 70, 0, 'NA'),
    (12, 1, 7, "UA", 202, "LAX", 1000, 9.5, 150, 20, '15'),
    # Thêm dữ liệu có giá trị NA (nullValue) và các cột số để InferSchema
]

# Định nghĩa cột (thêm một cột thừa 'extra' để đảm bảo inferSchema hoạt động tốt)
flight_columns = ["mon", "dom", "dow", "carrier", "flight", "org", "mile", "depart", "duration", "delay", "extra"]
df_flights_raw = spark.createDataFrame(flight_data, flight_columns)

# Ghi ra CSV tạm thời để mô phỏng việc đọc từ file
temp_path = "temp_flights.csv"
df_flights_raw.write.mode("overwrite").csv(temp_path, header=True)


# --- BÀI TẬP: ĐỌC DỮ LIỆU VỚI CÁC TÙY CHỌN CẦN THIẾT ---
file_path = temp_path # Dùng thư mục tạm thời đã tạo

# Read data from CSV file
flights = spark.read.csv(file_path,
                             sep=',',
                             header=True,
                             inferSchema=True,
                             nullValue='NA') # Xử lý chuỗi 'NA' là giá trị null

print(f"\n--- 2. Tải thành công tệp từ đường dẫn: {file_path} ---")

# Get number of records
record_count = flights.count()
print("\n--- 3. SỐ LƯỢNG BẢN GHI ---")
print("The data contain %d records." % record_count)

# View the first five records
print("\n--- 4. 5 DÒNG DỮ LIỆU ĐẦU TIÊN ---")
flights.show(5)

# Check column data types
print("\n--- 5. KIỂU DỮ LIỆU CỦA CÁC CỘT ---")
flights.printSchema()

# --- NHẬN XÉT VỀ KIỂU DỮ LIỆU ---
print("\n--- NHẬN XÉT: ---")
print("Các kiểu dữ liệu nhìn chung là chính xác (Integer cho mon, dom, dow, float/double cho depart, delay, v.v.).")
print("Việc sử dụng 'inferSchema=True' giúp PySpark tự động chuyển đổi các cột số.")


# Dừng Spark Session
spark.stop()