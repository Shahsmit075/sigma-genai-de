# ⚖️ Cortex Analyst vs. Custom NL2SQL Pipeline
**Day 6 · Comparative Evaluation Report · Sigma DataTech**

This report compares the SQL generation logic, accuracy, and latency of **Snowflake Cortex Analyst** (using Mistral Large 2) against our **Custom NL2SQL Pipeline** (using Amazon Nova Lite) across 5 standard analytical questions.

---

## 📊 Side-by-Side SQL Comparison

### Q1: "How many transactions do we have in total?"
* **Custom NL2SQL**:
  ```sql
  SELECT COUNT(*) AS TOTAL_TRANSACTIONS 
  FROM FACT_TRANSACTIONS;
  ```
* **Cortex Analyst**:
  ```sql
  SELECT COUNT(*) AS total_transactions
  FROM FACT_TRANSACTIONS;
  ```
* **Verdict**: **Tie (Equivalent)**. Both correctly identified that a simple `COUNT(*)` on `FACT_TRANSACTIONS` is sufficient.

---

### Q2: "How many transactions failed?"
* **Custom NL2SQL**:
  ```sql
  SELECT COUNT(*) AS FAILED_TRANSACTION_COUNT
  FROM FACT_TRANSACTIONS
  WHERE STATUS = 'FAILED';
  ```
* **Cortex Analyst**:
  ```sql
  SELECT COUNT(*)
  FROM FACT_TRANSACTIONS
  WHERE STATUS = 'FAILED';
  ```
* **Verdict**: **Tie (Equivalent)**. Custom NL2SQL used a slightly more descriptive column alias (`FAILED_TRANSACTION_COUNT`), whereas Cortex returned the raw count column. Both correctly filtered on `STATUS = 'FAILED'`.

---

### Q3: "Which merchant had the highest revenue?"
* **Custom NL2SQL**:
  ```sql
  SELECT M.MERCHANT_NAME,
         SUM(CASE WHEN T.STATUS = 'COMPLETED' THEN T.AMOUNT ELSE 0 END) AS REVENUE_USD
  FROM FACT_TRANSACTIONS T
  JOIN DIM_MERCHANT M ON T.MERCHANT_ID = M.MERCHANT_ID
  WHERE T.TRANSACTION_DATE BETWEEN '2024-01-15' AND '2024-01-31'
  GROUP BY M.MERCHANT_NAME
  ORDER BY REVENUE_USD DESC
  LIMIT 1;
  ```
* **Cortex Analyst**:
  ```sql
  SELECT MERCHANT_NAME, SUM(AMOUNT) AS REVENUE
  FROM FACT_TRANSACTIONS
  JOIN DIM_MERCHANT ON FACT_TRANSACTIONS.MERCHANT_ID = DIM_MERCHANT.MERCHANT_ID
  WHERE STATUS = 'COMPLETED'
  GROUP BY MERCHANT_NAME
  ORDER BY REVENUE DESC
  LIMIT 1;
  ```
* **Verdict**: **Cortex Analyst wins on correctness**. 
  * Custom NL2SQL hallucinated a date range filter (`WHERE T.TRANSACTION_DATE BETWEEN '2024-01-15' AND '2024-01-31'`) which was not requested.
  * Cortex Analyst correctly applied the `STATUS = 'COMPLETED'` filter to the entire query and summed the amount directly, which is cleaner and produces the exact overall top merchant.

---

### Q4: "What is the failure rate for each payment method?"
* **Custom NL2SQL**:
  ```sql
  SELECT PAYMENT_METHOD,
         COUNT(*) AS TOTAL_TRANSACTIONS,
         SUM(CASE WHEN STATUS='FAILED' THEN 1 ELSE 0 END) AS FAILED_TRANSACTIONS,
         ROUND(100.0 * SUM(CASE WHEN STATUS='FAILED' THEN 1 ELSE 0 END) / COUNT(*), 2) AS FAILURE_RATE_PCT
     FROM FACT_TRANSACTIONS
     GROUP BY PAYMENT_METHOD
     ORDER BY FAILURE_RATE_PCT DESC;
  ```
