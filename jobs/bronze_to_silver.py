import sys
from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, current_timestamp, to_timestamp
)
from pyspark.sql.types import (
    StructType, StructField,
    StringType, IntegerType, DoubleType, TimestampType
)


def get_spark(app_name: str) -> SparkSession:
    return (
        SparkSession.builder
        .appName(app_name)
        .getOrCreate()
    )


def read_bronze(spark: SparkSession, path: str):
    return (
        spark.read
        .option("header", "true")
        .csv(path)
    )


def transform_to_silver(df):
    return (
        df
        .withColumn("order_id", col("order_id").cast(IntegerType()))
        .withColumn("customer_id", col("customer_id").cast(IntegerType()))
        .withColumn("amount", col("amount").cast(DoubleType()))
        .withColumn(
            "order_ts",
            to_timestamp("order_ts", "yyyy-MM-dd HH:mm:ss")
        )
        # RULE: Silver không cho amount null
        .filter(col("amount").isNotNull())
        # audit columns
        .withColumn("processed_at", current_timestamp())
    )


def write_silver(df, path: str):
    (
        df.write
        .mode("overwrite")
        .parquet(path)
    )


def main(bronze_path: str, silver_path: str):
    spark = get_spark("bronze-to-silver")

    df_bronze = read_bronze(spark, bronze_path)
    df_silver = transform_to_silver(df_bronze)

    write_silver(df_silver, silver_path)

    spark.stop()


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(
            "Usage: spark-submit bronze_to_silver.py "
            "<bronze_path> <silver_path>"
        )
        sys.exit(1)

    bronze_path = sys.argv[1]
    silver_path = sys.argv[2]

    main(bronze_path, silver_path)