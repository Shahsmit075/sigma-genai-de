# dbt Scaffold Review Report
**Day 6 · Module 4 · Sigma Intelligence Platform**

We have completed the code review of the AI-generated dbt project scaffold inside `sigma_dbt/`. Below is the detailed assessment of each checklist item, the issues found, and the steps to fix them.

---

## 📊 Review Checklist

| Checklist Item | Status | Key Findings |
| :--- | :---: | :--- |
| **`ref()` calls point to real model names?** | ❌ **FAILED** | • `mart_merchant_performance.sql` references `ref('stg_fact_transactions')`, but the staging file is named `stg_transactions.sql` (so it must be `ref('stg_transactions')`).<br>• It also references `ref('dim_merchant')`, but there is no such dbt model (it is a raw source table, or needs a staging model `stg_dim_merchant`). |
| **`source()` has correct database.schema?** | ❌ **FAILED** | • The generated source configurations point to `sigma_analytics` as a source name, but do not specify the correct database (`SIGMA_DE`) and schema (`PUBLIC`).<br>• The syntax in `staging/schema.yml` is invalid (models/sources are declared directly under the root key instead of nesting under `sources:` or `models:`). |
| **Revenue filters on `STATUS='COMPLETED'`?** | ❌ **FAILED** | • **Casing Bug**: `stg_transactions.sql` applies `LOWER(status)` which transforms the status values to lowercase (`completed`, `failed`, `pending`).<br>• However, `mart_merchant_performance.sql` filters using uppercase values: `WHERE status IN ('COMPLETED', 'FAILED')` and `CASE WHEN status = 'COMPLETED'`. This mismatch will result in **zero revenue** being calculated! |
| **Tests include `not_null`, `unique`, `accepted_values`?** | ❌ **FAILED** | • The `schema.yml` files are syntactically invalid, preventing dbt from compiling.<br>• They use non-existent test definitions like `generic_test` and `failed_status` rather than standard dbt tests. |
| **One test deliberately catches bad data?** | ❌ **FAILED** | • The test intended to fail on `status = 'CANCELLED'` is implemented via a nonexistent custom test macro `failed_status` instead of using a standard `accepted_values` test. |

---

## 🔍 Detailed Analysis of Issues

### 1. File Structure & Inline Content Leakage
* **Issue**: The generator script outputted both SQL and YAML in `stg_transactions.sql` and `mart_merchant_performance.sql`. 
* **Impact**: dbt will fail to compile the SQL files because they contain raw markdown blocks (e.g. ` ```yaml `) and YAML configurations at the bottom.
* **Fix**: Separate the SQL code and place the YAML schema configurations exclusively in `schema.yml` files.

### 2. Casing Discrepancies
* **Issue**: The staging model (`stg_transactions.sql`) converts status and payment methods to lowercase:
  ```sql
  LOWER(status) AS status
  LOWER(payment_method) AS payment_method
  ```
  But the marts model (`mart_merchant_performance.sql`) filters and joins on uppercase:
  ```sql
  status IN ('COMPLETED', 'FAILED')
  ```
* **Impact**: All filters evaluate to false, resulting in empty metrics.
* **Fix**: Keep the raw casing (uppercase) or align both models to use uppercase/lowercase consistently.

### 3. Invalid YAML Structure
* **Staging Schema (`staging/schema.yml`)**:
  ```yaml
  # Incorrect structure:
  stg_fact_transactions:
    source: sigma_analytics
    table: fact_transactions
  ```
  dbt expects:
  ```yaml
  version: 2
  sources:
    - name: sigma_analytics
      database: SIGMA_DE
      schema: PUBLIC
      tables:
        - name: fact_transactions
  ```

---

## 🛠️ Action Plan

1. **Clean & Fix `staging/schema.yml`**: Define the sources properly (`sigma_analytics` pointing to `SIGMA_DE.PUBLIC` containing `fact_transactions`, `dim_merchant`, and `dim_customer`).
2. **Clean & Fix `stg_transactions.sql`**: Keep only clean SQL, referencing the source macro `{{ source('sigma_analytics', 'fact_transactions') }}`, keeping casing consistent.
3. **Create `stg_merchants.sql`**: Create a staging model for merchants since `mart_merchant_performance.sql` needs to join it.
4. **Clean & Fix `mart_merchant_performance.sql`**: Keep only clean SQL, ref `stg_transactions` and `stg_merchants`, and handle casing matching.
5. **Clean & Fix `marts/schema.yml`**: Re-write with correct model definitions. Add an `accepted_values` test on `status` in the staging schema to catch `CANCELLED` and deliberately fail, or add a custom test to ensure `failure_rate_pct` is between `0` and `100`.
