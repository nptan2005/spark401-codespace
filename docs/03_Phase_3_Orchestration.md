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

## Step 4: Triển khai Cloud Composer 2 (Airflow enterprise)

> Codespace = code & CI
> GCP = runtime & orchestration

### 🎯 Mục tiêu:

* Có Airflow thật chạy trên GCP (Composer 2)
* DAG gọi Dataproc Serverless (không giữ cluster)
* Không hardcode secret
* Chuẩn ngân hàng / enterprise

### 4.1 TẠO CLOUD COMPOSER 2 (CHUẨN + TIẾT KIỆM):

#### ✅ Chọn version ổn định:

|Thành phần|Version|
|----------|-------|
|Composer|2.16.1|
|Airflow|2.10.5 ✅|
|Python|3.10|

> 👉 2.10.5 là bản LTS ổn định nhất hiện tại cho enterprise

#### 🔧 Lệnh tạo Composer (bản tối ưu chi phí):

##### 1️⃣ Tạo Service Account

```bash
gcloud iam service-accounts create cdp-composer-sa \
  --display-name "CDP Composer Service Account" \
  --project cdp-dem-project
```

👉 Service Account sẽ có dạng:

```code
cdp-composer-sa@cdp-dem-project.iam.gserviceaccount.com
```

##### 2️⃣ Gán quyền BẮT BUỘC
##### GÁN IAM CHUẨN (ENTERPRISE MINIMAL)

```bash
PROJECT_ID=cdp-dem-project
COMPOSER_SA=cdp-composer-sa@$PROJECT_ID.iam.gserviceaccount.com
```

1. Composer worker:

```bash
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$COMPOSER_SA" \
  --role="roles/composer.worker"
```

2. Dataproc Serverless:

```bash
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$COMPOSER_SA" \
  --role="roles/dataproc.editor"
```

3. BigQuery:

```bash
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$COMPOSER_SA" \
  --role="roles/bigquery.jobUser"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$COMPOSER_SA" \
  --role="roles/bigquery.dataEditor"
```
4. GCS (bronze / silver / gold / temp):

```bash
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$COMPOSER_SA" \
  --role="roles/storage.objectAdmin"
```

5. Gán role Composer ServiceAgentV2Ext:

Xác định Composer Service Agent

```code
service-585752501826@cloudcomposer-accounts.iam.gserviceaccount.com
```

Grant

```bash
PROJECT_ID=cdp-dem-project
COMPOSER_AGENT=service-585752501826@cloudcomposer-accounts.iam.gserviceaccount.com

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$COMPOSER_AGENT" \
  --role="roles/composer.ServiceAgentV2Ext"
```
hoặc

```bash
PROJECT_ID=cdp-dem-project

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:service-585752501826@cloudcomposer-accounts.iam.gserviceaccount.com" \
  --role="roles/composer.ServiceAgentV2Ext"
```

> 📌 Đây là set quyền chuẩn CDP enterprise (không dư)

#### TẠO COMPOSER

> ⚠️ Chạy một lần, mất ~20–30 phút

```bash
gcloud composer environments create cdp-airflow \
  --location asia-southeast1 \
  --image-version composer-3-airflow-2.10.5 \
  --environment-size small \
  --service-account cdp-composer-sa@cdp-dem-project.iam.gserviceaccount.com \
  --project cdp-dem-project
```


##### 📌 Giải thích nhanh:
*	environment-size small → tiết kiệm ~$250/tháng
*	Không bật K8s workload dư
*	Không custom image (chưa cần)

##### Check

```bash
gcloud composer environments describe cdp-airflow \
  --location asia-southeast1
```

##### Check status

```bash
gcloud composer environments describe cdp-airflow \
  --location asia-southeast1 \
  --project cdp-dem-project \
  --format="value(state)"
```

##### Check log

```bash
gcloud composer operations list \
  --locations asia-southeast1 \
  --project cdp-dem-project
```

```bash
gcloud composer operations describe <OPERATION_ID> \
  --location asia-southeast1
```

Ex:

```bash
gcloud composer operations describe 7e86687f-6839-41fe-83be-ffe3da51d751 \
  --location asia-southeast1
```

#### Delete Composer

```bash
gcloud composer environments delete cdp-airflow \
  --location asia-southeast1 \
  --project cdp-dem-project
```

##### Đánh gía tiêu chuẩn:

|Thành phần|Chuẩn enterprise|
|----------|----------------|
|Composer SA riêng|✅|
|Không dùng default SA|✅|
|Tách quyền Dataproc|✅|
|Tách quyền BigQuery|✅|
|Composer ServiceAgentV2Ext|✅ (cái này nhiều người thiếu)|

