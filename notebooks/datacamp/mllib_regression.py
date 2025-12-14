from pyspark.ml.feature import VectorAssembler  # Để kết hợp các cột tính năng
from pyspark.ml.regression import LinearRegression  # Mô hình hồi quy tuyến tính
from pyspark.sql import SparkSession
from pyspark.sql.types import DoubleType, StructField, StructType

# --- KHỞI TẠO SPARK SESSION ---
spark = SparkSession.builder.appName("MLlibDemo").getOrCreate()
print("--- 1. KHỞI TẠO SPARK CHO MLlib ---")

# --- 2. TẠO DỮ LIỆU MẪU (Giả sử dự đoán Giá nhà dựa trên Diện tích và Số phòng) ---
# Cột Label (giá trị mục tiêu) là 'Price'
data = [
    (100.0, 2.0, 250000.0), # Diện tích, Số phòng, Giá
    (150.0, 3.0, 350000.0),
    (75.0, 1.0, 180000.0),
    (200.0, 4.0, 420000.0),
    (120.0, 2.0, 280000.0)
]
schema = StructType([
    StructField("Area", DoubleType(), True),
    StructField("Rooms", DoubleType(), True),
    StructField("Price", DoubleType(), True) # Label
])
df = spark.createDataFrame(data, schema=schema)
print("\n--- 2. DATAFRAME GỐC (Dữ liệu Giá nhà) ---")
df.show()

# --- 3. VECTORIZATION (CHUYỂN ĐỔI TÍNH NĂNG) ---
# MLlib yêu cầu các tính năng (features) được gom vào một cột Vector duy nhất.
assembler = VectorAssembler(
    inputCols=["Area", "Rooms"],
    outputCol="Features"
)
df_vectorized = assembler.transform(df)
print("\n--- 3. DATAFRAME ĐÃ VECTORIZED ---")
df_vectorized.select("Features", "Price").show(truncate=False)

# --- 4. XÂY DỰNG MÔ HÌNH HỒI QUY TUYẾN TÍNH ---
# Khai báo mô hình, chỉ định cột Features và Label
lr = LinearRegression(
    featuresCol="Features", 
    labelCol="Price"
)

# Chia dữ liệu thành tập Huấn luyện (Training) và Kiểm tra (Test)
(trainingData, testData) = df_vectorized.randomSplit([0.7, 0.3], seed=42)

# Huấn luyện mô hình
lr_model = lr.fit(trainingData)
print("\n--- 4. MÔ HÌNH ĐÃ HUẤN LUYỆN THÀNH CÔNG ---")
print(f"Hệ số hồi quy (Coefficients): {lr_model.coefficients}")
print(f"Sai số chặn (Intercept): {lr_model.intercept}")

# --- 5. ĐÁNH GIÁ MÔ HÌNH (Dự đoán trên tập Test) ---
predictions = lr_model.transform(testData)
print("\n--- 5. DỰ ĐOÁN TRÊN TẬP TEST ---")
predictions.select("Price", "prediction").show()

# Dừng Spark Session
spark.stop()