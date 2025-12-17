from airflow import DAG
from airflow.providers.google.cloud.operators.dataproc import DataprocSubmitJobOperator
from datetime import datetime

PROJECT_ID = "cdp-dem-project"
REGION = "asia-southeast1"
CLUSTER = "cdp-demo-dp"

with DAG(
    dag_id="silver_to_gold",
    start_date=datetime(2024, 1, 1),
    schedule=None,
    catchup=False,
    tags=["cdp", "silver", "gold"],
) as dag:

    silver_to_gold = DataprocSubmitJobOperator(
        task_id="silver_to_gold",
        project_id=PROJECT_ID,
        region=REGION,
        job={
            "placement": {
                "cluster_name": CLUSTER
            },
            "pyspark_job": {
                "main_python_file_uri": "gs://cdp-dem-code/jobs/silver_to_gold.py",
                "args": [
                    "gs://cdp-dem-silver/orders",
                    "cdp-dem-project",
                    "cdp_gold",
                    "orders",
                ],
            },
        },
    )