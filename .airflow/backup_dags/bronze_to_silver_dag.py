from airflow import DAG
from airflow.providers.google.cloud.operators.dataproc import DataprocSubmitJobOperator
from datetime import datetime

PROJECT_ID = "cdp-dem-project"
REGION = "asia-southeast1"
CLUSTER = "cdp-demo-dp"

with DAG(
    dag_id="bronze_to_silver",
    start_date=datetime(2024, 1, 1),
    schedule=None,
    catchup=False,
    tags=["cdp", "bronze", "silver"],
) as dag:

    bronze_to_silver = DataprocSubmitJobOperator(
        task_id="bronze_to_silver",
        project_id=PROJECT_ID,
        region=REGION,
        job={
            "placement": {
                "cluster_name": CLUSTER
            },
            "pyspark_job": {
                "main_python_file_uri": "gs://cdp-dem-code/jobs/bronze_to_silver.py",
                "args": [
                    "gs://cdp-dem-bronze/orders/bronze_sample.csv",
                    "gs://cdp-dem-silver/orders",
                ],
            },
        },
    )