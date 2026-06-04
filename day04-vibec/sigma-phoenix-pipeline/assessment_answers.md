
---

### Q1. Glue job fails with `InvalidInputException` at job creation — most likely cause and fix?

**Cause:** Using `GlueVersion="3.0"` for a **Python Shell** job. GlueVersion 3.0 is **Spark-only** — passing it when `Command.Name = "pythonshell"` causes Glue to immediately reject the job creation call with `InvalidInputException`.

**Exact Fix (from your `app.py`, line 359):**
```python
# WRONG:
GlueVersion="3.0"

# CORRECT (as implemented in your app.py):
GlueVersion="1.0"   # Only version supported for Python Shell jobs
```
Your `app.py` already has this right (`GlueVersion="1.0"` at line 359). The `docs.md` explicitly calls this out as Bug #1.

---

### Q2. Quality report shows `negative_amounts: 0` despite negative values in data — where to look and what fix?

**Where to look first — `etl.py` lines 50 and 60, in this exact order:**

```python
# Line 50 — COUNTING happens BEFORE fixing:
negative_amounts = int((df['amount'] < 0).sum())   # ✅ counted correctly on raw df

# Line 60 — FIXING (abs) happens AFTER counting:
df_cleaned['amount'] = df_cleaned['amount'].abs()  # ✅ fix is after count
```

In **this codebase the logic is actually correct** — the count is taken on the raw `df` before `abs()` is applied. If your report shows `0`, the bug is **not in the ETL code** but one of these:

1. **The raw CSV uploaded to S3 has no negatives** — the file `orders_day3.csv` wasn't the one uploaded (wrong day selected).
2. **The `amount` column has a different name or type** (read as string → comparison `< 0` returns all `False`). Fix: `pd.to_numeric(df['amount'], errors='coerce')` before counting.
3. **Looking at a stale quality report** — S3 returned a cached old report from a previous run.

**Fix to apply in `etl.py`:**
```python
# Add this before counting to handle string-typed amounts:
df['amount'] = pd.to_numeric(df['amount'], errors='coerce')
negative_amounts = int((df['amount'] < 0).sum())
```

---

### Q3. Why does the guide say "never skip with if not exists" for Glue job creation, and what is the correct approach?

**Why not `if not exists`:** If a job with **wrong configuration** already exists (e.g., wrong `GlueVersion`, wrong `ScriptLocation`, wrong `MaxCapacity`), silently skipping creation means the **stale bad config persists**. Every subsequent `start_job_run` will use the old broken configuration — it will keep failing with no obvious reason why.

**Correct approach (from `app.py` lines 347–365 and `docs.md`):**
```python
# Always delete first, then recreate — no exceptions:
try:
    glue_client.delete_job(JobName=GLUE_JOB)  # safe — ignores if already deleted
except Exception:
    pass
glue_client.create_job(Name=GLUE_JOB, ...)   # now guaranteed fresh config
```
This ensures **idempotent deployment** — Tab 1 can be re-run safely at any time and will always deploy the correct, current configuration.

---

### Q4. Tab 3 quick-question button clears text input and results disappear — why and the session state pattern fix?

**Why it happens:** In Streamlit, every user interaction (button click) triggers a **full page rerun**. If a button handler directly writes to the `st.text_input`'s `key` *after* the widget has already been rendered in that run, Streamlit raises a `StreamlitAPIException`. Without a stable `key=` on the text_input, its value resets to empty on every rerun. Results stored as local variables are also lost.

