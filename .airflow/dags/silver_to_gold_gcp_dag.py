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