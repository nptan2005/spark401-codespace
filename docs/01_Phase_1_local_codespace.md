# AIRLOW: LOCAL (CODESPACE) -> CLOUD COMPOSER (GCP):
# PHASE 1 – Local / Codespace 

## 🅱️ B1 – CHUẨN HOÁ DAG AIRFLOW

### 1️⃣ Nguyên tắc thiết kế (rất quan trọng):
#### ❌ Không làm
	•	Không gọi gcloud trong DAG
	•	Không login trong DAG
	•	Không hardcode project / region / bucket

#### ✅ Phải làm
	•	Dùng DataprocSubmitJobOperator
	•	Config qua Variable / ENV
	•	DAG chỉ mô tả workflow, không xử lý business logic

### 2️⃣ Cấu trúc thư mục:

```
spark401-codespace/
├── .airflow
|   ├──dags
│       ├── bronze_to_silver_dag.py
│       └── silver_to_gold_dag.py
├── jobs/
│   ├── bronze_to_silver.py
│   └── silver_to_gold.py
├── configs/
│   └── env.yaml              # optional
├── requirements.txt
└── README.md
```
>>> 👉 Cloud Composer chỉ cần thư mục dags/

#### set airflow home:
```bash
export AIRFLOW_HOME=/workspaces/spark401-codespace/.airflow
```
check:
```bash
echo $AIRFLOW_HOME
```
Init lại DB (1 lần duy nhất)
```bash
airflow db init
```
Check DAG folder
```bash
airflow info | grep dags
```
list
```bash
airflow dags list
```

### 3️⃣ Chuẩn hoá DAG: bronze_to_silver:

dags/bronze_to_silver_gcp_dag.py
```python
from airflow import DAG
from airflow.providers.google.cloud.operators.dataproc import DataprocSubmitJobOperator
from airflow.models import Variable
from datetime import datetime

PROJECT_ID = Variable.get("PROJECT_ID")
REGION = Variable.get("REGION")
CLUSTER_NAME = Variable.get("DATAPROC_CLUSTER")

BRONZE_PATH = Variable.get("BRONZE_PATH")
SILVER_PATH = Variable.get("SILVER_PATH")
JOB_BUCKET = Variable.get("JOB_BUCKET")

with DAG(
    dag_id="bronze_to_silver",
    start_date=datetime(2024, 1, 1),
    schedule=None,
    catchup=False,
    tags=["cdp", "bronze", "spark"],
) as dag:

    bronze_to_silver = DataprocSubmitJobOperator(
        task_id="bronze_to_silver",
        project_id=PROJECT_ID,
        region=REGION,
        job={
            "placement": {"cluster_name": CLUSTER_NAME},
            "pyspark_job": {
                "main_python_file_uri": f"gs://{JOB_BUCKET}/jobs/bronze_to_silver.py",
                "args": [BRONZE_PATH, SILVER_PATH],
            },
        },
    )
```

### 4️⃣ Chuẩn hoá DAG: silver_to_gold:

dags/silver_to_gold_gcp_dag.py
```python
from airflow import DAG
from airflow.providers.google.cloud.operators.dataproc import DataprocSubmitJobOperator
from airflow.models import Variable
from datetime import datetime

PROJECT_ID = Variable.get("PROJECT_ID")
REGION = Variable.get("REGION")
CLUSTER_NAME = Variable.get("DATAPROC_CLUSTER")

SILVER_PATH = Variable.get("SILVER_PATH")
BQ_DATASET = Variable.get("BQ_DATASET")
BQ_TABLE = Variable.get("BQ_TABLE")
JOB_BUCKET = Variable.get("JOB_BUCKET")

with DAG(
    dag_id="silver_to_gold",
    start_date=datetime(2024, 1, 1),
    schedule=None,
    catchup=False,
    tags=["cdp", "silver", "gold", "bigquery"],
) as dag:

    silver_to_gold = DataprocSubmitJobOperator(
        task_id="silver_to_gold",
        project_id=PROJECT_ID,
        region=REGION,
        job={
            "placement": {"cluster_name": CLUSTER_NAME},
            "pyspark_job": {
                "main_python_file_uri": f"gs://{JOB_BUCKET}/jobs/silver_to_gold.py",
                "args": [SILVER_PATH, PROJECT_ID, BQ_DATASET, BQ_TABLE],
            },
        },
    )
```

### 5️⃣ Airflow Variables – LOCAL (Codespace):

Chạy 1 lần

```bash
airflow variables set PROJECT_ID cdp-dem-project
airflow variables set REGION asia-southeast1
airflow variables set DATAPROC_CLUSTER cdp-demo-dp

airflow variables set JOB_BUCKET cdp-dem-bronze
airflow variables set BRONZE_PATH gs://cdp-dem-bronze/orders
airflow variables set SILVER_PATH gs://cdp-dem-silver/orders

airflow variables set BQ_DATASET cdp_gold
airflow variables set BQ_TABLE orders
```
check:
```bash
airflow variables list
```

### 6️⃣ Test DAG local (Codespace):

⚠️ Dataproc có thể OFF, DAG vẫn parse OK

```bash
airflow dags list
airflow dags test bronze_to_silver_gcp 2025-12-12
airflow dags test silver_to_gold_gcp 2025-12-12
```

👉 Nếu Dataproc OFF → job fail là đÚNG
👉 Quan trọng: DAG parse không lỗi

