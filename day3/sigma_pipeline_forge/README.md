# ⚡ Sigma DataTech Intelligence Pipeline - PART 1
**Day 3 Lab — GenAI for Data Engineering**

Real AWS pipeline (S3 → Glue → Athena) with AI assistance via AWS Bedrock.

# ⚡ If you have to do this manually
 
 (Without the app, manually you will do the following):-

1. AWS Console → S3 — create bucket, create all folder prefixes manually
2. Upload CSVs — drag/drop each day's file to correct S3 path
3. IAM Console — create SigmaGlueServiceRole, attach policies manually
4. Write Glue ETL script — code the PySpark/Python validation + transform logic yourself
5. Glue Console — create job, configure settings, upload script
6. Run Glue job — trigger manually, watch CloudWatch logs
7. Athena Console — write CREATE DATABASE DDL, run it
8. Athena Console — write CREATE EXTERNAL TABLE DDL, run it
9. Athena Console — run MSCK REPAIR TABLE after each load
10. Athena Console — write SQL queries manually for every business question
11. Excel/Python — manually analyse quality issues in the data
12. Word/Confluence — write data quality report manually

Our app does all 12 in 4 button clicks. 
---

## Pre-requisites (do this before class)

1. AWS account with $200 credits — **us-east-1 region**
3. Python 3.10+ installed
4. AWS credentials configured (`aws configure` or `.env` file) - your personal account with Nova Lite enabled - IMPORTANT (ELSE use trainer account)


---

## Setup (one time)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Generate fictional data
python data/generate_data.py

# 3. Copy and fill credentials
cp .env.example .env

# 4. Run the app
streamlit run app.py
```

---

## How to use

| Tab | What you do |
|-----|-------------|
| 🔧 Setup Pipeline | Click once — AI writes Glue script, deploys job, creates Athena tables |
| 📦 Daily Load | Load Day 1 through Day 5 — watch Glue run and AI catch bugs |
| 🔍 Ask Your Data | Type a business question → Bedrock → Athena → answer |
| 📊 Pipeline Health | Revenue trends + AI health summary across all loaded days |

---

## The Day 3 challenge

**Day 3 data is deliberately broken.** Three issues are planted:
- 10 orders with negative amounts (refund misposting)
- 5 duplicate order_ids (retry without idempotency)
- 3 null customer_ids (guest checkout failure)

Load Day 3 and see if the pipeline + AI catches all of them.

---

## AWS cost estimate

| Service | Est. cost per student per day |
|---------|-------------------------------|
| Glue Python Shell (0.0625 DPU × 5 jobs × ~30s each) | ~$0.10 |
| S3 (< 10 MB total) | < $0.01 |
| Athena (< 1 MB scanned) | < $0.01 |
| Bedrock Claude 3.5 Haiku | ~$0.005 |
| **Total** | **~$0.12** |

Well within the $200 credit limit.

FILE STRUCTURE

sigma_pipeline_forge/
├── app.py                  ← Streamlit app (4 tabs, dark theme, Smart TV ready)
├── bedrock_client.py       ← Streaming, cost tracking, health check
├── glue_manager.py         ← Auto-creates IAM role, deploys job, polls status
├── s3_manager.py           ← Bucket creation, uploads, reads
├── athena_client.py        ← DDL setup, query execution, results as DataFrame
├── prompt_builder.py       ← All 5 Bedrock prompts, centralised
├── glue_scripts/
│   └── sigma_etl.py        ← Validated Glue Python Shell script (the one actually deployed)
├── data/
│   ├── generate_data.py    ← Run once to get all CSVs
│   ├── customers.csv, products.csv
│   └── orders_day1–5.csv   ← Day 3 has the planted bugs
└── tests/                  ← 54 tests, all passing ✅


S3 STRUCTURE

sigma-datatech-ak/
├── raw/
│   ├── orders/
│   │   ├── date=2024-01-15/orders.csv    ← Day 1 upload
│   │   ├── date=2024-01-16/orders.csv    ← Day 2 upload
│   │   ├── date=2024-01-17/orders.csv    ← Day 3 (buggy data)
│   │   ├── date=2024-01-18/orders.csv    ← Day 4 upload
│   │   └── date=2024-01-19/orders.csv    ← Day 5 upload
│   ├── customers/customers.csv           ← one-time reference
│   └── products/products.csv             ← one-time reference
│
├── processed/
│   ├── orders/
│   │   ├── date=2024-01-15/orders.csv    ← Glue cleaned output
│   │   └── ...
│   ├── customers/customers.csv
│   └── products/products.csv
│
├── reports/
│   ├── quality_report_orders_2024-01-15.json
│   ├── quality_report_orders_2024-01-16.json
│   └── quality_report_orders_2024-01-17.json  ← AI catches the Day 3 bugs here
│
├── glue-scripts/
│   └── sigma_etl.py                      ← deployed by Setup tab
│
├── temp/                                 ← Glue temp files
└── athena-results/                       ← Athena query output