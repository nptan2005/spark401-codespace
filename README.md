# spark401-codespace

## setup environment: 

Auto activate .venv
```bash
cat <<'EOF' >> ~/.bashrc

# === Auto activate project venv ===
if [ -f "/workspaces/spark401-codespace/.venv/bin/activate" ]; then
  source /workspaces/spark401-codespace/.venv/bin/activate
fi
EOF
```

check spark:
```bash
find /opt -maxdepth 2 -type d | grep spark
```

setup PATH

```bash
cat <<'EOF' >> ~/.bashrc

# === Spark env ===
export SPARK_HOME=/opt/spark
export PATH=$SPARK_HOME/bin:$PATH
EOF
```

reload shell
```bash
source ~/.bashrc
```

## setup Jupyter:

Jupyter and Spark on codeSapce for testing

start

```bash
python -m jupyterlab --ip=0.0.0.0 --port=8888 --no-browser
```

setup bypass token jupyter

```bash
jupyter lab --generate-config
```
>>> ~/.jupyter/jupyter_lab_config.py

```bash
code ~/.jupyter/jupyter_lab_config.py
```

```python
c.ServerApp.ip = "0.0.0.0"
c.ServerApp.port = 8888

# 🔥 Disable token & password
c.ServerApp.token = ""
c.ServerApp.password = ""

# Không mở browser trong container
c.ServerApp.open_browser = False

# Cho phép chạy dưới root / container
c.ServerApp.allow_root = True
```

sau khi set no token chi cần start

```bash
python -m jupyterlab
```

Tăt token Jupyter tạm thời

```bash
python -m jupyterlab \
  --ip=0.0.0.0 \
  --port=8888 \
  --no-browser \
  --ServerApp.token='' \
  --ServerApp.password=''
```

set jupyter as auto

```bash
# Auto start Jupyter (optional)
if [ -z "$JUPYTER_STARTED" ]; then
  export JUPYTER_STARTED=1
  nohup python -m jupyterlab >/tmp/jupyter.log 2>&1 &
fi
```

## Setup Spark

setup kernel
```bash
pip install ipykernel
```

Đăng ký kernal Spark cho Jupyter:

```bash
python -m ipykernel install \
  --user \
  --name spark401 \
  --display-name "PySpark 4.0.1 (.venv)"
```

start and expose spark

```bash 
pyspark --conf spark.ui.port=4040 

```

# Setup GCP:

```
Codespaces
 ├─ code PySpark
 ├─ demo Spark UI (local)
 ├─ git push
      ↓
GCP
 ├─ GCS (Bronze/Silver/Gold)
 ├─ Dataproc (Spark cluster)
 ├─ Airflow (VM / Composer)
 └─ BigQuery (Gold serving)
```

Bước 1: install on codespace

```bash
curl -fsSL https://packages.cloud.google.com/apt/doc/apt-key.gpg \
  | sudo gpg --dearmor -o /usr/share/keyrings/cloud.google.gpg

echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" \
  | sudo tee /etc/apt/sources.list.d/google-cloud-sdk.list

sudo apt-get update
sudo apt-get install -y google-cloud-cli
```

Check version

```bash
gcloud version
```

Bước 2: login GCP from codespace

```bash
gcloud auth login
```

Bước 3: setup project

```bash
gcloud config set project cdp-dem-project
```

check

```bash
gcloud config list
```

Bước 4: enable API

```bash
gcloud services enable \
  storage.googleapis.com \
  dataproc.googleapis.com \
  compute.googleapis.com \
  iam.googleapis.com \
  bigquery.googleapis.com
```

Bước 5: Create BRONZE/SILVER/GOLD Bucket:

```bash
gsutil mb -p cdp-dem-project -l asia-southeast1 gs://cdp-dem-bronze
gsutil mb -p cdp-dem-project -l asia-southeast1 gs://cdp-dem-silver
gsutil mb -p cdp-dem-project -l asia-southeast1 gs://cdp-dem-gold
```

check:

```bash
gsutil ls
```

# Session 1: test on job

Step 1: submit job

```bash
spark-submit jobs/bronze_to_silver.py \
  data/bronze_sample.csv \
  data/silver_out
```

check:

```bash
ls data/silver_out
```

fast test:

```bash
python - <<'EOF'
from pyspark.sql import SparkSession
spark = SparkSession.builder.getOrCreate()
spark.read.parquet("data/silver_out").show()
spark.stop()
EOF
```

