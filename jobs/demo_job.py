from pyspark.sql import SparkSession

spark = SparkSession.builder \
    .appName("Job-Demo") \
    .master("local[*]") \
    .getOrCreate()

df = spark.read.option("header", True).csv("data/sample.csv")
df.printSchema()
df.show()

spark.stop()