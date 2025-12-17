# Phase 2: GCP Free Tier - DataProc Serverless

* Dataproc Serverless
* GCS (Bronze / Silver)
* BigQuery (Gold)
* Airflow chỉ submit job

## Plan test:
```text
GCS Bronze (CSV)
   ↓
Dataproc Serverless (PySpark)
   ↓
GCS Silver (Parquet + partition)
   ↓
Dataproc Serverless
   ↓
BigQuery Gold
```

## BƯỚC 1: QUY ƯỚC ENTERPRISE 

### 1️⃣ Naming convention (giữ từ giờ):

|Thành phần|Quy ước|
|----------|-------|
|Project|cdp-dem-project|
|Region|asia-southeast1|
|GCS|cdp-{env}-{layer}|
|Dataset|{env}_{layer}|
|DAG|{layer}_to_{layer}|

> 👉 env = dev (free tier)

### 2️⃣ Bucket

Tách bucket không dùng chung

```text
gs://cdp-dev-bronze/
gs://cdp-dev-silver/
gs://cdp-dev-gold/
gs://cdp-dev-jobs/
```
> ❗ JOB_BUCKET ≠ BRONZE_BUCKET

## BƯỚC 2: Phase này không dùng cluster, nên sẽ xoá biến cluster:

```bash
airflow variables delete DATAPROC_CLUSTER
```
## BƯỚC 3: DAG CHUẨN SERVERLESS (ENTERPRISE STYLE):