Step 2: to GCP

```bash
spark-submit jobs/bronze_to_silver.py \
  gs://cdp-dem-bronze/orders/bronze_sample.csv \
  gs://cdp-dem-silver/orders
```

# Session 2: Dataproc cluster + submit job thật

Step 1: setup evironment:

```bash
export PROJECT_ID=cdp-dem-project
export REGION=asia-southeast1
export ZONE=asia-southeast1-a
export CLUSTER_NAME=cdp-demo-dp
```
Step 2: Create Dataproc cluster (NHẸ – TIẾT KIỆM)

service account:

```
585752501826-compute@developer.gserviceaccount.com
```
## Phân quyền: 
* Dataproc Worker:

```bash
gcloud projects add-iam-policy-binding cdp-dem-project \
  --member="serviceAccount:585752501826-compute@developer.gserviceaccount.com" \
  --role="roles/dataproc.worker"
```

* Storage Admin (đọc/ghi GCS Bronze/Silver):

```bash
gcloud projects add-iam-policy-binding cdp-dem-project \
  --member="serviceAccount:585752501826-compute@developer.gserviceaccount.com" \
  --role="roles/storage.admin"
```

* Logging + Monitoring:
```bash
gcloud projects add-iam-policy-binding cdp-dem-project \
  --member="serviceAccount:585752501826-compute@developer.gserviceaccount.com" \
  --role="roles/logging.logWriter"

gcloud projects add-iam-policy-binding cdp-dem-project \
  --member="serviceAccount:585752501826-compute@developer.gserviceaccount.com" \
  --role="roles/monitoring.metricWriter"
``` 

check:

```bash
gcloud projects get-iam-policy cdp-dem-project \
  --flatten="bindings[].members" \
  --filter="bindings.members:585752501826-compute@developer.gserviceaccount.com" \
  --format="table(bindings.role)"
```

* Create with custom:

```bash
gcloud dataproc clusters create $CLUSTER_NAME \
  --region $REGION \
  --zone $ZONE \
  --master-machine-type e2-standard-2 \
  --worker-machine-type e2-standard-2 \
  --num-workers 2 \
  --master-boot-disk-size 100 \
  --worker-boot-disk-size 100 \
  --image-version 2.2-debian12 \
  --project $PROJECT_ID
```
Step 2: Đưa job lên GCP:


Tạo bucket chứa code (nếu chưa có):
```bash
gsutil mb -p $PROJECT_ID -l $REGION gs://cdp-dem-code || true
```

Upload file job:
```bash
gsutil cp jobs/bronze_to_silver.py gs://cdp-dem-code/jobs/bronze_to_silver.py
```

## Data to Bronze

Step 3: Chuẩn bị dữ liệu Bronze trên GCS

upload data:
```bash
gsutil cp data/bronze_sample.csv gs://cdp-dem-bronze/orders/bronze_sample.csv
```
check:
```bash
gsutil ls gs://cdp-dem-bronze/orders
```

step 4: test submit job

```bash
gcloud dataproc jobs submit pyspark \
  gs://cdp-dem-code/jobs/bronze_to_silver.py \
  --region $REGION \
  --cluster $CLUSTER_NAME \
  -- \
  gs://cdp-dem-bronze/orders/bronze_sample.csv \
  gs://cdp-dem-silver/orders
```

follow logs:
```bash
gcloud dataproc jobs list --region $REGION
```

check detail job ID:

```bash
gcloud dataproc jobs describe <JOB_ID> --region $REGION
```

check silver

```bash
gsutil ls gs://cdp-dem-silver/orders
```

check data via script:

```bash
python - <<'EOF'
from pyspark.sql import SparkSession
spark = SparkSession.builder.getOrCreate()
spark.read.parquet("gs://cdp-dem-silver/orders").show()
spark.stop()
EOF
```

## Bronze -> Silver -> Gold:

```
Bronze (GCS)
   ↓
Silver (GCS Parquet)
   ↓
Gold (BigQuery Tables)
```

Step 5: TẠO DATASET BIGQUERY:

```bash
bq mk \
  --location=$REGION \
  --dataset $PROJECT_ID:cdp_gold
```

```bash
bq mk \
  --location=asia-southeast1 \
  --dataset cdp-dem-project:cdp_gold
```