## Step 5: Airflow Enterprise trên GCP (Composer 3 + Dataproc Serverless)

#### 🎯 Mục tiêu:

* Codespace chỉ để code & CI/CD
* Airflow chạy 100% trên GCP
* Spark chạy bằng Dataproc Serverless
* Cấu trúc đúng chuẩn Enterprise / Banking

### 5.1 – LẤY DAG BUCKET CỦA COMPOSER

```bash
gcloud composer environments describe cdp-airflow \
  --location asia-southeast1 \
  --project cdp-dem-project \
  --format="value(config.dagGcsPrefix)"
```

📌Kết quả:

```code
gs://asia-southeast1-cdp-airflow-e00866e0-bucket/dags
```

👉Đây là:
```code
COMPOSER_DAG_BUCKET
```

### 5.2 QUY ƯỚC CHUẨN ENTERPRISE:

#### 📂 Local (Codespace):

```code
.airflow/
└── dags/
    └── cdp/
        └── orders/
            └── cdp_orders_bronze_to_gold.py
```

>👉 **Mỗi domain = 1 folder**
>* cdp/orders
>* cdp/customers
>* cdp/transactions

### 5.3 UPLOAD DAG LÊN COMPOSER

```bash
gsutil rsync -r .airflow/dags/cdp \
  gs://asia-southeast1-cdp-airflow-e00866e0-bucket/dags/cdp
```

>📌 **Lưu ý:**
>* KHÔNG cần restart
>* Airflow auto-detect sau 30–60s

### 5.4 KIỂM TRA AIRFLOW UI:

```bash
gcloud composer environments describe cdp-airflow \
  --location asia-southeast1 \
  --project cdp-dem-project \
  --format="value(config.airflowUri)"
```

> ➡️ Mở link → đăng nhập Google

sẽ thấy DAG:
```code
cdp_orders_bronze_to_gold
```
### 5.5 DAG CHUẨN ENTERPRISE (Dataproc Serverless)

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
BQ_DATASET = Variable.get("BQ_DATASET")
BQ_TABLE = Variable.get("BQ_TABLE")

