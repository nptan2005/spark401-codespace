#!/bin/bash
set -e

echo ">>> Install Spark 4.0.1"

SPARK_VERSION=4.0.1
HADOOP_VERSION=3

cd /opt
sudo curl -L https://archive.apache.org/dist/spark/spark-${SPARK_VERSION}/spark-${SPARK_VERSION}-bin-hadoop${HADOOP_VERSION}.tgz \
  | sudo tar -xz

sudo ln -s /opt/spark-${SPARK_VERSION}-bin-hadoop${HADOOP_VERSION} /opt/spark

echo ">>> Set environment variables"
echo 'export SPARK_HOME=/opt/spark' >> ~/.bashrc
echo 'export PATH=$SPARK_HOME/bin:$PATH' >> ~/.bashrc
echo 'export PYSPARK_PYTHON=python3' >> ~/.bashrc

echo ">>> Install Python packages"
pip install --upgrade pip
pip install -r requirements.txt

echo "export SPARK_HOME=/opt/spark"
echo "export PATH=$SPARK_HOME/bin:$PATH"
echo "export PYSPARK_PYTHON=python3"

echo "source ~/.bashrc" >> ~/.profile

echo ">>> Done"