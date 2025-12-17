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