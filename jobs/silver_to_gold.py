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


def write_gold(df, project: str, dataset: str, table: str):
    (
        df.write \
        .format("bigquery") \
        .option("table", f"{project}:{dataset}.{table}") \
        .option("temporaryGcsBucket", "cdp-dem-bq-temp") \
        .mode("overwrite") \
        .save()
    )


def main(silver_path, project, dataset, table):
    spark = get_spark("silver-to-gold")

    df_silver = read_silver(spark, silver_path)
    df_gold = transform_to_gold(df_silver)

    write_gold(df_gold, project, dataset, table)

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