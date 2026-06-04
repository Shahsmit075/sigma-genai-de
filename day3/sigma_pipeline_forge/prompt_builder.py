"""
All Bedrock prompts for Sigma DataTech Pipeline Forge.
Centralised here so prompt quality can be iterated without touching app.py.
"""

SYSTEM_PROMPT = """You are a senior Data Engineer at Sigma DataTech, a Series B fintech startup
processing 4 million transactions per day on AWS. You write clean, production-ready Python code
with proper logging, error handling, docstrings, and inline comments.
Always use boto3 for AWS operations. Never use print() — use logging."""


# ── Glue ETL Script ────────────────────────────────────────────────────────────
def build_glue_etl_prompt(bucket_name: str, source_columns: list) -> str:
    cols = ', '.join(source_columns)
    return f"""Write a complete AWS Glue Python Shell (Python 3.9) ETL script for Sigma DataTech.

Bucket: {bucket_name}
Input columns: {cols}

The script must:
1. Parse job arguments: --bucket_name, --date_partition, --job_type (orders or reference)
2. For job_type=orders:
   - Read CSV from s3://{{bucket_name}}/raw/orders/date={{date_partition}}/orders.csv using boto3 + pandas
   - Count and log: null customer_ids, negative amounts, duplicate order_ids
   - Fix: drop null customer_ids, abs() negative amounts, drop_duplicates on order_id (keep first)
   - Add columns: processed_at (ISO timestamp), is_high_value (True if amount > 10000)
   - Write clean CSV to s3://{{bucket_name}}/processed/orders/date={{date_partition}}/orders.csv
   - Write a JSON quality report to s3://{{bucket_name}}/reports/quality_report_orders_{{date_partition}}.json
3. For job_type=reference:
   - Copy customers.csv and products.csv from raw/ to processed/
4. Use Python logging throughout (INFO for each step, ERROR on exception)
5. Wrap entire job in try/except — log error and re-raise

Output only the Python script. No explanation, no markdown fences."""


# ── NL2SQL ─────────────────────────────────────────────────────────────────────
def build_nl2sql_prompt(question: str, schema_context: str) -> str:
    return f"""Convert this business question to a valid Athena SQL query.

Database: sigma_db
Schema:
{schema_context}

Question: {question}

Rules:
- Athena uses Presto SQL syntax
- All string comparisons are case-sensitive
- is_high_value column contains the strings 'True' or 'False' (not booleans)
- amount is stored as DOUBLE
- Always add LIMIT 100 unless the question asks for aggregates
- Output only the raw SQL query — no explanation, no markdown, no code fences"""


# ── Data Quality Analysis ──────────────────────────────────────────────────────
def build_data_quality_prompt(report_json: str) -> str:
    return f"""Analyse this Glue job quality report for Sigma DataTech's orders pipeline.

{report_json}

Write a 3-part response:
1. Status (one word: HEALTHY / WARNING / CRITICAL) followed by one sentence
2. What specific issues were found and their business impact (be concrete with numbers)
3. One actionable recommendation for the data engineering team

Max 120 words. Plain English only — no bullet points, no headers."""


# ── Query Result Explanation ───────────────────────────────────────────────────
def build_query_explanation_prompt(question: str, sql: str, result_summary: str) -> str:
    return f"""A business analyst at Sigma DataTech asked: "{question}"

The query that ran:
{sql}

Query result: {result_summary}

Write exactly one plain-English sentence answering their question using the specific
numbers from the result. No technical jargon. No mention of SQL."""


# ── Pipeline Health Summary ────────────────────────────────────────────────────
def build_health_summary_prompt(all_reports_json: str) -> str:
    return f"""Review all pipeline quality reports for Sigma DataTech and give an executive summary.

{all_reports_json}

Write 3 sentences:
1. Overall pipeline health across all loaded days
2. The most significant anomaly found (if any) and which day it occurred
3. One recommendation for the DE team before going to production

Max 100 words. Be specific with numbers."""


# ── Schema context for NL2SQL ─────────────────────────────────────────────────
SCHEMA_CONTEXT = """
Table: orders
  order_id STRING, customer_id STRING, product_id STRING, amount DOUBLE,
  status STRING ('completed'|'pending'|'failed'|'refunded'),
  payment_method STRING ('UPI'|'Net Banking'|'Credit Card'|'Debit Card'|'Wallet'),
  created_at STRING, city STRING, processed_at STRING,
  is_high_value STRING ('True'|'False'),
  date STRING  ← partition key, format YYYY-MM-DD

Table: customers
  customer_id STRING, name STRING, email STRING, phone STRING,
  city STRING, tier STRING ('Gold'|'Silver'|'Bronze'), signup_date STRING

Table: products
  product_id STRING, name STRING,
  category STRING ('Payments'|'Lending'|'Insurance'|'Investments'|'Transfers'),
  price DOUBLE, is_active STRING

Note: All amounts are in Indian Rupees (INR).
"""

# ── Pre-built quick questions ──────────────────────────────────────────────────
QUICK_QUESTIONS = [
    "Which city had the highest total revenue across all days?",
    "What percentage of orders used UPI as payment method?",
    "Which product category generates the most revenue?",
    "How many orders were placed each day? Show the daily trend.",
    "Who are the top 5 customers by total spend?",
]