check

```bash
bq ls cdp-dem-project:cdp_gold
```

tạo staging:

```bash
gsutil mb -p cdp-dem-project -l asia-southeast1 gs://cdp-dem-bq-temp
```

step 7: grant permission

xác đinh acct
```bash
gcloud dataproc clusters describe cdp-demo-dp \
  --region asia-southeast1 \
  --format="value(config.gceClusterConfig.serviceAccount)"
```
grant:

```bash
gcloud projects add-iam-policy-binding cdp-dem-project \
  --member="serviceAccount:585752501826-compute@developer.gserviceaccount.com" \
  --role="roles/bigquery.dataEditor"

gcloud projects add-iam-policy-binding cdp-dem-project \
  --member="serviceAccount:585752501826-compute@developer.gserviceaccount.com" \
  --role="roles/bigquery.jobUser"
```

chuẩn hơn:

```bash
bq update \
  --dataset \
  --add_iam_member="serviceAccount:585752501826-compute@developer.gserviceaccount.com:roles/bigquery.dataEditor" \
  cdp-dem-project:cdp_gold
```

step 7: upload job to GCP

```bash
gsutil cp jobs/silver_to_gold.py gs://cdp-dem-code/jobs/silver_to_gold.py
```


step 8: submit gold job

```bash
gcloud dataproc jobs submit pyspark \
  gs://cdp-dem-code/jobs/silver_to_gold.py \
  --region asia-southeast1 \
  --cluster cdp-demo-dp \
  -- \
  gs://cdp-dem-silver/orders \
  cdp-dem-project \
  cdp_gold \
  orders
```

check result:
```bash
bq ls cdp-dem-project:cdp_gold
```
query
```bash
bq query --use_legacy_sql=false '
SELECT * FROM `cdp-dem-project.cdp_gold.orders`
'
```

## Airflow DAG orchestrate Bronze → Silver → Gold:

```
Bronze (GCS) 
   → Spark on Dataproc (Silver)
      → Spark BigQuery (Gold)
```

•	Airflow KHÔNG chạy Spark trực tiếp
	•	Airflow chỉ submit job + monitor
	•	Tách rõ:
	•	Code Spark = jobs/
	•	Orchestration = dags/

Architecture:

```
Airflow (Composer / Local)
 ├── DataprocCreateClusterOperator (optional)
 ├── DataprocSubmitJobOperator (bronze_to_silver)
 ├── DataprocSubmitJobOperator (silver_to_gold)
 └── DataprocDeleteClusterOperator (cost saving)
```

project:

```
spark401-codespace/
├── .airflow/dags/
│   └── cdp_bronze_silver_gold.py
├── jobs/
│   ├── bronze_to_silver.py
│   └── silver_to_gold.py
├── data/
├── README.md
```

flow

```
Codespace (dev)
 └── Airflow local (test DAG logic)
       └── Submit Spark job → Dataproc (GCP)
             └── GCS / BigQuery
```

### Airflow (local) in codespace:

**Chiến lược**
|Thành phần|Vai trò|
|----------|-------|
|Codespace|Code, test, CI/CD|
|Dataproc|Spark runtime (on-demand)|
|Composer|Airflow production|
|GCS|Bronze / Silver|
|BigQuery|Gold|



* read doc at [link](./airflow/README.md) how to setup airflow in codespace

setup cloud: ADC
```bash
gcloud auth application-default login
```
|Lệnh|Dùng cho|
|----|---------|
|gcloud auth login|CLI, gsutil, gcloud|
|gcloud auth application-default login|Python / Airflow / SDK / Spark|

Airflow KHÔNG dùng credential của gcloud auth login
→ nó chỉ đọc ADC


run test
```bash
airflow dags test bronze_to_silver 2024-01-01
```

```bash
airflow dags test silver_to_gold 2024-01-01
```

check
```bash
gsutil ls gs://cdp-dem-gold/
```

List bảng trong dataset GOLD
```bash
bq ls cdp-dem-project:cdp_gold
```

Show schema bảng (ví dụ bảng orders)
```bash
bq show cdp-dem-project:cdp_gold.orders
```

Query thử dữ liệu:
```bash
bq query --use_legacy_sql=false \
'SELECT COUNT(*) FROM `cdp-dem-project.cdp_gold.orders`'
```

