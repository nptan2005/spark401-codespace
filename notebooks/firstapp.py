from pyspark import SparkContext
logFile = "./README.md"  
sc = SparkContext("local", "first app")
SparkContext.setSystemProperty("hadoop.home.dir", "/")
sc.setLogLevel("ERROR")
logData = sc.textFile(logFile).cache()
numAs = logData.filter(lambda s: 'a' in s).count()
numBs = logData.filter(lambda s: 'b' in s).count()
print("Lines with a: %i, lines with b: %i" % (numAs, numBs))

# Tắt SparkContext khi hoàn thành
sc.stop()
