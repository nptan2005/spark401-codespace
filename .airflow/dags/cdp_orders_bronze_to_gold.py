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
    dag_id="cdp_orders_bronze_to_gold",
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
                "mainPythonFileUri": f"gs://{JOB_BUCKET}/jobs/cdp_orders_bronze_job.py",
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
                "mainPythonFileUri": f"gs://{JOB_BUCKET}/jobs/cdp_orders_gold_job.py",
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