with DAG(
    dag_id="cdp_orders_bronze_to_gold",
    start_date=datetime(2024, 1, 1),
    schedule=None,
    catchup=False,
    tags=["cdp", "orders", "dataproc", "serverless"],
) as dag:

    bronze_to_silver = DataprocCreateBatchOperator(
        task_id="bronze_to_silver",
        project_id=PROJECT_ID,
        region=REGION,
        batch={
            "pyspark_batch": {
                "main_python_file_uri": f"gs://{JOB_BUCKET}/jobs/cdp/orders/cdp_orders_bronze_job.py",
                "args": [
                    BRONZE_PATH,
                    SILVER_PATH,
                ],
            }
        },
    )

    silver_to_gold = DataprocCreateBatchOperator(
        task_id="silver_to_gold",
        project_id=PROJECT_ID,
        region=REGION,
        batch={
            "pyspark_batch": {
                "main_python_file_uri": f"gs://{JOB_BUCKET}/jobs/cdp/orders/cdp_orders_gold_job.py",
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

#### 📌 LƯU Ý KHÁC BIỆT LOCAL TEST VS CLOUD (SERVERLESS VS CLUSTER)

|Thành phần|Cluster|Serverless|
|----------|-------|----------|
|Operator|DataprocSubmitJobOperator ❌|DataprocCreateBatchOperator ✅|
|placement.cluster_name|Bắt buộc|❌ Không dùng|
|Batch|❌|✅|
|Pay-per-job|❌|✅|
|Enterprise|⚠️|✅|


### 5.6 AIRFLOW VARIABLES (TRÊN COMPOSER):

> **Airflow UI → Admin → Variables:**

|Key|Value|
|---|-----|
|PROJECT_ID|cdp-dem-project|
|REGION|asia-southeast1|
|JOB_BUCKET|cdp-dem-code|
|BRONZE_PATH|gs://cdp-dem-bronze/orders|
|SILVER_PATH|gs://cdp-dem-silver/orders|
|BQ_DATASET|cdp_gold|
|BQ_TABLE|orders|

### 5.7 COPY JOB 

```bash
gsutil cp jobs/cdp/orders/cdp_orders_bronze_job.py gs://cdp-dem-bronze/jobs/cdp/orders

gsutil cp jobs/cdp/orders/cdp_orders_gold_job.py gs://cdp-dem-bronze/jobs/cdp/orders
```

### 5.8 RUN DAG 🎉:

>➡️ **Trigger DAG**
>➡️ **Theo dõi:**
>* Dataproc → Batches
>* BigQuery → table cdp_gold.orders

### 5.9 fix lỗi (1):

#### IAM / GCP security:

##### ❌ Lỗi:

```code
User not authorized to act as service account
'585752501826-compute@developer.gserviceaccount.com'
```

**👉 Ý nghia**

>Cloud Composer (Airflow) đang muốn impersonate service account
>585752501826-compute@developer.gserviceaccount.com
>nhưng KHÔNG được phép.

#### 🔍 TẠI SAO AIRFLOW LẠI DÙNG COMPUTE SA?

**Mặc định:**
* Dataproc Serverless nếu không chỉ định execution_config.service_account
* 👉 nó fallback về Compute Engine default SA

```code
<PROJECT_NUMBER>-compute@developer.gserviceaccount.com
```
> 👉 Và Composer worker SA không có quyền “actAs” SA này

#### ✅ CÁCH ĐÚNG – ENTERPRISE FIX (BẮT BUỘC)

Có 2 cách, nhưng CHỈ CÁCH 2 LÀ ĐÚNG CHUẨN BANK/ENTERPRISE.

##### 🚫 CÁCH 1 (TẠM)

Cho Composer actAs Compute SA

```bash
PROJECT_ID=cdp-dem-project
PROJECT_NUMBER=585752501826

gcloud iam service-accounts add-iam-policy-binding \
  ${PROJECT_NUMBER}-compute@developer.gserviceaccount.com \
  --member="serviceAccount:cdp-composer-sa@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/iam.serviceAccountUser"
```

**⚠️ Không khuyến nghị vì:**
>*	Compute SA = quyền rất rộng
>*	Không audit tốt
>*	Không đạt chuẩn bank

##### ✅ CÁCH 2 (CHUẨN ENTERPRISE – BẮT BUỘC DÙNG)

###### 🎯 TẠO SERVICE ACCOUNT RIÊNG CHO DATAPROC SERVERLESS

```bash
gcloud iam service-accounts create cdp-dataproc-sa \
  --display-name "CDP Dataproc Serverless SA" \
  --project cdp-dem-project
```

```code
DATAPROC_SA=cdp-dataproc-sa@cdp-dem-project.iam.gserviceaccount.com
```

###### 🔐 GÁN ROLE CHUẨN

```bash
DATAPROC_SA=cdp-dataproc-sa@cdp-dem-project.iam.gserviceaccount.com

gcloud projects add-iam-policy-binding cdp-dem-project \
  --member="serviceAccount:$DATAPROC_SA" \
  --role="roles/dataproc.worker"

gcloud projects add-iam-policy-binding cdp-dem-project \
  --member="serviceAccount:$DATAPROC_SA" \
  --role="roles/storage.objectAdmin"

gcloud projects add-iam-policy-binding cdp-dem-project \
  --member="serviceAccount:$DATAPROC_SA" \
  --role="roles/bigquery.dataEditor"

gcloud projects add-iam-policy-binding cdp-dem-project \
  --member="serviceAccount:$DATAPROC_SA" \
  --role="roles/bigquery.jobUser"
```

###### 🔑 CHO COMPOSER ĐƯỢC IMPERSONATE SA NÀY

```bash
gcloud iam service-accounts add-iam-policy-binding \
  $DATAPROC_SA \
  --member="serviceAccount:cdp-composer-sa@cdp-dem-project.iam.gserviceaccount.com" \
  --role="roles/iam.serviceAccountUser"
```
> 👉 ĐÂY LÀ DÒNG QUYẾT ĐỊNH

###### 🛠️ SỬA DAG (BẮT BUỘC)

Trong DataprocCreateBatchOperator PHẢI CHỈ RÕ service_account

```python
DataprocCreateBatchOperator(
    task_id="bronze_to_silver",
    project_id=PROJECT_ID,
    region=REGION,
    batch={
        "pyspark_batch": {
            "main_python_file_uri": "...",
            "args": [...],
        },
        "environment_config": {
            "execution_config": {
                "service_account": "cdp-dataproc-sa@cdp-dem-project.iam.gserviceaccount.com"
            }
        }
    },
)
```

##### Runtime config:

```python
"runtime_config": {
    "properties": {
        # Driver
        "spark.driver.cores": "4",
        "spark.driver.memory": "4g",

        # Executor
        "spark.executor.cores": "4",
        "spark.executor.memory": "4g",
        "spark.executor.instances": "2",

        # Optional – giảm overhead
        "spark.sql.shuffle.partitions": "8",
    }
}
```

|Tham số|Giá trị hợp lệ|
|-------|--------------|
|spark.driver.cores|4 / 8 / 16|
|spark.executor.cores|4 / 8 / 16|
|spark.executor.instances|>= 2|
|spark.driver.memory|≥ 4g (khuyến nghị)|
|spark.executor.memory|≥ 4g|


###### UPLOAD DAG LÊN COMPOSER

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
BQ_DATASET = Variable.get("BQ_DATASET")
BQ_TABLE = Variable.get("BQ_TABLE")

with DAG(
    dag_id="cdp_orders_bronze_to_gold",
    start_date=datetime(2024, 1, 1),
    schedule=None,
    catchup=False,
    tags=["cdp", "orders", "dataproc", "serverless"],
) as dag:

    bronze_to_silver = DataprocCreateBatchOperator(
        task_id="bronze_to_silver",
        project_id=PROJECT_ID,
        region=REGION,
        batch={
            "pyspark_batch": {
                "main_python_file_uri": (
                    f"gs://{JOB_BUCKET}/jobs/cdp/orders/cdp_orders_bronze_job.py"
                ),
                "args": [
                    BRONZE_PATH,
                    SILVER_PATH,
                ],
            },

            # ✅ ĐÚNG: runtime_config nằm trong batch
            "runtime_config": {
                "properties": {
                    # Driver
                    "spark.driver.cores": "4",
                    "spark.driver.memory": "4g",

                    # Executor
                    "spark.executor.cores": "4",
                    "spark.executor.memory": "4g",
                    "spark.executor.instances": "2",

                    # Optional – giảm overhead
                    "spark.sql.shuffle.partitions": "8",
                }
            },
            "environment_config": {
                "execution_config": {
                    "service_account": (
                        "cdp-dataproc-sa@cdp-dem-project.iam.gserviceaccount.com"
                    )
                }
            },
        },
    )

    silver_to_gold = DataprocCreateBatchOperator(
        task_id="silver_to_gold",
        project_id=PROJECT_ID,
        region=REGION,
        batch={
            "pyspark_batch": {
                "main_python_file_uri": f"gs://{JOB_BUCKET}/jobs/cdp/orders/cdp_orders_gold_job.py",
                "args": [
                    SILVER_PATH,
                    PROJECT_ID,
                    BQ_DATASET,
                    BQ_TABLE,
                ],
            },
             # ✅ ĐÚNG: runtime_config nằm trong batch
            "runtime_config": {
                "properties": {
                    # Driver
                    "spark.driver.cores": "4",
                    "spark.driver.memory": "4g",

                    # Executor
                    "spark.executor.cores": "4",
                    "spark.executor.memory": "4g",
                    "spark.executor.instances": "2",

                    # Optional – giảm overhead
                    "spark.sql.shuffle.partitions": "8",
                }
            },
            "environment_config": {
                "execution_config": {
                    "service_account": (
                        "cdp-dataproc-sa@cdp-dem-project.iam.gserviceaccount.com"
                    )
                }
            },
        }
    )

    bronze_to_silver >> silver_to_gold
```

Copy

```bash
gsutil rsync -r .airflow/dags/cdp \
  gs://asia-southeast1-cdp-airflow-e00866e0-bucket/dags/cdp
```

### 5.10 fix lỗi (2):

### bị CHẶN QUOTA GCP

#### ❌ NGUYÊN NHÂN LỖI

Dataproc Serverless Spark tự scale tài nguyên Compute Engine phía sau.

Log báo 3 lỗi quota:

```code
1. Insufficient 'CPUS_ALL_REGIONS'
   Requested: 12.0
   Available: 0.0

2. Insufficient 'DISKS_TOTAL_GB'
   Requested: 1200 GB
   Available: 844 GB

3. CPU quota exceeded (min 2 workers required)
```

>👉 Tài khoản GCP Free / new project:
>*	CPU quota = 0
>*	Disk quota = < 1TB
>* Serverless Spark → đòi quota rất cao ngay từ đầu

* ⛔ Không có cách “config nhỏ hơn nữa” để né quota này
* ⛔ Không phải bug

#### 🎯 MỤC TIÊU HIỆN TẠI

> “Chạy xong pipeline Bronze → Silver → Gold 1 lần thành công

**→ Cách NGẮN NHẤT – ÍT ĐỤNG NHẤT – CHẮC CHẠY**

#### ✅ CÁCH FIX

> 👉 CHUYỂN TẠM THỜI SANG DATAPROC CLUSTER (ON-DEMAND)

KHÔNG đổi Spark code
KHÔNG đổi DAG logic
CHỈ đổi operator

##### Nguyên nhân:

|Serverless|Dataproc Cluster|
|----------|----------------|
|Quota CPU|❌ bị chặn|
|Disk quota|❌ cao|
|Min cores|4–8|
|Mục tiêu học/demo|❌|

##### So sánh Dataproc Batch Job (Serverless) vs Dataproc Cluster

**🔹 Dataproc Batch Job (Serverless)**

|Tiêu chí|Batch Job|
|--------|---------|
|Cách chạy||Mỗi job → spin up Spark riêng|
|Quản lý cluster|❌ Không|
|Quota|❌ Rất gắt (CPU, Disk)|
|Free tier|❌ Dễ fail|
|Control Spark config|❌ Bị giới hạn|
|Airflow|Dùng DataprocCreateBatchOperator|
|Phù hợp|Job nhỏ, ad-hoc, prod có quota lớn|

**📌 Thực tế bạn gặp hôm nay**
>**→ Fail liên tục vì:**
* CPU cores bắt buộc 4/8/16
* Min executor ≥ 2
* Quota CPU/DISK không đủ

**⛔ Kết luận:**
> 👉 KHÔNG phù hợp tài khoản GCP Free / học tập

**🔹 Dataproc Cluster (Classic)**

|Tiêu chí|Cluster|
|--------|-------|
|Cách chạy|1 cluster → nhiều job|
|Quản lý cluster|✅ Có|
|Quota|✅ Dễ kiểm soát|
|Free tier|✅ Khả thi|
|Control Spark config|✅ Full|
|Airflow|DataprocSubmitJobOperator|
|Phù hợp|Enterprise, learning, CDP|

**📌 Giống Hadoop / Spark on-prem**
**📌 Đúng kiến trúc ngân hàng / CDP**

**✅ Kết luận:**
> 👉 NÊN DÙNG CLUSTER – và bạn đang đi đúng hướng


#### 🛠 FIX CỤ THỂ

##### 1️⃣ TẠO CLUSTER NHỎ NHẤT

```bash
gcloud dataproc clusters create cdp-demo \
  --region asia-southeast1 \
  --master-machine-type e2-standard-2 \
  --worker-machine-type e2-standard-2 \
  --num-workers 2 \
  --master-boot-disk-size 50 \
  --worker-boot-disk-size 50 \
  --image-version 2.2-debian12 \
  --project cdp-dem-project
```

|Thành phần|Dung lượng|
|----------|----------|
|OS + Spark|~10–15GB|
|Log|~5GB|
|Job demo|<1GB|

**💡 Cluster này:**
*	2 worker
*	rẻ
*	đủ chạy Spark demo

##### Bỏ DataprocCreateBatchOperator dùng DataprocSubmitJobOperator

Mẫu

```python
from airflow.providers.google.cloud.operators.dataproc import DataprocSubmitJobOperator

bronze_to_silver = DataprocSubmitJobOperator(
    task_id="bronze_to_silver",
    project_id=PROJECT_ID,
    region=REGION,
    job={
        "placement": {
            "cluster_name": "cdp-demo"
        },
        "pyspark_job": {
            "main_python_file_uri": "gs://cdp-dem-code/jobs/cdp/orders/cdp_orders_bronze_job.py",
            "args": [
                BRONZE_PATH,
                SILVER_PATH,
            ],
        },
    },
)
```

##### 🚀 CHẠY SPARK JOB BẰNG CLI

###### Bronze → Silver
```bash
gcloud dataproc jobs submit pyspark \
  gs://cdp-dem-code/jobs/cdp/orders/cdp_orders_bronze_job.py \
  --cluster cdp-demo \
  --region asia-southeast1 \
  -- \
  gs://cdp-dem-bronze/orders \
  gs://cdp-dem-silver/orders
```

Check

```bash
gsutil ls gs://cdp-dem-silver/orders/
```

###### Silver → Gold (BigQuery)

```bash
gcloud dataproc jobs submit pyspark \
  gs://cdp-dem-code/jobs/cdp/orders/cdp_orders_gold_job.py \
  --cluster cdp-demo \
  --region asia-southeast1 \
  -- \
  gs://cdp-dem-silver/orders \
  cdp-dem-project \
  cdp_gold \
  orders
```

Check BigQuery:

```bash
bq show cdp-dem-project:cdp_gold.orders
```

###### TEST DAG:

```bash
airflow dags test cdp_orders_bronze_to_gold 2025-12-19
```

##### 🧹 SAU KHI CHẠY XONG DELETE

```bash
gcloud dataproc clusters delete cdp-demo \
  --region asia-southeast1 \
  --project cdp-dem-project
```

> Bước 5 thực hiện có phát sinh lôi do môi trường, ài vậy sẽ chuyển qua bước 4 (thực chất làm làm lại bước 5 với cách dùng dataproc cluster)

## Step 6: Cloud Composer (Enterprise Airflow):

### 🎯 Mục tiêu:
*	Airflow chạy thật trên GCP (không local)
*	DAG giống hệt DAG bạn vừa test thành công
*	Spark chạy trên Dataproc Cluster (tạm thời – phù hợp free quota)
*	Codespace = DEV
*	Composer = PROD orchestration

### 🔒 NGUYÊN TẮC:

> ❌ **KHÔNG** tạo Composer khi:

*	Dataproc cluster đang chạy không cần thiết
*	Chưa gán đúng Service Account

> ✅ **Composer** = tốn tiền nhất, nên:

*	Tạo → test → xóa
*	Không để chạy qua đêm

### 🧱 6.0: PRE-CHECK

#### 1. Xác nhận trạng thái hiện tại:

```bash
# Không còn cluster cũ
gcloud dataproc clusters list \
  --region asia-southeast1 \
  --project cdp-dem-project

# Không còn composer
gcloud composer environments list \
  --locations asia-southeast1 \
  --project cdp-dem-project
```

👉 Kết quả mong muốn

```code
Listed 0 items.
```

#### 2. Billing an toàn:

```text
Billing → Overview
```

> ✔ Remaining credit > 0
> ✔ Charges ≈ 0

### 6.1 SERVICE ACCOUNT:

Composer TUYỆT ĐỐI không dùng default SA.

#### 6.1.1 Tạo Service Account cho Composer:

```bash
gcloud iam service-accounts create cdp-composer-sa \
  --display-name "CDP Composer Service Account" \
  --project cdp-dem-project
```

**📌 SA:**

```text
cdp-composer-sa@cdp-dem-project.iam.gserviceaccount.com
```

#### 6.1.2 Gán IAM tối thiểu (BANK-GRADE):

```bash
PROJECT_ID=cdp-dem-project
COMPOSER_SA=cdp-composer-sa@$PROJECT_ID.iam.gserviceaccount.com
```

##### Composer worker

```bash
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$COMPOSER_SA" \
  --role="roles/composer.worker"
```

##### Dataproc

```bash
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$COMPOSER_SA" \
  --role="roles/dataproc.editor"
```

##### BigQuery

```bash
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$COMPOSER_SA" \
  --role="roles/bigquery.jobUser"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$COMPOSER_SA" \
  --role="roles/bigquery.dataEditor"
```

##### GCS

```bash
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$COMPOSER_SA" \
  --role="roles/storage.objectAdmin"
```

#### 6.1.3 Composer Service Agent (HAY BỊ THIẾU ❗):

```bash
PROJECT_NUMBER=585752501826
```

```bash
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:service-${PROJECT_NUMBER}@cloudcomposer-accounts.iam.gserviceaccount.com" \
  --role="roles/composer.ServiceAgentV2Ext"
```

> 📌 Nếu thiếu role này → Composer FAIL âm thầm

### 6.2 ☁️ TẠO CLOUD COMPOSER (TIẾT KIỆM):

#### 6.2.1 Chọn version CHUẨN

|Thành phần|Version|
|----------|-------|
|Composer|3|
|Airflow|2.10.5 ✅|
|Python|3.10|
|Size|small|

#### 6.2.3 Lệnh tạo Composer

⏳ 20–30 phút

```bash
gcloud composer environments create cdp-airflow \
  --location asia-southeast1 \
  --image-version composer-3-airflow-2.10.5 \
  --environment-size small \
  --service-account cdp-composer-sa@cdp-dem-project.iam.gserviceaccount.com \
  --project cdp-dem-project
```

#### 6.2.3 Theo dõi trạng thái:

```bash
gcloud composer environments describe cdp-airflow \
  --location asia-southeast1 \
  --project cdp-dem-project \
  --format="value(state)"
```

✔ RUNNING → OK
❌ ERROR → DỪNG

### 6.3 ĐẨY DAG LÊN COMPOSER

#### 6.3.1 Lấy DAG bucket:

```bash
gcloud composer environments describe cdp-airflow \
  --location asia-southeast1 \
  --project cdp-dem-project \
  --format="value(config.dagGcsPrefix)"
```

📌 Ví dụ:

```code
gs://asia-southeast1-cdp-airflow-xxxx-bucket/dags
```

Kết quả:

```code
gs://asia-southeast1-cdp-airflow-96b66680-bucket/dags
```

#### 6.3.2 Upload DAG

```bash
gsutil rsync -r .airflow/dags/cdp \
  gs://asia-southeast1-cdp-airflow-96b66680-bucket/dags/cdp
```

⏱ Sau ~30–60s DAG sẽ xuất hiện

#### 6.3.3 Mở Airflow UI

```bash
gcloud composer environments describe cdp-airflow \
  --location asia-southeast1 \
  --project cdp-dem-project \
  --format="value(config.airflowUri)"
```

👉 Login → thấy DAG:

```code
cdp_orders_bronze_to_gold
```

### 6.4 AIRFLOW VARIABLES

**Airflow UI → Admin → Variables**

|Key|Value|
|---|-----|
|PROJECT_ID|cdp-dem-project|
|REGION|asia-southeast1|
|JOB_BUCKET|cdp-dem-code|
|BRONZE_PATH|gs://cdp-dem-bronze/orders|
|SILVER_PATH|gs://cdp-dem-silver/orders|
|BQ_DATASET|cdp_gold|
|BQ_TABLE|orders|

### 6.5 TẠO DATAPROC CLUSTER:

#### 1️⃣ Tạo Dataproc cluster cdp-demo

```bash
gcloud dataproc clusters create cdp-demo \
  --region asia-southeast1 \
  --master-machine-type e2-standard-2 \
  --worker-machine-type e2-standard-2 \
  --num-workers 2 \
  --master-boot-disk-size 50 \
  --worker-boot-disk-size 50 \
  --image-version 2.2-debian12 \
  --project cdp-dem-project
```

#### 2️⃣ Verify cluster

```bash
gcloud dataproc clusters list \
  --region asia-southeast1 \
  --project cdp-dem-project
```

✔ Thấy:

```code
cdp-demo   RUNNING
```

### 6.6 RUN DAG TRÊN GCP 🎉

1️⃣ Tạo Dataproc cluster (giống lúc test local)

2️⃣ Trigger DAG trên UI

3️⃣ Theo dõi:
* Dataproc → Jobs
* BigQuery → partition mới

### 6.7 KIỂM TRA KẾT QUÀ

#### 1️⃣ Kiểm tra trạng thái DAG trong Composer:

**Trong Composer UI:**
*	DAG: cdp_orders_bronze_to_gold
*	Cả 2 task:
	+	bronze_to_silver
	+	silver_to_gold

👉 Màu xanh (SUCCESS)
👉 Không còn retry / failed

✔ Nếu đúng → sang bước 2

#### 2️⃣ Kiểm tra dữ liệu Silver (GCS):

```bash
gsutil ls gs://cdp-dem-silver/orders/
```

Kết quả:

```code
gs://cdp-dem-silver/orders/
gs://cdp-dem-silver/orders/_SUCCESS
gs://cdp-dem-silver/orders/order_date=2024-01-01/
gs://cdp-dem-silver/orders/order_date=2024-01-02/
```

**👉 Điều này xác nhận:**
*	Spark Bronze → Silver chạy OK
*	Partition theo order_date đúng chuẩn Lakehouse

#### 3️⃣ Kiểm tra dữ liệu Gold (BigQuery)

##### 3.1 Kiểm tra table:

```bash
bq show cdp-dem-project:cdp_gold.orders
```

**Cần thấy:**
* Table tồn tại
* Partition: DAY (field: order_date)
* Có Total Rows > 0

#### 3.2 Query nhanh để xác nhận data

```sql
SELECT
  order_date,
  COUNT(*) AS cnt,
  SUM(amount) AS total_amount
FROM `cdp-dem-project.cdp_gold.orders`
GROUP BY order_date
ORDER BY order_date;
```

#### 4️⃣ Kiểm tra cost:

```bash
gcloud dataproc clusters list \
  --region asia-southeast1 \
  --project cdp-dem-project
```



### 6.8 🧹 CLEANUP 

```bash
# Xóa cluster
gcloud dataproc clusters delete cdp-demo \
  --region asia-southeast1 \
  --project cdp-dem-project

# (Optional) Xóa Composer
gcloud composer environments delete cdp-airflow \
  --location asia-southeast1 \
  --project cdp-dem-project
```

> 💰 → KHÔNG tốn tiền qua đêm

## Step 7: Testing with Batch Serverless

### ✅ 7.1 Chiến lược đúng cho Free Tier

#### 🔥 NGUYÊN TẮC SỐNG CÒN:

|Mục|Quyết định|
|---|----------|
|Dataproc|Serverless Batch|
|Cluster|❌ Không dùng|
|runtime_config|❌ Không set|
|executor|Google aut
|cores|Google auto|
|memory|Google auto|
|Batch|nhỏ, ngắn|
|Cost|Pay-per-job (vài cent)|

**👉 Chỉ truyền đúng 3 thứ:**
* main_python_file_uri
* args
* project / region

### 7.2 🧩 DAG CHUẨN DÙNG DATAPROC SERVERLESS (FREE TIER SAFE)

> 👉 Thay toàn bộ ***DataprocSubmitJobOperator*** bằng ***DataprocCreateBatchOperator***

#### ✅ DAG VERSION – SERVERLESS SAFE

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
BQ_DATASET = Variable.get("BQ_DATASET")
BQ_TABLE = Variable.get("BQ_TABLE")

with DAG(
    dag_id="cdp_orders_bronze_to_gold_serverless",
    start_date=datetime(2025, 12, 19),
    schedule=None,
    catchup=False,
    tags=["cdp", "orders", "dataproc", "serverless"],
) as dag:

    bronze_to_silver = DataprocCreateBatchOperator(
        task_id="bronze_to_silver",
        project_id=PROJECT_ID,
        region=REGION,
        batch={
            "pyspark_batch": {
                "main_python_file_uri": f"gs://{JOB_BUCKET}/jobs/cdp/orders/cdp_orders_bronze_job.py",
                "args": [
                    BRONZE_PATH,
                    SILVER_PATH,
                ],
            }
        },
    )

    silver_to_gold = DataprocCreateBatchOperator(
        task_id="silver_to_gold",
        project_id=PROJECT_ID,
        region=REGION,
        batch={
            "pyspark_batch": {
                "main_python_file_uri": f"gs://{JOB_BUCKET}/jobs/cdp/orders/cdp_orders_gold_job.py",
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

* 📌 Không có runtime_config
* 📌 Không có cluster_name
* 📌 Không có resource override

> → Google tự cấp resource tối thiểu hợp lệ

### 7.3 Service Accounts

#### ✅ 7.3.1: Xác định Service Accounts

```bash
gcloud composer environments describe cdp-airflow \
  --location asia-southeast1 \
  --project cdp-dem-project \
  --format="value(config.nodeConfig.serviceAccount)"
```

Kết quả:

```code
cdp-composer-sa@cdp-dem-project.iam.gserviceaccount.com
```

#### ✅ 7.3.2: Cấp quyền Service Account User

```bash
gcloud iam service-accounts add-iam-policy-binding \
  585752501826-compute@developer.gserviceaccount.com \
  --member="serviceAccount:cdp-composer-sa@cdp-dem-project.iam.gserviceaccount.com" \
  --role="roles/iam.serviceAccountUser" \
  --project cdp-dem-project
```

#### ✅ 7.3.3: Cấp quyền Dataproc Serverless (nếu chưa)

```bash
gcloud projects add-iam-policy-binding cdp-dem-project \
  --member="serviceAccount:cdp-composer-sa@cdp-dem-project.iam.gserviceaccount.com" \
  --role="roles/dataproc.editor"
```

#### 7.3.4 Kiểm tra:

```bash
gcloud iam service-accounts get-iam-policy \
  585752501826-compute@developer.gserviceaccount.com \
  --project cdp-dem-project
```

### 7.4 🧪 TEST CÁCH ĐÚNG (KHÔNG TỐN TIỀN TREO)

#### 7.4.1 Sync DAG lên Composer

```bash
gsutil rsync -r .airflow/dags/cdp \
  gs://asia-southeast1-cdp-airflow-96b66680-bucket/dags/cdp
```

#### 7.4.2 Trigger DAG trong UI (khuyến nghị):

👉 Composer UI → Trigger
⛔ Không dùng airflow dags test cho serverless

#### 7.4.3 Theo dõi batch

```bash
gcloud dataproc batches list \
  --region asia-southeast1 \
  --project cdp-dem-project
```

#### 7.4.4 Xem log batch:

```bash
gcloud dataproc batches describe <BATCH_ID> \
  --region asia-southeast1 \
  --project cdp-dem-project
```

```bash
gcloud dataproc batches describe 49771ca0-cd25-4a0b-a16d-1a219152890e \
  --region asia-southeast1 \
  --project cdp-dem-project
```

### 7.5 💰 CAM KẾT CHI PHÍ (RẤT QUAN TRỌNG)

|Thành phần|Có tốn tiền không|
|----------|-----------------|
|Composer|Có (nhưng rất thấp, free credit cover)|
|Dataproc Serverless Batch|Có (vài cent / job)|
|GCS|Rẻ|
|BigQuery|Free tier đủ|

👉 Không có VM treo
👉 Không có cluster sống
👉 Không có surprise bill