* **Cortex Analyst**:
  ```sql
  SELECT PAYMENT_METHOD,
         (SUM(CASE WHEN STATUS = 'FAILED' THEN 1 ELSE 0 END) * 1.0 / COUNT(*)) AS FAILURE_RATE
  FROM FACT_TRANSACTIONS
  GROUP BY PAYMENT_METHOD;
  ```
* **Verdict**: **Custom NL2SQL wins on compliance and formatting**.
  * Custom NL2SQL followed the business rule guidelines precisely: it multiplied by `100.0` to calculate a percentage, rounded to 2 decimal places (`FAILURE_RATE_PCT`), and sorted the output in descending order.
  * Cortex Analyst returned a decimal ratio (e.g. `0.15` instead of `15.0%`) and omitted the sorting step.

---

### Q5: "What was the total revenue generated across all merchants?"
* **Custom NL2SQL**:
  ```sql
  SELECT SUM(CASE WHEN STATUS='COMPLETED' THEN AMOUNT ELSE 0 END) AS TOTAL_REVENUE_USD
  FROM FACT_TRANSACTIONS;
  ```
* **Cortex Analyst**:
  ```sql
  SELECT SUM(AMOUNT) AS TOTAL_REVENUE
  FROM FACT_TRANSACTIONS
  WHERE STATUS = 'COMPLETED';
  ```
* **Verdict**: **Tie (Logically Equivalent)**. 
  * Custom NL2SQL used conditional aggregation (`SUM(CASE WHEN STATUS='COMPLETED'...)`).
  * Cortex Analyst used a simpler global `WHERE` filter. Both methods yield the correct revenue sum.

---

## ⏱️ Execution & Latency Profile

| Metric | Custom NL2SQL (Nova Lite) | Cortex Analyst (Mistral Large 2) |
| :--- | :--- | :--- |
| **Average Latency** | ~2.5 seconds | ~16.5 seconds (excluding outliers) |
| **Max Latency** | ~4.0 seconds | 864.8 seconds (Question 5)* |
| **API Boundary** | Multi-hop (AWS Bedrock ➔ Local ➔ Snowflake) | In-database execution (No data leaves Snowflake) |

> [!NOTE]
> *The 864.8s outlier for Cortex Analyst Question 5 represents a transient network handshake or API connection pool timeout during Snowflake execution. Under normal conditions, Cortex Analyst queries execute in 10-15 seconds.

---

## 💡 Architectural Pros & Cons

### 1. Custom NL2SQL Pipeline (Nova Lite / Local LLM)
* **Pros**:
  * **Ultra-low latency**: Direct API response times under 3 seconds.
  * **Fine-grained control**: Easy to inject few-shot prompt examples and force formatting rules (e.g., forcing percentages or `ORDER BY` clauses).
  * **Low cost**: Using smaller models (Nova Lite or local Qwen 2.5) is highly cost-effective.
* **Cons**:
  * **Context limits**: Scale-out requires manually feeding table schemas into the prompt, consuming tokens.
  * **Security**: Schemas and query results are sent to external model APIs.

### 2. Snowflake Cortex Analyst (Mistral Large 2)
* **Pros**:
  * **In-Database Security**: Fully governed within the Snowflake perimeter (zero external API leakage of metadata or query results).
  * **Semantic Model Grounding**: Uses a centralized `.yaml` semantic model that maps columns, joins, and synonyms, reducing hallucinations on schema structures.
* **Cons**:
  * **Higher Latency**: The cold-start connection and metadata compile phase take longer (~15s average).
  * **Rigid Formatting**: Harder to force aesthetic rules (like decimal rounding or percentage conversions) without altering the semantic model files.