**Session State Pattern Fix (exactly as in `app.py` lines 670–684):**
```python
# ① STAGE: button click sets a temporary key (NOT the widget key directly)
if qq_cols[i].button(btn_label, key=f"qq_{i}"):
    st.session_state["_qq_label"] = btn_label
    st.rerun()   # ← trigger a fresh rerun

# ② INJECT: At the TOP of the tab, BEFORE the widget renders, read & apply the staged value
if "_qq_label" in st.session_state:
    lbl = st.session_state.pop("_qq_label")   # consume it (pop removes it)
    st.session_state["nl_question_input"] = QUICK_QUESTIONS[lbl][0]  # inject into widget key
    st.session_state["generated_sql"] = QUICK_QUESTIONS[lbl][1]

# ③ PERSIST: Always give text_input a key= so it survives reruns
user_question = st.text_input("Ask a question...", key="nl_question_input")
```
Results are stored in `st.session_state["query_result_df"]` so they survive reruns without re-querying Athena.

---

### Q5. Athena query returns `2.94E8` in dashboard — what SQL change and where to enforce it?

**The problem:** Athena returns `DOUBLE`/`FLOAT` aggregations as strings with scientific notation (e.g. `"2.94E8"`) when using plain `SUM(amount)`.

**SQL fix — in the Bedrock prompt (instruction to the LLM) AND in your hardcoded queries:**
```sql
-- WRONG:
SELECT date, SUM(amount) FROM sigma_phoenix_orders GROUP BY date

-- CORRECT:
SELECT date, CAST(ROUND(SUM(amount)) AS BIGINT) AS daily_revenue
FROM sigma_phoenix_db.sigma_phoenix_orders GROUP BY date
```

**Enforce in two places:**
1. **In the Bedrock prompt** (Tab 3, `app.py` line 715) — include the rule: *"Always wrap SUM/AVG of `amount` in `CAST(ROUND(...) AS BIGINT)`"* so the LLM generates safe SQL.
2. **In post-processing display** (`format_dataframe_display()`, `app.py` lines 271–290) — use `float()` before formatting, which handles any remaining scientific notation strings:
```python
return f"₹{int(round(float(clean_val))):,}"  # float() converts '2.94E8' safely
```

---

### Q6. After Tab 1 deploy, running Tab 3 gives "table not found" for `sigma_phoenix_orders` — what's the missing step?

**Missing step: Tab 2 (Daily Load) has never been run.**

Here's the dependency chain:
```
Tab 1 (Deploy Pipeline)
  └── Creates the Athena TABLE DEFINITION (schema + S3 location)
      BUT → no processed CSV files exist yet in S3 (processed/orders/)

Tab 2 (Daily Load) — MUST run first
  └── Uploads orders CSV → S3 raw zone
  └── Triggers Glue ETL → writes processed CSV to processed/orders/date=.../
  └── Runs MSCK REPAIR TABLE → registers the new partition in Athena

Tab 3 (Ask Your Data)
  └── NOW Athena can find sigma_phoenix_orders (table + partition + data all exist)
```

Tab 1 only creates the **empty table definition** pointing at `s3://sigma-phoenix-bucket/processed/orders/`. Without at least one ETL run (Tab 2) writing actual data there and `MSCK REPAIR TABLE` registering the partition, Athena has nothing to query → "table not found" or "no partitions found."

---

### Q7. Two teams use the same bucket name `sigma-bucket` — what goes wrong and how does naming prevent it?

**What goes wrong:** S3 bucket names are **globally unique across all AWS accounts worldwide**. If Team A already created `sigma-bucket`, Team B's `create_bucket` call will get a `BucketAlreadyExists` error (or worse — silently succeed if they're in the same account, but they'll share data). Both teams' raw CSVs, processed files, and quality reports would **overwrite each other** in the same bucket paths, corrupting results.

**How the naming convention prevents it** (from `docs.md` and `app.py` line 219):
```
sigma-{teamname}-bucket-{account_id}

phoenix  → sigma-phoenix-bucket-431294761477
matrix   → sigma-matrix-bucket-...
nexus    → sigma-nexus-bucket-...
```
Each team's bucket name embeds their **unique team name** (and optionally account ID). This guarantees global uniqueness — no two teams can accidentally share an S3 bucket, Glue job, Athena DB, or table, even if running in the same AWS account.

---

