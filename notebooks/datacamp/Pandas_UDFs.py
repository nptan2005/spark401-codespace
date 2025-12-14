import pandas as pd  # Cần thiết cho việc tạo dữ liệu mẫu
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, pandas_udf
from pyspark.sql.types import DoubleType

# --- Khởi tạo Spark Session ---
spark = SparkSession.builder \
    .appName("PandasUDFExample") \
    .getOrCreate()

print("--- BẮT ĐẦU: Ví dụ về Pandas UDF (Vectorized UDF) ---")

# --- MOCK DATA: Tạo DataFrame mẫu cho bài tập ---
# Trong môi trường học tập, df đã có sẵn. Ở đây, ta tạo df_data để mô phỏng.
data = {'id': range(1, 6), 'value': [10.5, 20.0, 35.7, 42.1, 55.9]}
df_pandas = pd.DataFrame(data)
df = spark.createDataFrame(df_pandas)

print("-> DataFrame Gốc (df):")
df.show()

# --- 1. Định nghĩa Pandas UDF (Instructions 1) ---
# @pandas_udf(DoubleType()) là decorator bắt buộc để khai báo đây là Pandas UDF,
# và chỉ ra kiểu dữ liệu trả về là DoubleType.
@pandas_udf(DoubleType())
def add_ten_pandas(column: pd.Series) -> pd.Series:
    """Thêm 10 vào mỗi phần tử trong cột (thao tác vectorized)."""
    return column + 10

# --- 2. Áp dụng UDF và Hiển thị Kết quả (Instructions 2 & 3) ---
print("\n--- KẾT QUẢ: Áp dụng Pandas UDF (Thêm 10) ---")

# Apply the UDF and show the result
# Thêm cột mới "10_plus" bằng cách áp dụng hàm add_ten_pandas lên cột "value"
df_result = df.withColumn("10_plus", add_ten_pandas(col("value")))
df_result.show()

spark.stop()