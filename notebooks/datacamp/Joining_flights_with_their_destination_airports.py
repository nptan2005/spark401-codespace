from pyspark.sql import SparkSession
from pyspark.sql.functions import col
from pyspark.sql.types import IntegerType, StringType, StructField, StructType

# --- Khởi tạo Spark Session ---
spark = SparkSession.builder \
    .appName("FlightAirportJoiner") \
    .getOrCreate()

print("--- BẮT ĐẦU: Nối Dữ liệu Chuyến bay và Sân bay ---")

# --- MOCK DATA: Giả định DataFrames đã có sẵn trong Workspace ---
# 1. DataFrame Sân bay (airports)
airports_data = [
    ("JFK", "John F. Kennedy", "New York"),
    ("LAX", "Los Angeles Intl", "Los Angeles"),
    ("SFO", "San Francisco Intl", "San Francisco"),
    ("ORD", "O'Hare Intl", "Chicago")
]
# 'faa' là mã sân bay FAA, được dùng làm khóa chính trong bảng airports
airports_schema = ["faa", "name", "city"]
airports = spark.createDataFrame(airports_data, airports_schema)

# 2. DataFrame Chuyến bay (flights)
flights_data = [
    (1, "BOS", "JFK", 120),
    (2, "LAX", "SFO", 60),
    (3, "MIA", "JFK", 150),
    (4, "ORD", "LAX", 240) # Điểm đích là LAX
]
# 'dest' là mã sân bay đích, được dùng làm khóa ngoại trong bảng flights
flights_schema = ["flight_id", "origin", "dest", "duration"]
flights = spark.createDataFrame(flights_data, flights_schema)

print("-> DataFrame FLIGHTS (5 dòng đầu):")
flights.show(5)

# --- 1. Xem xét DataFrame airports ---
print("\n--- SCHEMA CỦA AIRPORTS (Trước khi đổi tên) ---")
airports.printSchema()
# Ghi chú: Cột khóa để nối là "faa" (trong airports) và "dest" (trong flights).

# --- 2. Đổi tên cột Khóa trong airports ---
# .withColumnRenamed() renames the "faa" column to "dest"
# Việc đổi tên giúp việc nối (join) trở nên trực quan hơn (join trên 'dest')
airports = airports.withColumnRenamed("faa", "dest")

# --- 3. Nối DataFrames ---
# Tham số: (DataFrame cần nối), on="cột chung", how="inner" (lấy các dòng khớp nhau)
# Join the DataFrames
flights_with_airports = flights.join(airports, on="dest", how="inner")

# --- 4. Xem xét DataFrame đã nối ---
print("\n--- SCHEMA CỦA FLIGHTS_WITH_AIRPORTS (Đã nối) ---")
flights_with_airports.printSchema()

print("\n--- DỮ LIỆU ĐÃ NỐI (Mỗi chuyến bay có thêm thông tin sân bay đích) ---")
flights_with_airports.show(5, truncate=False)

spark.stop()