### Q8. Tab 1 shows ✅ but Tab 2 fails every run — `from awsglue.context import GlueContext` at top of `etl.py` — what's wrong?

**What's wrong:** The job is a **Python Shell** job (`Command.Name = "pythonshell"`), not a Spark/PySpark job. The `awsglue` library (including `GlueContext`, `DynamicFrame`, `SparkContext`) is **only available in Glue Spark/PySpark jobs**. Importing it in a Python Shell job causes an `ImportError` at runtime — the job immediately fails.

Tab 1 succeeds because it only calls `glue_client.create_job()` — it doesn't *execute* the script. Tab 2 triggers `start_job_run()`, which actually runs `etl.py` on Glue infrastructure, where `awsglue` doesn't exist in Python Shell mode.

**Allowed imports for Python Shell (exactly as in `etl.py` lines 1–8):**
```python
import sys, json, io, logging
from datetime import datetime
import argparse
import boto3        # ✅ allowed
import pandas as pd # ✅ allowed via --additional-python-modules
# NO awsglue.* imports — Python Shell only!
```

---

### Q9. Schema was updated and Tab 1 re-ran with `CREATE EXTERNAL TABLE IF NOT EXISTS`, but Athena still queries old schema — what should the approach be?

**The problem with `IF NOT EXISTS`:** If the table already exists, `CREATE EXTERNAL TABLE IF NOT EXISTS` is a **no-op** — Athena silently skips creation and keeps the old schema. Your schema update is never applied.

**What the guide's correct approach should be** (and what `app.py` already does for customers/products tables — lines 411, 436):
```sql
-- Step 1: Remove the old definition
DROP TABLE IF EXISTS sigma_phoenix_db.sigma_phoenix_customers;

-- Step 2: Create fresh with new schema
CREATE EXTERNAL TABLE sigma_phoenix_db.sigma_phoenix_customers (
    customer_id STRING,
    name STRING,
    ...  -- new columns here
) ...;
```

For the **orders table** (which has partitions), additionally run:
```sql
MSCK REPAIR TABLE sigma_phoenix_db.sigma_phoenix_orders;
```
after recreation to re-register all partitions. This is the **idempotent deploy pattern**: Drop → Create → Repair. It's the same reason the Glue job does delete-then-create.

---

### Q10. `null_customer_ids: 0` in quality metrics but the defect exists in raw file — three places where the count could be silently lost

Walk through the pipeline:

**1️⃣ Data Generation (`generate_data.py` → `orders_day3.csv`)**
- The defect may not have been correctly planted — if `customer_id` is set to an **empty string `""`** instead of a true `NaN`/`NULL`, then `df['customer_id'].isna()` in pandas returns `False` for empty strings.
- **Silent loss:** `isna()` only catches `NaN`/`None`, not `""`. Fix: `df['customer_id'].replace("", pd.NA).isna().sum()`.

**2️⃣ S3 Upload (`app.py` Tab 2, lines 481–488)**
- The wrong day's file could have been uploaded — e.g., `orders_day1.csv` (clean data) instead of `orders_day3.csv`.
- If the S3 key `raw/orders/date=2026-05-03/orders.csv` already had clean data from a previous run, uploading an identical clean file again means the Glue ETL never sees the defect-containing file.
- **Silent loss:** No upload validation (row count, checksum) — the UI just shows "✅ CSV uploaded."

**3️⃣ Glue Processing (`etl.py` line 49)**
- `pandas.read_csv()` by default parses blank CSV cells as `NaN` — but if the CSV uses a literal string `"NULL"` or `"null"` for missing values, those won't be caught by `.isna()` unless `na_values=["NULL", "null", ""]` is specified.
- **Silent loss:**
```python
# Could miss string "NULL":
null_customer_ids = int(df['customer_id'].isna().sum())  # only catches NaN

# Fix:
df['customer_id'] = df['customer_id'].replace(["NULL", "null", ""], pd.NA)
null_customer_ids = int(df['customer_id'].isna().sum())
```

---