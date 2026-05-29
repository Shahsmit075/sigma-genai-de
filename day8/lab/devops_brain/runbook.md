# Pipeline Overview

<<<<<<< HEAD
This pipeline ingests transaction data, transforms it, and loads it into bronze, silver, and gold tables. It runs to ensure data is available for downstream analytics and reporting. If it stops, critical business metrics and reports will be unavailable.

# Pipeline Steps

1. Connect to the DuckDB database using `get_connection()`.
2. Set up required tables using `setup_tables()`.
3. Load merchant data into the `merchants` table using `load_merchants()`.
4. Load all transactions into the `bronze_transactions` table using `load_bronze()`.
5. Transform bronze transactions to silver using `transform_bronze_to_silver()`.
6. Load transformed data into the `silver_transactions` table using `load_silver()`.
7. Compute merchant performance metrics using `compute_merchant_performance()`.
8. Compute daily summary metrics using `compute_daily_summary()`.
9. Load merchant performance and daily summary into gold tables using `load_gold()`.

# Schedule / Trigger

This pipeline runs every night at 2 AM using a cron job.

# Failure Modes

1. **DuckDB Connection Failure**
   - **Root Cause:** Database is down or inaccessible.
   - **Symptom:** `get_connection()` raises an exception.
2. **Table Creation Failure**
   - **Root Cause:** Syntax error in SQL or database constraints.
   - **Symptom:** `setup_tables()` raises an exception.
3. **Merchant Data Load Failure**
   - **Root Cause:** Corrupt or missing merchant data.
   - **Symptom:** `load_merchants()` raises an exception.
4. **Bronze Table Load Failure**
   - **Root Cause:** Invalid transaction data or database constraints.
   - **Symptom:** `load_bronze()` raises an exception.
5. **Silver Table Transformation Failure**
   - **Root Cause:** Invalid or missing merchant mappings.
   - **Symptom:** `transform_bronze_to_silver()` raises an exception.

# Recovery Actions

1. **DuckDB Connection Failure**
   - Check database server status.
   - Restart the database if necessary.
   - Retry the pipeline.
2. **Table Creation Failure**
   - Review SQL syntax and constraints.
   - Correct any errors and rerun `setup_tables()`.
3. **Merchant Data Load Failure**
   - Verify merchant data integrity.
   - Correct any issues and rerun `load_merchants()`.
4. **Bronze Table Load Failure**
   - Validate transaction data.
   - Correct any issues and rerun `load_bronze()`.
5. **Silver Table Transformation Failure**
   - Check merchant mappings.
   - Correct any issues and rerun `transform_bronze_to_silver()`.

# Known Bugs

- Hardcoded AWS credentials in the code.
- Lack of null handling in `transform_bronze_to_silver()`.
- Inefficient set operations in `compute_daily_summary()`.

# Escalation Contacts
=======
This pipeline ingests transaction data, transforms it into a cleaned and enriched format, and computes merchant performance and daily summary metrics. It runs to ensure data is up-to-date for downstream analytics and reporting. If it stops, critical business metrics and reports will be outdated.

## Pipeline Steps

1. Connect to DuckDB database using `get_connection()`.
2. Set up required tables using `setup_tables()`.
3. Load merchants data using `load_merchants()`.
4. Load raw transactions into the bronze table using `load_bronze()`.
5. Transform bronze transactions to silver using `transform_bronze_to_silver()`.
6. Load transformed transactions into the silver table using `load_silver()`.
7. Compute merchant performance metrics using `compute_merchant_performance()`.
8. Compute daily summary metrics using `compute_daily_summary()`.
9. Load computed metrics into gold tables using `load_gold()`.

## Schedule / Trigger

This pipeline runs every hour, triggered by a cron job.

## Failure Modes

1. **Database Connection Failure**
   - **Root Cause:** DuckDB service is down.
   - **Symptom:** `get_connection()` raises an exception.
2. **Table Creation Failure**
   - **Root Cause:** Syntax error in SQL.
   - **Symptom:** `setup_tables()` raises an exception.
3. **Merchant Data Load Failure**
   - **Root Cause:** Corrupted merchant data.
   - **Symptom:** `load_merchants()` raises an exception.
4. **Bronze Table Load Failure**
   - **Root Cause:** Malformed transaction data.
   - **Symptom:** `load_bronze()` raises an exception.
5. **Silver Table Transformation Failure**
   - **Root Cause:** Missing merchant mapping.
   - **Symptom:** `transform_bronze_to_silver()` raises an exception.

## Recovery Actions

1. **Database Connection Failure**
   - Check DuckDB service status.
   - Restart DuckDB service if down.
   - Retry pipeline.
2. **Table Creation Failure**
   - Review SQL syntax in `setup_tables()`.
   - Fix SQL errors.
   - Retry pipeline.
3. **Merchant Data Load Failure**
   - Validate merchant data integrity.
   - Correct any data issues.
   - Retry pipeline.
4. **Bronze Table Load Failure**
   - Inspect transaction data for errors.
   - Correct malformed records.
   - Retry pipeline.
5. **Silver Table Transformation Failure**
   - Ensure all merchants are mapped.
   - Add missing merchant mappings.
   - Retry pipeline.

## Known Bugs

- Hardcoded AWS credentials in the code.
- Lack of null handling in `transform_bronze_to_silver()`.

## Escalation Contacts
>>>>>>> 83d5fc253a8457c3903da527641897b01c810c15

1. **On-call DE:** Priya Nair (priya.nair@sigmadatatech.in, +91-98400-11111)
2. **Tech Lead:** Arjun Mehta (arjun.mehta@sigmadatatech.in)
3. **Platform Manager:** Kavya Reddy (kavya.reddy@sigmadatatech.in)

<<<<<<< HEAD
# Data Quality Checks

- Verify the count of records in `bronze_transactions`, `silver_transactions`, `gold_merchant_performance`, and `gold_daily_summary`.
- Ensure `quality_flag` is correctly set in `silver_transactions`.
- Check for any `NULL` values in critical fields.
- Validate merchant performance and daily summary metrics against expected values.
=======
## Data Quality Checks

- Verify the number of records in `silver_transactions` matches expected count.
- Check `gold_merchant_performance` for accurate merchant metrics.
- Ensure `gold_daily_summary` reflects current date's data.
>>>>>>> 83d5fc253a8457c3903da527641897b01c810c15