test submit job trực tiếp:
```bash
gcloud dataproc jobs list \
  --region asia-southeast1 \
  --cluster cdp-demo-dp
```



## Delete cluster sau khi test:

|Hành động|Chi phí|
|---------|-------|
|Cluster tồn tại|💸 tốn tiền|
|Delete cluster|❌ không tốn|
|Submit job khi cluster không tồn tại|❌ fail|

👉 Vì vậy sau khi dùng xong cần delete cluster, và khi test cần:

🔹 Khi cần chạy DAG → tạo lại

🔹 Không cần tên mới (tên cũ dùng lại OK)

check
```bash
gcloud compute instances list \
  --filter="name~'cdp-demo-dp'" \
  --format="table(name,zone,machineType,status)"
```

```bash
gcloud dataproc clusters list --region=asia-southeast1
```
xem chi tiết cluster:
```bash
gcloud dataproc clusters describe cdp-demo-dp \
  --region=asia-southeast1
```

check instances
```bash
gcloud compute instances list
```

check disks
```bash
gcloud compute disks list
```

check staticIP
```bash
gcloud compute addresses list
```

check dataproc jobs
```bash
gcloud dataproc jobs list --region=asia-southeast1
```

### tiết kiệm
delete
```bash
gcloud dataproc clusters delete $CLUSTER_NAME --region $REGION
```

hoặc cụ thể:
```bash
gcloud dataproc clusters delete cdp-demo-dp \
  --region asia-southeast1 \
  --quiet
```
kiểm tra sau khi xoá:
```bash
gcloud dataproc clusters list --region asia-southeast1
```

## Khi cần test lại

run 

```bash
export PROJECT_ID=cdp-dem-project
export REGION=asia-southeast1
export ZONE=asia-southeast1-a
export CLUSTER_NAME=cdp-demo-dp
```

create:

```bash
gcloud dataproc clusters create $CLUSTER_NAME \
  --region $REGION \
  --zone $ZONE \
  --master-machine-type e2-standard-2 \
  --worker-machine-type e2-standard-2 \
  --num-workers 2 \
  --master-boot-disk-size 100 \
  --worker-boot-disk-size 100 \
  --image-version 2.2-debian12 \
  --project $PROJECT_ID
```

Tiết kiệm hơn nên tạo disk 50GB:
```bash
export PROJECT_ID=cdp-dem-project
export REGION=asia-southeast1
export ZONE=asia-southeast1-a
export CLUSTER_NAME=cdp-demo-dp

gcloud dataproc clusters create $CLUSTER_NAME \
  --region $REGION \
  --zone $ZONE \
  --master-machine-type e2-standard-2 \
  --worker-machine-type e2-standard-2 \
  --num-workers 2 \
  --master-boot-disk-size 50 \
  --worker-boot-disk-size 50 \
  --image-version 2.2-debian12 \
  --project $PROJECT_ID
```

### check billing:
```bash
gcloud billing accounts list
```
```bash
gcloud beta billing projects describe cdp-dem-project
```


## Continue follow documents as bellow:
### AIRFLOW -> GCP, PLAN:

|Phase|Tóm tắt   |
|-----|----------|
|[Phase 1 – Environment](./docs/01_Phase_1_local_codespace.md)|Test local trên codespace|
|[Phase 2 – Data Processing](./docs/02_Phase_2_GCP_Free_Tier_Serverless.md)|Dag test local trên codespace và spark job submit GCP Serverless|
|[Phase 3 – Orchestration](./docs/03_Phase_3_Orchestration.md)|Airflow|
|[Phase 4 – Enterprise Hardening](./docs/04_Phase_4_Enterprise_Hardening.md)|IAM · CI/CD · Guardrails|
|Phase 5 – Observability|Logging · Lineage · Cost|
|Phase 6 – Production|SLA · Retry · Backfill|

0. [Setup airlow in codespace](./airflow/README.md)
1. [PHASE 1 – Local / Codespace](./docs/01_Phase_1_local_codespace.md)
2. [PHASE 2 – GCP Free Tier - DataProc Serverless](./docs/02_Phase_2_GCP_Free_Tier_Serverless.md)
3. [PHASE 3 - Airflow orchestration](./docs/03_Phase_3_Orchestration.md)
4. [Phase 4 – Enterprise Hardening](./docs/04_Phase_4_Enterprise_Hardening.md)