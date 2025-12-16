from airflow import DAG
from airflow.providers.google.cloud.operators.dataproc import (
    DataprocSubmitJobOperator,
    DataprocCreateClusterOperator,
    DataprocDeleteClusterOperator,
)
from datetime import datetime

PROJECT_ID = "cdp-dem-project"
REGION = "asia-southeast1"
CLUSTER_NAME = "cdp-demo-dp"

BRONZE_PATH = "gs://cdp-dem-bronze/orders/bronze_sample.csv"
SILVER_PATH = "gs://cdp-dem-silver/orders"
BQ_DATASET = "cdp_gold"
BQ_TABLE = "orders"

default_args = {
    "owner": "cdp",
    "retries": 1,
}

with DAG(
    dag_id="cdp_bronze_silver_gold",
    default_args=default_args,
    start_date=datetime(2024, 1, 1),
    schedule=None,      # manual trigger
    catchup=False,
    tags=["cdp", "spark", "dataproc"],
) as dag:

    # (OPTIONAL) Create cluster – dùng khi muốn auto cost control
    create_cluster = DataprocCreateClusterOperator(
        task_id="create_cluster",
        project_id=PROJECT_ID,
        region=REGION,
        cluster_name=CLUSTER_NAME,
        cluster_config={
            "master_config": {
                "num_instances": 1,
                "machine_type_uri": "e2-standard-2",
                "disk_config": {"boot_disk_size_gb": 100},
            },
            "worker_config": {
                "num_instances": 2,
                "machine_type_uri": "e2-standard-2",
                "disk_config": {"boot_disk_size_gb": 100},
            },
            "software_config": {
                "image_version": "2.2-debian12"
            },
        },
    )

    bronze_to_silver = DataprocSubmitJobOperator(
        task_id="bronze_to_silver",
        project_id=PROJECT_ID,
        region=REGION,
        job={
            "placement": {"cluster_name": CLUSTER_NAME},
            "pyspark_job": {
                "main_python_file_uri": "gs://cdp-dem-code/jobs/bronze_to_silver.py",
                "args": [
                    BRONZE_PATH,
                    SILVER_PATH,
                ],
            },
        },
    )

    silver_to_gold = DataprocSubmitJobOperator(
        task_id="silver_to_gold",
        project_id=PROJECT_ID,
        region=REGION,
        job={
            "placement": {"cluster_name": CLUSTER_NAME},
            "pyspark_job": {
                "main_python_file_uri": "gs://cdp-dem-code/jobs/silver_to_gold.py",
                "args": [
                    SILVER_PATH,
                    PROJECT_ID,
                    BQ_DATASET,
                    BQ_TABLE,
                ],
            },
        },
    )

    delete_cluster = DataprocDeleteClusterOperator(
        task_id="delete_cluster",
        project_id=PROJECT_ID,
        region=REGION,
        cluster_name=CLUSTER_NAME,
        trigger_rule="all_done",
    )

    create_cluster >> bronze_to_silver >> silver_to_gold >> delete_cluster