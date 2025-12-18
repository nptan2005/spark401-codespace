# Phase 3: Airflow orchestration

## Overview:
1.	Refactor job → idempotent
2.	Airflow DAG trigger Dataproc Serverless
3.	Data dependency (Bronze → Silver → Gold)
4.	Retry / alert / logging
5.	Dev (Codespace) → Prod (Composer)

## 🎯 Step 1 – Chuẩn hoá job cho Airflow
Airflow chạy theo schedule → cần incremental

### ✅ 1.1: CHỐT NGUYÊN TẮC ENTERPRISE

#### Silver:
*	Partition by order_date
*	Có thể overwrite theo partition

#### Gold:
*	Không overwrite toàn bảng
*	Load theo ngày (partition)

### 1.2 ✏️ SỬA silver_to_gold.py:

#### Nội dung edit
```python
def write_gold(df, project, dataset, table):
    (
        df.write
        .format("bigquery")
        .option("table", f"{project}:{dataset}.{table}")
        .option("temporaryGcsBucket", "cdp-dem-bq-temp")
        .option("partitionField", "order_date")   # 👈 QUAN TRỌNG
        .option("partitionType", "DAY")
        .mode("append")                            # 👈 KHÔNG overwrite
        .save()
    )
```

#### full file:
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

def write_gold(df, project, dataset, table):
    (
        df.write
        .format("bigquery")
        .option("table", f"{project}:{dataset}.{table}")
        .option("temporaryGcsBucket", "cdp-dem-bq-temp")
        .option("partitionField", "order_date")   
        .option("partitionType", "DAY")
        .mode("append")                            
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

### 1.3 Test code:

1️⃣ Upload lại job
```bash
gsutil cp jobs/silver_to_gold.py gs://cdp-dem-bronze/jobs/
```
**Cần remove table cũ, do table trước đó ko có partition:**
```bash
bq rm -f -t cdp-dem-project:cdp_gold.orders
```
2️⃣ Chạy lại batch:
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
3️⃣ Check BigQuery
```bash
bq show cdp-dem-project:cdp_gold.orders
```

## Step 2: New DAG: 

**Mục tiêu:***
Codespace chỉ để DEV
Airflow chỉ để ORCHESTRATE
Spark chạy trên Dataproc Serverless

**Kiến trúc**
```text
Airflow DAG
   |
   |-- bronze_to_silver (Dataproc Serverless)
   |
   |-- silver_to_gold   (Dataproc Serverless)
```
**Thành phần:**
|Thành phần|Vai trò|
|----------|-------|
|Codespace|Dev DAG|
|Airflow local|Validate DAG|
|Dataproc Serverless|Run Spark|
|BigQuery|Serving|
|Composer|Prod (sau)|


### 2.1 📁 dags/bronze_to_gold_dag.py:

```python
from airflow import DAG
from airflow.providers.google.cloud.operators.dataproc import (
    DataprocCreateBatchOperator
)
from airflow.models import Variable
from datetime import datetime

PROJECT_ID = Variable.get("PROJECT_ID")
REGION = Variable.get("REGION")

BRONZE_PATH = Variable.get("BRONZE_PATH")
SILVER_PATH = Variable.get("SILVER_PATH")

BQ_DATASET = Variable.get("BQ_DATASET")
BQ_TABLE = Variable.get("BQ_TABLE")

JOB_BUCKET = Variable.get("JOB_BUCKET")

with DAG(
    dag_id="bronze_to_gold_dataproc_serverless",
    start_date=datetime(2025, 12, 12),
    schedule=None,
    catchup=False,
    tags=["cdp", "dataproc", "serverless"],
) as dag:

    bronze_to_silver = DataprocCreateBatchOperator(
        task_id="bronze_to_silver",
        project_id=PROJECT_ID,
        region=REGION,
        batch={
            "pysparkBatch": {
                "mainPythonFileUri": f"gs://{JOB_BUCKET}/jobs/bronze_to_silver.py",
                "args": [BRONZE_PATH, SILVER_PATH],
            }
        },
    )

    silver_to_gold = DataprocCreateBatchOperator(
        task_id="silver_to_gold",
        project_id=PROJECT_ID,
        region=REGION,
        batch={
            "pysparkBatch": {
                "mainPythonFileUri": f"gs://{JOB_BUCKET}/jobs/silver_to_gold.py",
                "args": [
                    SILVER_PATH,
                    PROJECT_ID,
                    BQ_DATASET,
                    BQ_TABLE,
                ],
            }
        },
    )

    bronze_to_silver >> silver_to_gold
```

### 2.2 TEST LOCAL (CODESPACE):

```bash
airflow dags list | grep bronze_to_gold
airflow dags test bronze_to_gold_dataproc_serverless 2025-12-12
```
**👉 Airflow sẽ:**
*	Không chạy Spark local
*	Chỉ submit Dataproc Serverless batch

## Step 3: Chuẩn hoá Airflow Dev (Professional / Bank-grade):

**<ins>Mục tiêu:</ins>**
*	Không để example DAG
*	Không lẫn DAG local / DAG prod
*	Chuẩn bị CI/CD đẩy lên Cloud Composer

### 3.1 TẮT EXAMPLE DAG:

Tắt:
```bash
export AIRFLOW__CORE__LOAD_EXAMPLES=False
```

Check:
```bash
airflow dags list | grep example
```

### 3.2 CẤU TRÚC DAG CHUẨN:

Backup dags dev and change name:
```bash
mkdir -p ./.airflow/backup_dags
mv ./.airflow/dags/* ./.airflow/backup_dags
cp ./.airflow/backup_dags/bronze_to_gold_dataproc_serverless.py ./.airflow/dags/
```
Cấu trúc:
```text
((.venv) ) @nptan2005 ➜ /workspaces/spark401-codespace (main) $ tree -L4 ./.airflow/
./.airflow/
├── README.md
├── airflow.cfg
├── airflow.db
├── backup_dags
│   ├── bronze_to_gold_dataproc_serverless.py
│   ├── bronze_to_silver_dag.py
│   ├── bronze_to_silver_gcp_dag.py
│   ├── silver_to_gold_dag.py
│   └── silver_to_gold_gcp_dag.py
├── dags
│   └── cdp_orders_bronze_to_gold.py
├── logs
├── plugins
└── requirements-airflow.txt
```

### 3.3 QUI ƯỚC ĐẶT TÊN FILE DAG:

📄 File name = business flow

🆔 dag_id = business flow

Tên đúng:
```text
cdp_orders_bronze_to_gold.py
```
```python
dag_id="cdp_orders_bronze_to_gold"
```
#### 📐 QUY ƯỚC CHUNG

🧩 File name
```code
<domain>_<subject>_<layer_flow>.py
```

**<ins>Ví dụ</ins>:**

|Use case|File|
|--------|----|
|Orders CDP|cdp_orders_bronze_to_gold.py|
|Transactions fraud|cdp_txn_bronze_to_gold.py|
|Customer 360|cdp_customer_bronze_to_gold.py|


### 3.4 ĐỔI DAG ID THEO CHUẨN:

```text
cdp_orders_bronze_to_gold
```
**Diễn giải:**
* cdp = domain
* orders = subject
* bronze_to_gold = business flow

#### 🆔 DAG ID

```code
<domain>_<subject>_<layer_flow>
```

> 👉 file name == dag_id (best practice)

#### 🔄 INFRA ĐỂ Ở ĐÂU?

> 👉 Trong code task, không trong tên:

```python
DataprocCreateBatchOperator(
    task_id="spark_bronze_to_silver",
    ...
)
```

### 3.5 ✅ QUY ƯỚC ĐẶT TÊN FILE SPARK JOB:

> **Nguyên tắc cốt lõi**
> * 👉 Tên Spark job = mô tả nghiệp vụ + tầng dữ liệu
> * 👉 KHÔNG gắn hạ tầng (dataproc / serverless / k8s / spark-submit)

#### 📐 Công thức chuẩn

```text
<domain>_<subject>_<layer>_job.py
```

#### 📊 Áp dụng cho CDP demo "Orders" cho demo này:

Bronze → Silver
```text
cdp_orders_bronze_job.py
```

Silver → Gold
```text
cdp_orders_gold_job.py
```

> 👉 layer đích là đủ

<ins>**Giải thích:**</ins>

|Lý do|Giải thích|
|-----|----------|
|Business-first|Reviewer chỉ cần tên file|
|Không phụ thuộc hạ tầng|Spark chạy ở đâu cũng được|
|Dễ mở rộng|Sau này thêm cdp_orders_risk_gold_job.py|
|Chuẩn audit|Bank & Big4 rất thích|

#### 📁 CẤU TRÚC THƯ MỤC SPARK JOB:

```text
jobs/
├── cdp/
│   └── orders/
│       ├── cdp_orders_bronze_job.py
│       ├── cdp_orders_gold_job.py
│       └── schemas.py
```

👉 Sau này:

```text
jobs/cdp/customer/
jobs/cdp/transactions/
```

#### 🧩 BÊN TRONG FILE – QUY ƯỚC BẮT BUỘC:

##### 1️⃣ main() luôn tồn tại:

```python

if __name__ == "__main__":
...
```

hoặc 

```python
def main(...):
    ...
```

##### 2️⃣ App name = giống tên file:

```python
SparkSession.builder.appName("cdp-orders-bronze")
```

> ✔ Khi xem Dataproc / Spark UI → rất rõ

##### 3️⃣ Không hardcode ENV:

**❌ Sai:**

```python
"gs://cdp-dem-silver/orders"
```

**✅ Đúng:**

```python
sys.argv[1]
```

##### 4️⃣ Một job = một trách nhiệm

**✔ Bronze job:**
* 	cast
* 	cast
* 	cast
* 	clean
* 	partition
*	audit column

**✔ Gold job:**
*	business shape
*	KPI-ready
*	push BigQuery

> 👉 Không trộn logic

##### 🔁 Mapping DAG ↔ Spark job 

|DAG|Spark job|
|---|---------|
|cdp_orders_bronze_to_gold|cdp_orders_bronze_job.py → cdp_orders_gold_job.py|

> * DAG = orchestration
> * Spark = compute

### 3.6 CHUẨN HOÁ GCP:

#### 🎯 Mục tiêu
*	Không hardcode path
* 	Dễ deploy Airflow
*	Chuẩn enterprise (Composer / CI-CD)

Đến bước này, hiện tại GCP đang có:

```bash
gs://cdp-dem-bronze/   # raw data + jobs
gs://cdp-dem-silver/   # curated parquet
gs://cdp-dem-gold/     # (optional) curated outputs
gs://cdp-dem-code/     # ⬅️ bucket này rất quan trọng
gs://cdp-dem-bq-temp/  # BigQuery temp
```

> 👉 Cần có thay đổi nhỏ

#### Chuẩn hoá:

Hiện tại bạn đang để Spark job ở:

```bash
gs://cdp-dem-bronze/jobs/
```

> ❌ không chuẩn enterprise

##### ✅ Chuẩn GCP Bucket:

|Loại|Bucket|Mục đích|
|----|------|--------|
|data|cdp-dem-bronze|raw data|
|code|cdp-dem-code|spark jobs|
|temp|cdp-dem-bq-temp|BigQuery|

##### 👉 Thực hiện:

```bash
# tạo folder logic (GCS không cần mkdir thật)
gsutil cp -r ./jobs/cdp gs://cdp-dem-code/jobs/
```

Kiểm tra:

```bash
gsutil ls gs://cdp-dem-code/jobs/cdp/orders/
```

Ta sẽ có:

```code
gs://cdp-dem-code/jobs/cdp/orders/cdp_orders_bronze_job.py
gs://cdp-dem-code/jobs/cdp/orders/cdp_orders_gold_job.py
```

✔ Không xoá jobs ở bronze vội
✔ Chuyển dần sang cdp-dem-code

##### Chuẩn hoá cách gọi Spark job (SERVERLESS / AIRFLOW READY):

**Ví dụ chuẩn (Dataproc Serverless)**
```bash
gcloud dataproc batches submit pyspark \
  gs://cdp-dem-code/jobs/cdp/orders/cdp_orders_bronze_job.py \
  --region asia-southeast1 \
  -- \
  gs://cdp-dem-bronze/orders \
  gs://cdp-dem-silver/orders
```
> ✔ Khi sang Airflow → chỉ copy

##### Chuẩn hoá Naming ENV:

|Thành phần|Chuẩn|
|----------|-----|
|Project|cdp-dem-project|
|Region|asia-southeast1|
|Dataset|cdp_gold|
|Domain|orders|



### 3.7 LOCK VERSION AIRFLOW:

Trong requirements.txt:
```text
apache-airflow==2.10.5
apache-airflow-providers-google==10.20.0
```
👉 Không dùng latest trong enterprise