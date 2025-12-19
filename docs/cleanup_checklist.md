# 🧹 CLEANUP CHECKLIST

## 1️⃣ Xoá Dataproc Cluster

```bash
gcloud dataproc clusters delete cdp-demo \
  --region asia-southeast1 \
  --project cdp-dem-project
```
>📌 Khi nào cần test lại → tạo lại trong 3–5 phút.

## 2️⃣ Airflow Local (Codespace)

**KHÔNG cần xoá gì thêm:**
*	.airflow/ giữ lại
*	DAG giữ lại
*	Chỉ là dev environment

## 3️⃣ Cloud Composer:

Check

```bash
gcloud composer environments list \
  --locations asia-southeast1
```


### TEST xong cần:

```bash
# 1. Xoá Dataproc cluster
gcloud dataproc clusters delete cdp-demo \
  --region asia-southeast1 \
  --project cdp-dem-project

# 2. (Optional) Xoá Composer
gcloud composer environments delete cdp-airflow \
  --location asia-southeast1 \
  --project cdp-dem-project
```

### Check khi start lại: 3.1 Dataproc (Cluster & Serverless)

```bash
# Cluster (stateful)
gcloud dataproc clusters list \
  --region asia-southeast1 \
  --project cdp-dem-project

# Batch serverless
gcloud dataproc batches list \
  --region asia-southeast1 \
  --project cdp-dem-project
```
### Check khi start lại: 3.2 Cloud Composer (RẤT QUAN TRỌNG – tốn tiền nhất)

```bash
gcloud composer environments list \
  --locations asia-southeast1 \
  --project cdp-dem-project
```

### Check khi start lại: 3.3 Compute Engine (VM, disk, IP)

```bash
gcloud compute instances list --project cdp-dem-project
gcloud compute disks list --project cdp-dem-project
gcloud compute addresses list --project cdp-dem-project
```



xoá disk

```bash
gcloud compute disks delete pvc-6620ac92-40a7-42b9-8450-c35644822911 \
  --zone asia-southeast1-b \
  --project cdp-dem-project \
  --quiet

gcloud compute disks delete pvc-9543797f-11a3-4c6e-9927-75ccd7d82bf6 \
  --zone asia-southeast1-b \
  --project cdp-dem-project \
  --quiet
```