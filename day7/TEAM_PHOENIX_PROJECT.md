# 🔥 Team Phoenix — Customer Churn Prediction Pipeline
## Day 7 | Sigma DataTech | Pipeline Brain

> **Mission**: Build a daily AI-assisted pipeline that identifies customers at risk of churning — before they leave — using RFM analysis on transaction history. Output is written as a production-grade Gold table consumed by CRM and retention teams.

---

## 📌 Table of Contents

1. [The Business Problem](#1-the-business-problem)
2. [What the System Does — Big Picture](#2-what-the-system-does--big-picture)
3. [Data Sources](#3-data-sources)
4. [System Architecture](#4-system-architecture)
5. [Layer-by-Layer Breakdown](#5-layer-by-layer-breakdown)
   - [Bronze Layer](#bronze-layer--raw-ingest)
   - [Silver Layer](#silver-layer--clean--enrich)
   - [Gold Layer](#gold-layer--churn-prediction)
6. [Unique Concepts Applied](#6-unique-concepts-applied)
   - [What Is RFM?](#what-is-rfm)
   - [Medallion Architecture](#medallion-architecture)
   - [Idempotency](#idempotency)
   - [Partition Pruning](#partition-pruning)
7. [Business Rules — Full List](#7-business-rules--full-list)
8. [Tools & Technologies](#8-tools--technologies)
9. [Airflow DAG — Orchestration](#9-airflow-dag--orchestration)
10. [AI's Role in This Pipeline](#10-ais-role-in-this-pipeline)
11. [Output: What CRM Gets](#11-output-what-crm-gets)
12. [Validation Checklist](#12-validation-checklist)

---

## 1. The Business Problem

> **In one sentence**: Sigma DataTech loses revenue when customers stop transacting without warning — this pipeline detects the early warning signal before the customer is fully gone.

### Why Churn Matters

```
A customer who buys once a week suddenly goes quiet for 3 weeks.

Without this pipeline:     Nobody knows. CRM team finds out after the customer has left.
With this pipeline:        After 14 days of inactivity → customer is flagged as at_risk.
                           CRM gets a daily table → sends targeted offer → customer retained.
```

### Measurable Outcome
- Every day at 04:00 UTC, a fresh `churn_risk` Gold table is available
- CRM team queries it to pull **all `at_risk` customers** for that day's retention campaign
- Success metric: reduce churn rate by acting on at_risk signals within 24 hours

---

## 2. What the System Does — Big Picture

```
                        ┌─────────────────────────────────┐
                        │     DAILY TRIGGER (Airflow)     │
                        │     Every day at 02:00 UTC      │
                        └────────────────┬────────────────┘
                                         │
                    ┌────────────────────▼─────────────────────┐
                    │           INPUT: Raw CSV Files            │
                    │   transactions.csv  (~1M rows/day)        │
                    └────────────────────┬─────────────────────┘
                                         │
                    ┌────────────────────▼─────────────────────┐
                    │   BRONZE LAYER — Dump raw data as-is     │
                    │   Add metadata. Partition by date.        │
                    │   Output: Parquet files                   │
                    └────────────────────┬─────────────────────┘
                                         │
                    ┌────────────────────▼─────────────────────┐
                    │   SILVER LAYER — Clean + Filter + Enrich │
                    │   Keep only COMPLETED transactions        │
                    │   Cast types, remove nulls/negatives      │
                    │   Deduplicate on transaction_id           │
                    │   Output: Clean Parquet (COMPLETED only)  │
                    └────────────────────┬─────────────────────┘
                                         │
                    ┌────────────────────▼─────────────────────┐
                    │   GOLD LAYER — RFM + Churn Scoring       │
                    │   Calculate Recency, Frequency, Monetary  │
                    │   Flag: at_risk WHERE recency > 14 days  │
                    │   Output: churn_risk Gold table           │
                    └────────────────────┬─────────────────────┘
                                         │
                    ┌────────────────────▼─────────────────────┐
                    │         CRM / RETENTION TEAM             │
                    │   Queries churn_risk table daily         │
                    │   Sends targeted retention campaigns      │
                    └──────────────────────────────────────────┘
```

---

## 3. Data Sources

### Primary Source: `transactions.csv`
One file delivered daily by the upstream payment processing system.

| Column | Raw Type | Description | Example |
|--------|----------|-------------|---------|
| `transaction_id` | string | Unique ID per transaction | `TXN001` |
| `customer_id` | string | Unique ID per customer | `C001` |
| `merchant_id` | string | Which merchant received payment | `M001` |
| `amount` | string* | Transaction value in ₹ | `450.00` |
| `status` | string | COMPLETED / FAILED / PENDING | `COMPLETED` |
| `transaction_date` | string* | Date of transaction | `2024-01-15` |
| `payment_method` | string | UPI / CREDIT_CARD / DEBIT_CARD | `UPI` |

> ⚠️ *Raw CSV files store everything as strings — even numbers and dates. This is intentional. Type casting happens in the Silver layer.*

### How the File Arrives

```
Upstream Payment System
         │
         │  Daily CSV drop (02:00 UTC)
         ▼
S3 Bucket: s3://sigma-datatech/raw/transactions/
           └── date=2024-01-15/
               └── transactions.csv       ← today's file
```

The pipeline reads from this S3 path. If the file is missing → pipeline raises `FileNotFoundError`, sends SNS alert, and **aborts** — it does NOT write partial output.

### Reference/Dimension Source: `merchants.csv`
Small lookup file (~500 rows). Changes rarely (slowly changing dimension).

| Column | Description |
|--------|-------------|
| `merchant_id` | Matches transactions.csv |
| `merchant_name` | e.g., Swiggy, Amazon, Zomato |
| `category` | Food Delivery, E-Commerce, Travel... |
| `city` | Bengaluru, Mumbai, Gurugram... |

> **Note for churn pipeline**: Merchant data is less critical here — churn is customer-centric, not merchant-centric. However, it enriches Silver and allows future analysis like "are customers churning from specific merchant categories?"

---

## 4. System Architecture

### Full Stack View

```
┌─────────────────────────────────────────────────────────────────┐
│                        ORCHESTRATION                            │
│  Apache Airflow DAG: sigma_churn_pipeline                       │
│  Schedule: 0 2 * * *  (daily at 02:00 UTC)                      │
│  Retries: 2 | Retry delay: 5 min | SLA: 2 hours                 │
└──────────────┬─────────────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────────────┐
│                     COMPUTE LAYER                               │
│  PySpark on AWS EMR (Elastic MapReduce)                         │
│  Processes ~1M rows/day using distributed processing            │
└──────────────┬─────────────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────────────┐
│                       AI LAYER                                  │
│  Amazon Bedrock (Nova Lite / Nova Pro)                          │
│  ✦ Writes the PySpark pipeline code from our spec               │
│  ✦ Generates the Airflow DAG                                    │
│  ✦ Hardens the pipeline (adds safety patterns)                  │
│  ✦ Reviews code against 12-point checklist                      │
└──────────────┬─────────────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────────────┐
│                     STORAGE LAYER (S3)                          │
│                                                                 │
│  s3://sigma/raw/          ← Raw CSV files (input)               │
│  s3://sigma/bronze/       ← Raw Parquet, partitioned by date    │
│  s3://sigma/silver/       ← Clean Parquet, partitioned by date  │
│  s3://sigma/gold/         ← churn_risk table, partitioned by date│
└─────────────────────────────────────────────────────────────────┘
```

### Airflow Task Dependency Graph

```
[extract_bronze] ──► [transform_silver] ──► [build_gold_churn]
       │                     │                      │
   reads CSV            reads Bronze           reads Silver
   writes Parquet       writes Parquet         writes churn_risk
       │                     │                      │
   on failure:          on failure:            on failure:
   SNS alert            SNS alert              SNS alert
   ABORT                ABORT                  ABORT
```

---

## 5. Layer-by-Layer Breakdown

---

### BRONZE Layer — Raw Ingest

#### What It Does
Takes the raw CSV exactly as-is and writes it to Parquet. **No transformation. No filtering. No casting.**

#### Why This Approach?
Bronze is your **source of truth audit log**. If something goes wrong downstream, you can always replay from Bronze without re-downloading from the upstream system.

#### Input
```
s3://sigma/raw/transactions/date=2024-01-26/transactions.csv
```
Every column arrives as a **string** — even `amount` ("450.00") and `transaction_date` ("2024-01-15").

#### What Happens Inside

```python
Step 1: Read CSV with all columns as strings (schema inference OFF)
Step 2: Add 3 metadata columns:
        - ingestion_timestamp  → when this pipeline ran
        - source_file          → which CSV file was ingested
        - pipeline_run_id      → unique ID for this run (for tracing)
Step 3: Write to Parquet, partitioned by transaction_date
```

#### Output Schema (Bronze Parquet)
| Column | Type | Added by |
|--------|------|----------|
| `transaction_id` | string | source CSV |
| `customer_id` | string | source CSV |
| `merchant_id` | string | source CSV |
| `amount` | **string** | source CSV (raw, not cast yet) |
| `status` | string | source CSV |
| `transaction_date` | **string** | source CSV (raw, not cast yet) |
| `payment_method` | string | source CSV |
| `ingestion_timestamp` | string | **pipeline adds this** |
| `source_file` | string | **pipeline adds this** |
| `pipeline_run_id` | string | **pipeline adds this** |

#### Output Location
```
s3://sigma/bronze/transactions/
└── transaction_date=2024-01-26/
    └── part-00000.parquet
```

#### Quality Rule at Bronze
> None — Bronze accepts everything. Garbage in is acceptable here. Silver cleans it.

---

### SILVER Layer — Clean + Enrich

#### What It Does
Takes Bronze data and produces a **trusted, analysis-ready** dataset. This is the most complex layer.

#### Why Each Step Exists

```
┌─────────────────────────────────────────────────────────────────┐
│  STEP 1: Read Bronze (with partition pruning)                   │
│  → Only read today's partition, not 365 days of history         │
│  → Reason: Full table scan on 1M rows/day × 365 = 365M rows     │
│            Partition pruning keeps it to 1M rows.               │
└──────────────────────────────┬──────────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────────┐
│  STEP 2: Cast column types                                      │
│  amount          string → DECIMAL(18,2)                         │
│  transaction_date string → DATE                                 │
│  ingestion_timestamp string → TIMESTAMP                         │
│  → Reason: Math operations on strings fail silently.            │
│            You cannot SUM("450.00") — you need SUM(450.00).     │
└──────────────────────────────┬──────────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────────┐
│  STEP 3: Filter bad records                                     │
│  DROP WHERE transaction_id IS NULL                              │
│  DROP WHERE amount <= 0                                         │
│  KEEP ONLY WHERE status = 'COMPLETED'                           │
│  → Reason: NULL transaction_id = untraceable record.            │
│            Negative amounts = refunds/errors, not real revenue. │
│            FAILED/PENDING = customer never paid, should NOT      │
│            affect churn — a failed attempt ≠ customer activity. │
└──────────────────────────────┬──────────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────────┐
│  STEP 4: Deduplicate on transaction_id                          │
│  If same transaction_id appears twice, keep the one with the    │
│  latest ingestion_timestamp.                                    │
│  → Reason: CSV files from upstream sometimes resend yesterday's │
│            transactions (e.g., reconciliation re-runs).         │
│            Duplicate transactions would inflate spend totals.   │
└──────────────────────────────┬──────────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────────┐
│  STEP 5: Enrich with merchant dimension                         │
│  LEFT JOIN transactions ON merchant_id → get merchant_name,    │
│  category, city                                                 │
│  Add quality_flag = 'UNMATCHED' if no merchant found            │
│  → Reason: Future analysis — "are customers churning because    │
│            their favourite category (Food Delivery) is down?"   │
└──────────────────────────────┬──────────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────────┐
│  STEP 6: Quality Halt Check                                     │
│  IF null_customer_id_count / total_count > 5%                   │
│  → HALT pipeline, write failure report, DO NOT proceed to Gold  │
│  → Reason: If >5% of records have no customer_id, the churn    │
│            table will be incomplete and misleading for CRM.     │
└──────────────────────────────┬──────────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────────┐
│  STEP 7: Write Silver Parquet                                   │
│  Partition by transaction_date                                  │
│  Pattern: delete partition THEN write (idempotent)              │
└─────────────────────────────────────────────────────────────────┘
```

#### Row Count Logged at Each Step
```
[Silver] Input from Bronze:        1,000,000 rows
[Silver] After status filter:        720,000 rows  (COMPLETED only)
[Silver] After null/negative filter: 718,500 rows
[Silver] After deduplication:        715,200 rows
[Silver] Output written:             715,200 rows
```
These 4 numbers are logged to `run_metadata_{run_date}.json` and monitored by the Day 12 self-heal agent.

#### Output Schema (Silver Parquet)
| Column | Type | Source |
|--------|------|--------|
| `transaction_id` | string | Bronze |
| `customer_id` | string | Bronze |
| `merchant_id` | string | Bronze |
| `amount` | **DECIMAL(18,2)** | Cast from Bronze string |
| `status` | string | Bronze (COMPLETED only) |
| `transaction_date` | **DATE** | Cast from Bronze string |
| `payment_method` | string | Bronze |
| `merchant_name` | string | **Joined from merchants dim** |
| `category` | string | **Joined from merchants dim** |
| `city` | string | **Joined from merchants dim** |
| `quality_flag` | string | **Pipeline adds: CLEAN or UNMATCHED** |
| `ingestion_timestamp` | timestamp | Bronze |
| `pipeline_run_id` | string | Bronze |

---

### GOLD Layer — Churn Prediction

#### What It Does
Reads from Silver (last 30 days of COMPLETED transactions) and produces one row per customer with their RFM scores and churn risk label.

#### Why 30 Days Lookback?
RFM is a **historical pattern**, not a single day's snapshot. Reading only today's Silver would miss customers who haven't transacted in 2 weeks — they wouldn't appear at all. We need 30 days to compute:
- When did they **last** transact? (Recency)
- **How many times** have they transacted? (Frequency)
- **How much** have they spent? (Monetary)

#### Input
```
s3://sigma/silver/transactions/
WHERE transaction_date >= run_date - INTERVAL 30 DAYS   ← partition pruning
  AND transaction_date <= run_date
```

#### What Happens Inside

```
For each unique customer_id in the last 30 days:

  recency_days      = DATEDIFF(run_date, MAX(transaction_date))
  frequency         = COUNT(DISTINCT transaction_id)
  monetary          = SUM(amount)    ← COMPLETED only (already filtered in Silver)

  risk_status       = CASE
                        WHEN recency_days > 14 THEN 'at_risk'
                        ELSE 'active'
                      END

  generated_at      = current UTC timestamp of this pipeline run
```

#### Output Schema: `churn_risk` Gold Table
| Column | Type | Formula / Source | Description |
|--------|------|-----------------|-------------|
| `customer_id` | string | GROUP BY key | Unique customer |
| `recency_days` | integer | `DATEDIFF(run_date, MAX(transaction_date))` | Days since last purchase |
| `frequency` | integer | `COUNT(DISTINCT transaction_id)` | # of transactions in 30 days |
| `monetary` | decimal | `SUM(amount)` | Total ₹ spent in 30 days |
| `risk_status` | string | See rule below | `at_risk` or `active` |
| `last_transaction_date` | date | `MAX(transaction_date)` | When they last bought |
| `preferred_payment_method` | string | MODE(payment_method) | Most used payment type |
| `generated_at` | timestamp | pipeline runtime | When this record was created |
| `run_date` | date | pipeline parameter | Which day's run produced this |

#### Output Location
```
s3://sigma/gold/churn_risk/
└── run_date=2024-01-26/
    └── part-00000.parquet   ← one row per at-risk customer
```

#### Sample Output Rows
| customer_id | recency_days | frequency | monetary | risk_status |
|-------------|-------------|-----------|----------|-------------|
| C001 | 2 | 5 | ₹6,100 | active |
| C002 | 8 | 3 | ₹2,156 | active |
| C005 | 18 | 1 | ₹540 | **at_risk** |
| C007 | 26 | 1 | ₹145 | **at_risk** |
| C009 | 31 | 1 | ₹145 | **at_risk** |

---

## 6. Unique Concepts Applied

---

### What Is RFM?

RFM is a classic **customer analytics framework** used by every major e-commerce and fintech company. It scores customers on 3 dimensions to predict their future behaviour.

| Letter | Stands For | Our Formula | What It Tells Us |
|--------|-----------|-------------|-----------------|
| **R** | **Recency** | `DATEDIFF(run_date, MAX(transaction_date))` | How many days since last purchase. Lower = better. |
| **F** | **Frequency** | `COUNT(DISTINCT transaction_id)` | How many times they bought in 30 days. Higher = better. |
| **M** | **Monetary** | `SUM(amount)` WHERE COMPLETED | How much ₹ they spent. Higher = more valuable customer. |

#### RFM in Action — Example

```
Customer C001:
  Last transaction: 2 days ago       → Recency = 2    (very recent, LOW churn risk)
  Transactions in 30 days: 5         → Frequency = 5  (loyal buyer)
  Total spent: ₹6,100                → Monetary = HIGH (valuable customer)
  ─────────────────────────────────────────────────
  RFM Profile: Recent + Frequent + High Value = CHAMPION customer
  risk_status = 'active'

Customer C007:
  Last transaction: 26 days ago      → Recency = 26   (very stale, HIGH churn risk)
  Transactions in 30 days: 1         → Frequency = 1  (one-time buyer)
  Total spent: ₹145                  → Monetary = LOW
  ─────────────────────────────────────────────────
  RFM Profile: Stale + Rare + Low Value = AT RISK
  risk_status = 'at_risk'
```

#### Why Not Just Use Recency Alone?
Because a customer could have 0 transactions in 14 days but ₹50,000 in total spend over the last month. That's a high-value customer who took a short break — not a churner. Frequency and Monetary give CRM the **context** to decide how aggressively to target the customer.

---

### Medallion Architecture

```
BRONZE  →  SILVER  →  GOLD
  Raw       Clean      Business
  Data      Data       Aggregates
```

| Layer | Quality Level | Who Writes | Who Reads |
|-------|--------------|------------|-----------|
| Bronze | Raw, unvalidated | Pipeline (ingest) | Silver job only |
| Silver | Clean, typed, deduplicated | Pipeline (transform) | Gold job, analysts |
| Gold | Business-ready aggregates | Pipeline (aggregate) | CRM, dashboards, ML models |

**Why this matters**: If data at any layer is corrupted, you don't re-download from the upstream system. You replay from the previous layer. Bronze → re-run Silver. Silver → re-run Gold.

---

### Idempotency

> **Definition**: Running the pipeline twice for the same date produces exactly the same result. No duplicates. No data loss.

**The Problem Without Idempotency:**
```
Run 1 (Jan 26): writes 1,000 churn_risk rows for Jan 26
Pipeline crashes → Airflow retries
Run 2 (Jan 26): appends another 1,000 rows
Result: 2,000 rows for Jan 26 → CRM gets duplicate customers
```

**Our Solution — Delete-Partition-Then-Write:**
```python
# WRONG (mode='append' is never idempotent):
df.write.mode("append").parquet("s3://sigma/gold/churn_risk/")

# WRONG (mode='overwrite' wipes the ENTIRE table, not just one date):
df.write.mode("overwrite").parquet("s3://sigma/gold/churn_risk/")

# CORRECT (delete only today's partition, then write):
shutil.rmtree(f"s3://sigma/gold/churn_risk/run_date={run_date}", ignore_errors=True)
df.write.mode("overwrite").parquet(f"s3://sigma/gold/churn_risk/run_date={run_date}/")
```

---

### Partition Pruning

> **Definition**: Only read the data files you actually need, not the entire table.

**The Problem Without Pruning:**
```
Gold reads Silver for last 30 days
Silver has 365 days × 1M rows = 365M rows total
Without pruning → Spark scans ALL 365M rows
With pruning    → Spark scans only 30 days × 1M = 30M rows
                  12x faster, 12x cheaper on AWS
```

**How It Works:**
```python
# Partition pruning filter — PySpark uses the folder structure
silver_df = spark.read.parquet("s3://sigma/silver/transactions/") \
    .filter(col("transaction_date") >= run_date - timedelta(days=30)) \
    .filter(col("transaction_date") <= run_date)

# Spark only opens folders that match the date range:
#   s3://sigma/silver/transactions/transaction_date=2024-01-01/  ← scanned
#   s3://sigma/silver/transactions/transaction_date=2023-12-01/  ← SKIPPED
```

---

## 7. Business Rules — Full List

These are the exact rules the pipeline enforces. Every number has a business owner.

| # | Rule | Exact Formula | Business Owner | Impact If Violated |
|---|------|--------------|----------------|--------------------|
| BR-1 | Churn threshold | `at_risk = 'at_risk' WHERE DATEDIFF(run_date, MAX(transaction_date)) > 14` | Head of Retention (CRM) | Wrong customers targeted in campaign |
| BR-2 | Revenue calculation | `monetary = SUM(amount) WHERE status = 'COMPLETED'` | Finance | Inflated revenue if FAILED included |
| BR-3 | Null transaction filter | `DROP WHERE transaction_id IS NULL` | Data Governance | Untraceable records corrupt dedup |
| BR-4 | Negative amount filter | `DROP WHERE amount <= 0` | Finance | Refunds inflate spend, lower RFM scores |
| BR-5 | Status filter | `KEEP ONLY status = 'COMPLETED'` | Product | Failed attempts ≠ customer activity |
| BR-6 | Deduplication | `KEEP MAX(ingestion_timestamp) PER transaction_id` | Data Governance | Duplicate txns inflate frequency + monetary |
| BR-7 | Quality halt | `HALT IF null_customer_id_count / total_count > 0.05` | Data Engineering | Silent bad data reaches CRM |
| BR-8 | Idempotency | Delete partition before write | Data Engineering | Duplicate rows on retry |
| BR-9 | Lookback window | `WHERE transaction_date >= run_date - INTERVAL 30 DAYS` | Analytics | Short window misses returning customers |
| BR-10 | Error on missing file | `raise FileNotFoundError → SNS alert → ABORT` | Data Engineering | Partial Gold written for wrong date |
| BR-11 | SLA | Pipeline must complete within 2 hours of 02:00 UTC | Ops / CRM | Dashboard unavailable for morning campaign |
| BR-12 | Run date (not current date) | `run_date` passed as parameter, not `current_date()` | Data Engineering | Re-runs for past dates give wrong results |

---

### Why 14 Days? (Anil's Trap Question)

> **Question**: "Why 14 days specifically? Who in the business set that threshold?"

**Answer**: The 14-day threshold was set by the **Head of Customer Retention at Sigma DataTech**, not the data team. It comes from their internal churn study:
- Customers inactive for **< 7 days** → normal purchase cycle
- Customers inactive for **7–14 days** → early warning, monitor
- Customers inactive for **> 14 days** → statistically 3x more likely to never return

The data team's job is to implement this threshold precisely — not to decide it. The number lives in the pipeline config, not hardcoded in logic, so it can be updated without code changes.

---

## 8. Tools & Technologies

### PySpark
| What | Why |
|------|-----|
| Distributed data processing | 1M rows/day — needs parallel computation, not single-machine Python pandas |
| Reads/writes Parquet natively | Columnar format, partition-aware, 10x faster than CSV for analytics |
| Runs on AWS EMR | Elastic — scales up for big days, scales down to save cost |

**Input**: Bronze Parquet files on S3
**Output**: Silver and Gold Parquet files on S3

---

### Amazon Bedrock (Nova Lite + Nova Pro)
| What | Why |
|------|-----|
| Nova Lite | Scaffolding tasks — pipeline code, DAG structure (fast + cheap) |
| Nova Pro | Reasoning tasks — hardening code, code review (slower + stronger) |

**What AI does in this project:**
```
Our Pipeline Spec (plain English)
         │
         ▼ Nova Lite (Module 1)
Generated PySpark pipeline code
         │
         ▼ Nova Lite (Module 2)
Generated Airflow DAG
         │
         ▼ Nova Pro (Module 3)
Hardened pipeline (error handling, idempotency, logging added)
         │
         ▼ Nova Pro (Module 5)
12-point code review with PASS/FAIL/WARN per checkpoint
```

---

### Apache Airflow
| What | Why |
|------|-----|
| Workflow orchestration | Ensures Bronze runs before Silver, Silver before Gold — in the right order |
| Retry logic | If Bronze fails at 02:00 UTC, Airflow retries at 02:05 and 02:10 automatically |
| SLA monitoring | Alerts ops team if pipeline hasn't finished by 04:00 UTC (2-hour SLA) |
| Failure callbacks | On any task failure → sends alert to data-engineering Slack channel |

**Input**: Pipeline schedule + task definitions
**Output**: Triggered PySpark jobs in the correct order

---

### AWS S3
| Layer | S3 Path |
|-------|---------|
| Raw CSV input | `s3://sigma/raw/transactions/date={date}/` |
| Bronze output | `s3://sigma/bronze/transactions/transaction_date={date}/` |
| Silver output | `s3://sigma/silver/transactions/transaction_date={date}/` |
| Gold output | `s3://sigma/gold/churn_risk/run_date={date}/` |
| Run metadata | `s3://sigma/metadata/run_metadata_{date}.json` |

---

## 9. Airflow DAG — Orchestration

```
DAG ID:   sigma_churn_pipeline
Schedule: 0 2 * * *   (every day at 02:00 UTC)
Retries:  2 per task   (retry after 5 minutes)
SLA:      120 minutes  (must finish by 04:00 UTC)
```

### Task Flow

```
Task 1: extract_bronze
├─ Reads: s3://sigma/raw/transactions/date={run_date}/transactions.csv
├─ Writes: s3://sigma/bronze/transactions/transaction_date={run_date}/
└─ On failure: SNS alert → ABORT (task 2 never runs)
        │
        ▼ (only if extract_bronze succeeds)
Task 2: transform_silver
├─ Reads: s3://sigma/bronze/transactions/transaction_date={run_date}/
├─ Writes: s3://sigma/silver/transactions/transaction_date={run_date}/
└─ On failure: SNS alert → ABORT (task 3 never runs)
        │
        ▼ (only if transform_silver succeeds)
Task 3: build_gold_churn
├─ Reads: s3://sigma/silver/transactions/ (last 30 days)
├─ Writes: s3://sigma/gold/churn_risk/run_date={run_date}/
├─ Writes: s3://sigma/metadata/run_metadata_{run_date}.json
└─ On failure: SNS alert → ABORT
```

---

## 10. AI's Role in This Pipeline

> **The Rule**: AI generates the scaffold in 60 seconds. Humans spend 30 minutes reviewing it. That's still 10× faster than writing from scratch.

### What AI Gets RIGHT

| Module | What AI Nails |
|--------|--------------|
| M1 — Code Gen | PySpark imports, SparkSession setup, function structure per stage, medallion pattern |
| M2 — DAG Gen | DAG structure, `>>` dependencies, default_args, retry config |
| M3 — Hardening | try/except placement, run_metadata dict structure, row count logging checkpoints |
| M5 — Review | Idempotency detection, missing NULL checks, hardcoded paths, wildcard imports |

### What AI Gets WRONG (always check these)

| Module | What to Verify Manually |
|--------|------------------------|
| M1 | Broadcast hint syntax, hardcoded S3 paths, mode('append') instead of delete-partition-then-write |
| M2 | SLA values (AI picks a number — does your ops team agree?), Operator choice (PythonOperator vs EmrAddStepsOperator) |
| M3 | Idempotency implementation — AI may use `mode('overwrite')` which overwrites whole table, not one partition |
| M5 | Business rule correctness — AI doesn't know whether YOUR 14-day threshold is right |

---

## 11. Output: What CRM Gets

### Daily `churn_risk` Table
CRM analysts query this table every morning to build the day's retention campaign list.

```sql
-- CRM's daily query
SELECT customer_id, recency_days, frequency, monetary, preferred_payment_method
FROM churn_risk
WHERE run_date = CURRENT_DATE
  AND risk_status = 'at_risk'
ORDER BY recency_days DESC;
```

### Sample Output
```
customer_id | recency_days | frequency | monetary  | risk_status | preferred_payment_method
─────────────────────────────────────────────────────────────────────────────────────
C009        | 31           | 1         | ₹145.00   | at_risk     | DEBIT_CARD
C007        | 26           | 1         | ₹145.00   | at_risk     | DEBIT_CARD
C005        | 18           | 1         | ₹540.00   | at_risk     | UPI
C001        | 2            | 5         | ₹6,100.00 | active      | CREDIT_CARD
C002        | 8            | 3         | ₹2,156.00 | active      | UPI
```

**CRM Action**: C009, C007, C005 get a targeted "We miss you" offer via their preferred payment method channel.

---

## 12. Validation Checklist

Run this before committing:

```bash
cd day7
python tests/validate_day7.py
```

### What the Validator Checks

| Module | File | Minimum Requirement |
|--------|------|---------------------|
| M0 | `lab/my_pipeline_spec.txt` | Exists, > 100 bytes, all 6 sections filled |
| M1 | `pipeline_brain/generated_pipeline.py` | Exists, > 500 bytes, contains PySpark |
| M1 | `pipeline_brain/generation_report.json` | Valid JSON, has `generated_at` |
| M2 | `pipeline_brain/sigma_dag.py` | Exists, > 200 bytes, contains DAG |
| M2 | `pipeline_brain/dag_report.json` | Valid JSON, has `tasks_found` |
| M3 | `pipeline_brain/hardened_pipeline.py` | Exists, > 500 bytes |
| M3 | `pipeline_brain/hardening_report.json` | Valid JSON, `improvements_added` list present, Nova Pro used |
| M5 | `pipeline_brain/code_review.json` | Valid JSON, has `summary.merge_recommendation` |
| Bonus | `pipeline_brain/fixed_pipeline.py` | Fix ≥2 FAIL items from code review |
| Bonus | `pipeline_brain/my_review_notes.txt` | Document your changes |
| Stretch | `pipeline_brain/schema_drift_report.json` | Valid JSON (skip if not run) |

### Push When All Core Tests Are Green

```bash
git add .
git commit -m "Day 7 done — Team Phoenix churn pipeline"
git push
```

---

## Summary Card (for cold-call defence)

```
┌─────────────────────────────────────────────────────────────────┐
│  TEAM PHOENIX — Quick Reference                                 │
├─────────────────────────────────────────────────────────────────┤
│  Scenario    : Team 1 — Customer Churn Prediction Feed          │
│  Gold Table  : churn_risk                                       │
│  Key Rule    : at_risk WHERE DATEDIFF(run_date, MAX(txn_date))  │
│                > 14 (set by Head of Retention, not data team)   │
│  Status Filter: COMPLETED only — failed ≠ customer activity     │
│  Lookback    : 30 days for RFM, not just today                  │
│  Quality Halt: > 5% null customer_id → ABORT, no partial Gold   │
│  Idempotency : Delete partition THEN write (not mode=append)    │
│  Error Rule  : FileNotFoundError → SNS alert → ABORT            │
│  Why 14 days?: Business decision from CRM retention study       │
└─────────────────────────────────────────────────────────────────┘
```
