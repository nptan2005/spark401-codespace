# Phase 3: Airflow orchestration

## Overview:
1.	Refactor job → idempotent
2.	Airflow DAG trigger Dataproc Serverless
3.	Data dependency (Bronze → Silver → Gold)
4.	Retry / alert / logging
5.	Dev (Codespace) → Prod (Composer)

## 🎯 Step 1.1 – Chuẩn hoá job cho Airflow
Airflow chạy theo schedule → cần incremental

### ✅ 1.1.1: CHỐT NGUYÊN TẮC ENTERPRISE

#### Silver:
	*	Partition by order_date
	*	Có thể overwrite theo partition

### Gold:
	*	Không overwrite toàn bảng
	*	Load theo ngày (partition)

### ✏️ SỬA silver_to_gold.py:

Nội dung edit
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

full file:
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

### Test code:

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