**🧱 Bronze → Silver (Dataproc Serverless**

```python
from airflow import DAG
from airflow.providers.google.cloud.operators.dataproc import DataprocCreateBatchOperator
from airflow.models import Variable
from datetime import datetime

PROJECT_ID = Variable.get("PROJECT_ID")
REGION = Variable.get("REGION")

JOB_BUCKET = Variable.get("JOB_BUCKET")
BRONZE_PATH = Variable.get("BRONZE_PATH")
SILVER_PATH = Variable.get("SILVER_PATH")

with DAG(
    dag_id="bronze_to_silver_gcp",
    start_date=datetime(2025, 12, 12),
    schedule=None,
    catchup=False,
    tags=["cdp", "serverless", "bronze", "silver"],
) as dag:

    DataprocCreateBatchOperator(
        task_id="bronze_to_silver_gcp",
        project_id=PROJECT_ID,
        region=REGION,
        batch={
            "pyspark_batch": {
                "main_python_file_uri": f"gs://{JOB_BUCKET}/jobs/bronze_to_silver.py",
                "args": [BRONZE_PATH, SILVER_PATH],
            },
        },
    )
```

**🧱 Silver → Gold (BigQuery)**
```python
from airflow import DAG
from airflow.providers.google.cloud.operators.dataproc import DataprocCreateBatchOperator
from airflow.models import Variable
from datetime import datetime

PROJECT_ID = Variable.get("PROJECT_ID")
REGION = Variable.get("REGION")

JOB_BUCKET = Variable.get("JOB_BUCKET")
SILVER_PATH = Variable.get("SILVER_PATH")
BQ_DATASET = Variable.get("BQ_DATASET")
BQ_TABLE = Variable.get("BQ_TABLE")

with DAG(
    dag_id="silver_to_gold_gcp",
    start_date=datetime(2025, 12, 12),
    schedule=None,
    catchup=False,
    tags=["cdp", "serverless", "gold"],
) as dag:

    DataprocCreateBatchOperator(
        task_id="silver_to_gold_gcp",
        project_id=PROJECT_ID,
        region=REGION,
        batch={
            "pyspark_batch": {
                "main_python_file_uri": f"gs://{JOB_BUCKET}/jobs/silver_to_gold.py",
                "args": [SILVER_PATH, PROJECT_ID, BQ_DATASET, BQ_TABLE],
            },
        },
    )
```

## BƯỚC 4: CHECK QUYỀN (ENTERPRISE BẮT BUỘC):

Dataproc Serverless cần IAM sau:
```text
roles/dataproc.editor
roles/storage.objectAdmin
roles/bigquery.dataEditor
roles/bigquery.jobUser
```

check:
```bash
gcloud projects get-iam-policy cdp-dem-project
```

### 💰 FREE TIER – CÁCH KHÔNG BỊ ĐỐT TIỀN:

|Mục|Cách|
|---|----|
|Dataproc|Serverless only|
|VM|❌ Không dùng|
|Composer|Chưa tạo|
|Job|Manual trigger|
|Logs|Giữ mặc định|
> 👉 Mỗi DAG run chỉ vài cent

## Bước 5: VALIDATE + CHUẨN HOÁ ENTERPRISE FLOW (SERVERLESS)

### 5.1 jobs/bronze_to_silver.py
```python
import sys
from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, current_timestamp, to_timestamp
)
from pyspark.sql.types import (
    StructType, StructField,
    StringType, IntegerType, DoubleType, TimestampType
)


def get_spark(app_name: str) -> SparkSession:
    return (
        SparkSession.builder
        .appName(app_name)
        .getOrCreate()
    )


def read_bronze(spark: SparkSession, path: str):
    return (
        spark.read
        .option("header", "true")
        .csv(path)
    )


def transform_to_silver(df):
    return (
        df
        .withColumn("order_id", col("order_id").cast(IntegerType()))
        .withColumn("customer_id", col("customer_id").cast(IntegerType()))
        .withColumn("amount", col("amount").cast(DoubleType()))
        .withColumn(
            "order_ts",
            to_timestamp("order_ts", "yyyy-MM-dd HH:mm:ss")
        )
        # RULE: Silver không cho amount null
        .filter(col("amount").isNotNull())
        # audit columns
        .withColumn("processed_at", current_timestamp())
    )


def write_silver(df, path: str):
    (
        df.write \
        .mode("overwrite") \
        .partitionBy("order_date") \
        .parquet(path)
    )


def main(bronze_path: str, silver_path: str):
    spark = get_spark("bronze-to-silver")

    df_bronze = read_bronze(spark, bronze_path)
    df_silver = transform_to_silver(df_bronze)

    write_silver(df_silver, silver_path)

    spark.stop()


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(
            "Usage: spark-submit bronze_to_silver.py "
            "<bronze_path> <silver_path>"
        )
        sys.exit(1)

    bronze_path = sys.argv[1]
    silver_path = sys.argv[2]

    main(bronze_path, silver_path)
```

#### Test job Bronze_to_silver:

Tạo folder:
```bash
mkdir -p data/bronze/orders
mkdir -p data/silver/orders
```

Data:
```csv
order_id,customer_id,amount,order_ts,currency
1,101,100.5,2025-12-10 10:00:00,VND
2,102,,2025-12-10 11:00:00,VND
3,103,200.0,2025-12-11 09:30:00,VND
```

run job:
```bash
spark-submit \
  jobs/bronze_to_silver.py \
  data/bronze/orders \
  data/silver/orders
```

### 5.2 jobs/silver_to_gold.py
```python
import sys
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, to_date


def get_spark(app_name: str) -> SparkSession:
    return (
        SparkSession.builder
        .appName(app_name)
        # BigQuery connector có sẵn trên Dataproc
        .getOrCreate()
    )


def read_silver(spark: SparkSession, path: str):
    return spark.read.parquet(path)


def transform_to_gold(df):
    return (
        df
        .withColumn("order_date", to_date(col("order_ts")))
        .select(
            "order_id",
            "customer_id",
            "amount",
            "currency",
            "order_ts",
            "order_date"
        )
    )


def write_gold(df, project: str, dataset: str, table: str):
    (
        df.write \
        .format("bigquery") \
        .option("table", f"{project}:{dataset}.{table}") \
        .option("temporaryGcsBucket", "cdp-dem-bq-temp") \
        .mode("overwrite") \
        .save()
    )


def main(silver_path, project, dataset, table):
    spark = get_spark("silver-to-gold")

    df_silver = read_silver(spark, silver_path)
    df_gold = transform_to_gold(df_silver)

    write_gold(df_gold, project, dataset, table)

    # test
    # df_gold.show()
    # df_gold.printSchema()

    spark.stop()


if __name__ == "__main__":
    if len(sys.argv) != 5:
        print(
            "Usage: spark-submit silver_to_gold.py "
            "<silver_path> <project> <dataset> <table>"
        )
        sys.exit(1)

    silver_path = sys.argv[1]
    project = sys.argv[2]
    dataset = sys.argv[3]
    table = sys.argv[4]

    main(silver_path, project, dataset, table)
```

#### Test silver_to_gold:
Test local thay write_to_gold bằng:
```python
df_gold.show()
df_gold.printSchema()
```

```bash
spark-submit \
  jobs/silver_to_gold.py \
  data/silver/orders \
  dummy_project dummy_dataset dummy_table
```
### 5.3 Test job to GCP

#### 1️⃣ Kiểm tra Bronze data có thật chưa
```bash
gsutil ls gs://cdp-dem-bronze/orders/
```

#### 2️⃣ Xem thử nội dung Bronze
```bash
gsutil cat gs://cdp-dem-bronze/orders/*.csv | head
```

### 5.4 CHẠY BRONZE → SILVER (SERVERLESS):

#### ✅ STEP 5.4.1 – UPLOAD PYSPARK JOB LÊN GCS:
```bash
gsutil cp jobs/bronze_to_silver.py gs://cdp-dem-bronze/jobs/
```
```bash
gsutil cp jobs/silver_to_gold.py gs://cdp-dem-bronze/jobs/
```
Kiễm tra:
```bash
gsutil ls gs://cdp-dem-bronze/jobs/
```

#### ✅ STEP 5.4.2 – CHẠY LẠI SERVERLESS

```bash
gcloud dataproc batches submit pyspark \
  gs://cdp-dem-bronze/jobs/bronze_to_silver.py \
  --region asia-southeast1 \
  -- \
  gs://cdp-dem-bronze/orders \
  gs://cdp-dem-silver/orders
```

#### 📌 Giải thích ngắn:
	*	batches submit = Dataproc Serverless
	*	-- = bắt đầu truyền sys.argv
	*	2 path = đúng với main(bronze_path, silver_path)

#### ✅ STEP 5.4 – KIỂM TRA SILVER
```bash
gsutil ls gs://cdp-dem-silver/orders/
```

#### Giải thích job:
|Thành phần|Vai trò|
|----------|-------|
|Codespace|Viết code|
|GCS|Lưu data + job|
|Dataproc Serverless|Chạy Spark|
|BigQuery|Gold layer|
> 👉 Serverless = không cluster = đúng hướng enterprise + free tier

### STEP 5.5 – CHẠY SILVER → GOLD (BIGQUERY): 

```bash
gcloud dataproc batches submit pyspark \
  gs://cdp-dem-bronze/jobs/silver_to_gold.py \
  --region asia-southeast1 \
  -- \
  gs://cdp-dem-silver/orders \
  cdp-dem-project \
  cdp_gold \
  orders
```
Check Batch:
```bash
gcloud dataproc batches list --region asia-southeast1
```
### STEP 5.6 – KIỂM TRA BIGQUERY:

```bash
bq ls cdp-dem-project:cdp_gold
```

```bash
bq show cdp-dem-project:cdp_gold.orders
```

```bash
bq query --nouse_legacy_sql \
'SELECT COUNT(*) FROM `cdp-dem-project.cdp_gold.orders`'
```

#### Đến phase 2 - Bước 5:
	•	❌ Không cần Dataproc cluster
	•	✅ Dùng Spark Serverless
	•	✅ Spark job run

#### 🧠 NGUYÊN TẮC ENTERPRISE:

|Layer|Rule|
|-----|----|
|Bronze|raw, không rule|
|Silver|clean + audit|
|Gold|business, aggregation|
