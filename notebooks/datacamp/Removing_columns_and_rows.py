from pyspark.sql import SparkSession
from pyspark.sql.functions import col, isnull
from pyspark.sql.types import (
                               DoubleType,
                               IntegerType,
                               StringType,
                               StructField,
                               StructType,
)

# Khởi tạo Spark Session
spark = SparkSession.builder \
    .appName("FlightDataCleaning") \
    .getOrCreate()

print("--- 1. Bắt đầu phiên Spark để xử lý dữ liệu Chuyến bay ---")

# --- MÔ PHỎNG DỮ LIỆU CHUYẾN BAY (TƯƠNG TỰ flights.csv) ---
# Thêm các cột 'flight' và 'delay' với một số giá trị null
flight_data = [
    (1, "UA", 123, "SFO", 120.0, 5.0),    # Hàng 1: Đầy đủ
    (2, "AA", 456, "JFK", 55.0, None),    # Hàng 2: 'delay' thiếu
    (3, "DL", 789, "ORD", 90.0, 15.0),   # Hàng 3: Đầy đủ
    (4, "WN", 101, None, 70.0, 0.0),      # Hàng 4: 'org' (origin) thiếu
    (5, "UA", 202, "LAX", None, 20.0),    # Hàng 5: 'duration' thiếu
    (6, "AA", 808, "BOS", 65.0, None),    # Hàng 6: 'delay' thiếu
]

flight_columns = ["id", "carrier", "flight", "org", "duration", "delay"]
flights = spark.createDataFrame(flight_data, flight_columns)

print("\n--- 2. DATAFRAME GỐC (Trước khi làm sạch) ---")
flights.show()
print(f"Tổng số bản ghi ban đầu: {flights.count()}")

# --- BÀI TẬP: LOẠI BỎ CỘT VÀ HÀNG ---

# 1. Remove the 'flight' column
flights_drop_column = flights.drop("flight")

print("\n--- 3. DATAFRAME SAU KHI LOẠI BỎ CỘT 'flight' ---")
flights_drop_column.printSchema() # Xác nhận cột 'flight' đã biến mất

# 2. Number of records with missing 'delay' values
# Đếm số hàng có giá trị NULL trong cột 'delay'
missing_delay_count = flights_drop_column.filter(col('delay').isNull()).count()

print("\n--- 4. SỐ BẢN GHI THIẾU GIÁ TRỊ TRONG CỘT 'delay' ---")
print(f"Số bản ghi thiếu 'delay': {missing_delay_count}") # Kết quả sẽ là 2

# 3. Remove records with missing 'delay' values
# Lọc bỏ các hàng có 'delay' là NULL (subset=['delay'])
flights_valid_delay = flights_drop_column.na.drop(subset=['delay'])

print("\n--- 5. DATAFRAME SAU KHI LOẠI BỎ CÁC HÀNG THIẾU 'delay' ---")
flights_valid_delay.show()
print(f"Số bản ghi sau khi lọc 'delay': {flights_valid_delay.count()}") # Kết quả sẽ là 4

# 4. Remove records with missing values in any column and get the number of remaining rows
# Lọc bỏ các hàng có bất kỳ giá trị thiếu nào (subset mặc định là tất cả các cột)
flights_none_missing = flights_valid_delay.na.drop()
remaining_count = flights_none_missing.count()

print("\n--- 6. DATAFRAME SẠCH HOÀN TOÀN (Không có giá trị thiếu ở bất kỳ cột nào) ---")
flights_none_missing.show()
print(f"Số bản ghi còn lại sau khi lọc toàn bộ giá trị thiếu: {remaining_count}") # Kết quả sẽ là 3

# Dừng Spark Session
spark.stop()