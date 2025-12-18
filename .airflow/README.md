# AIRFLOW (only code in codespace)

```
airflow/
├── dags/
│   ├── bronze_to_silver.py
│   ├── silver_to_gold.py
│   └── __init__.py
├── plugins/
├── requirements.txt
└── README.md
```

## ✍️ DAG mẫu (Dataproc Spark)

```python
from airflow import DAG
from airflow.providers.google.cloud.operators.dataproc import DataprocSubmitJobOperator
from datetime import datetime

PROJECT_ID = "cdp-dem-project"
REGION = "asia-southeast1"
CLUSTER_NAME = "cdp-demo-dp"

with DAG(
    dag_id="bronze_to_silver",
    start_date=datetime(2024, 1, 1),
    schedule=None,
    catchup=False,
) as dag:

    spark_job = {
        "reference": {"project_id": PROJECT_ID},
        "placement": {"cluster_name": CLUSTER_NAME},
        "pyspark_job": {
            "main_python_file_uri": "gs://cdp-dem-code/jobs/bronze_to_silver.py",
            "args": [
                "gs://cdp-dem-bronze/orders/bronze_sample.csv",
                "gs://cdp-dem-silver/orders",
            ],
        },
    }

    DataprocSubmitJobOperator(
        task_id="run_spark",
        job=spark_job,
        region=REGION,
        project_id=PROJECT_ID,
    )
```

### Install requirement lib for airflow:

#### 📄 requirements-airflow.txt
```text
apache-airflow==2.10.5
apache-airflow-providers-google
apache-airflow-providers-apache-spark
```

```bash
pip install -r ./airflow/requirements-airflow.tx
```

### basic config airflow
```bash
export AIRFLOW_HOME=$PWD/.airflow
airflow db init
```

### Validate & test DAG trong Codespace

#### List DAG
```bash
airflow dags list
```

#### Parse DAG (rất quan trọng):
```bash
airflow dags list-import-errors
```

### test:
```bash
airflow dags test cdp_bronze_silver_gold 2024-01-01
```

### Tắt Example DAG:
```bash
export AIRFLOW__CORE__LOAD_EXAMPLES=False
```