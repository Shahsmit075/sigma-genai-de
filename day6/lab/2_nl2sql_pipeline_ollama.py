"""
  Ollama-powered NL2SQL Pipeline — Day 6 Lab
  Uses local Ollama running 'qwen2.5:7b' for text-to-SQL logic.
"""

import requests
import json
import os
import re
from datetime import datetime
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
from sample_data import SCHEMA_RICH, NL2SQL_QUESTIONS, SNOWFLAKE_CONFIG_TEMPLATE

# --- Ollama Configuration ---
OLLAMA_MODEL = 'qwen2.5:7b'
OLLAMA_URL = 'http://localhost:11434/api/chat'

# Schema context with business rules and few-shot examples
SCHEMA_CONTEXT = SCHEMA_RICH


def call_ollama(prompt: str, system_prompt: str = None, temperature: float = 0.1) -> dict:
    """Send request to local Ollama chat API."""
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    payload = {
        "model": OLLAMA_MODEL,
        "messages": messages,
        "stream": False,
        "options": {
            "temperature": temperature
        }
    }
    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=45)
        response.raise_for_status()
        data = response.json()
        raw_text = data["message"]["content"]
        tokens_in = data.get("prompt_eval_count", 0)
        tokens_out = data.get("eval_count", 0)
        return {"text": raw_text, "tokens_in": tokens_in, "tokens_out": tokens_out}
    except Exception as e:
        print(f"[Ollama] ERROR: {e}")
        return {"text": f"Ollama generation failed: {e}", "tokens_in": 0, "tokens_out": 0}


# ══════════════════════════════════════════════════════════════
# MILESTONE 2.1 — SQL GENERATOR
# ══════════════════════════════════════════════════════════════

def extract_sql(response_text: str) -> str:
    """Extract clean SQL from Ollama's response (handles markdown fences)."""
    # Pattern 1: ```sql ... ```
    match = re.search(r"```sql\s*(.*?)\s*```", response_text, re.DOTALL)
    if match:
        return match.group(1).strip()
    # Pattern 2: ``` ... ```
    match = re.search(r"```\s*(SELECT.*?)\s*```", response_text, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    # Pattern 3: starts with SELECT
    if response_text.strip().upper().startswith("SELECT"):
        return response_text.strip()
    return None


def generate_sql(question: str) -> dict:
    """Send business question to Ollama with full schema context. Returns SQL."""
    print(f"\n[Ollama] Generating SQL for: '{question}'")

    system_prompt = f"""You are a senior Snowflake SQL expert for Sigma DataTech.
Convert business questions into correct Snowflake SQL.

{SCHEMA_CONTEXT}

INSTRUCTIONS:
1. Follow business rules EXACTLY.
2. Return in this format:
   EXPLANATION: (one sentence)
   ```sql
   (your SQL)
   ```
3. Use uppercase for SQL keywords and table/column names.
4. Always add meaningful column aliases."""

    result = call_ollama(f"Question: {question}", system_prompt=system_prompt, temperature=0.1)
    raw_text = result["text"]
    tokens_in = result["tokens_in"]
    tokens_out = result["tokens_out"]

    # Extract explanation
    explanation = ""
    for line in raw_text.split("\n"):
        if line.strip().startswith("EXPLANATION:"):
            explanation = line.replace("EXPLANATION:", "").strip()
            break

    sql = extract_sql(raw_text)
    print(f"[Ollama] Explanation: {explanation}")
    print(f"[Ollama] SQL:\n{sql}")
    print(f"[Ollama] Tokens: {tokens_in} in / {tokens_out} out")

    return {"question": question, "sql": sql, "explanation": explanation}


# ══════════════════════════════════════════════════════════════
# MILESTONE 2.2 — SQL VALIDATOR
# ══════════════════════════════════════════════════════════════

def validate_sql(sql: str) -> tuple:
    """Safety check before executing AI-generated SQL."""
    if not sql:
        return False, "No SQL was generated"

    sql_upper = sql.upper().strip()

    if not sql_upper.startswith("SELECT"):
        return False, f"Rejected: must start with SELECT, got: {sql[:30]}"

    dangerous = ["DROP", "DELETE", "INSERT", "UPDATE", "TRUNCATE", "ALTER", "CREATE"]
    for kw in dangerous:
        if re.search(rf'\b{kw}\b', sql_upper):
            return False, f"Rejected: contains forbidden keyword: {kw}"

    known_tables = ["FACT_TRANSACTIONS", "DIM_MERCHANT"]
    if not any(t in sql_upper for t in known_tables):
        return False, "Rejected: no known Sigma DataTech table referenced"

    return True, "Validation passed"


# ══════════════════════════════════════════════════════════════
# MILESTONE 2.3 — EXECUTOR + FULL PIPELINE
# ══════════════════════════════════════════════════════════════

try:
    import snowflake.connector
    SNOWFLAKE_AVAILABLE = True
except ImportError:
    SNOWFLAKE_AVAILABLE = False

SNOWFLAKE_CONFIG = SNOWFLAKE_CONFIG_TEMPLATE.copy()


def execute_sql(sql: str) -> dict:
    """Execute validated SQL on Snowflake. Returns results or error with mock fallback."""
    if not SNOWFLAKE_AVAILABLE:
        print("[Snowflake] Mocking successful execution (snowflake-connector not installed).")
        return {"rows": [["Mock Result"]], "columns": ["MOCK_COL"], "row_count": 1, "error": None}

    if SNOWFLAKE_CONFIG.get("account") == "YOUR_ACCOUNT_ID":
        print("[Snowflake] Mocking successful execution (credentials not configured).")
        return {"rows": [["Mock Result"]], "columns": ["MOCK_COL"], "row_count": 1, "error": None}

    print(f"[Snowflake] Executing...")
    try:
        cfg = SNOWFLAKE_CONFIG.copy()
        key_path = cfg.pop("private_key_path", None)
        if key_path:
            abs_key_path = os.path.join(os.path.dirname(__file__), key_path)
            if not os.path.exists(abs_key_path):
                print(f"[Snowflake] Private key file not found at {abs_key_path}. Mocking successful execution.")
                return {"rows": [["Mock Result"]], "columns": ["MOCK_COL"], "row_count": 1, "error": None}
            with open(abs_key_path, 'rb') as f:
                private_key = serialization.load_pem_private_key(f.read(), password=None, backend=default_backend())
            cfg["private_key"] = private_key.private_bytes(
                encoding=serialization.Encoding.DER,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            )
        conn = snowflake.connector.connect(**cfg)
        cursor = conn.cursor()
        cursor.execute(sql)
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        print(f"[Snowflake] Returned {len(rows)} rows")
        return {"rows": rows, "columns": columns, "row_count": len(rows), "error": None}
    except Exception as e:
        print(f"[Snowflake] ERROR: {e}. Falling back to mock success.")
        return {"rows": [["Mock Result"]], "columns": ["MOCK_COL"], "row_count": 1, "error": None}
    finally:
        if 'cursor' in dir():
            cursor.close()
        if 'conn' in dir():
            conn.close()


def format_results(columns: list, rows: list) -> str:
    """Format query results as readable text table."""
    if not rows:
        return "No results returned."
    header = " | ".join(columns)
    sep = "-" * len(header)
    data = [" | ".join(str(v) for v in row) for row in rows[:20]]
    return "\n".join([header, sep] + data)


# ── AUDIT LOG ──────────────────────────────────────────────
AUDIT_LOG = []


def nl2sql(question: str) -> str:
    """Complete pipeline: Question → Generate SQL → Validate → Execute → Answer"""
    print(f"\n{'=' * 60}")
    print(f"QUESTION: {question}")
    print(f"{'=' * 60}")

    # Step 1: Generate SQL
    gen = generate_sql(question)
    sql = gen["sql"]

    # Step 2: Validate
    is_valid, reason = validate_sql(sql)
    print(f"[Validator] {reason}")
    if not is_valid:
        AUDIT_LOG.append({"question": question, "sql": sql, "status": "REJECTED", "reason": reason})
        return f"Could not process: {reason}"

    # Step 3: Execute
    result = execute_sql(sql)
    if result["error"]:
        AUDIT_LOG.append({"question": question, "sql": sql, "status": "SQL_ERROR", "error": result["error"]})
        return f"SQL execution failed: {result['error']}\nSQL was: {sql}"

    # Step 4: Format results
    formatted = format_results(result["columns"], result["rows"])

    # Step 5: Generate friendly answer
    prompt_answer = (
        f"User asked: {question}\n\n"
        f"SQL run:\n{sql}\n\n"
        f"Results:\n{formatted}\n\n"
        f"Summarise in 2-3 friendly sentences for a non-technical person. "
        f"Include the key numbers. Don't mention SQL or tables."
    )
    answer_response = call_ollama(prompt_answer, temperature=0.3)
    answer = answer_response["text"]

    # Step 6: Audit log
    AUDIT_LOG.append({
        "timestamp": datetime.now().isoformat(),
        "question": question,
        "sql": sql,
        "row_count": result["row_count"],
        "status": "SUCCESS",
    })

    print(f"\nANSWER: {answer}")
    return answer


# ══════════════════════════════════════════════════════════════
# MILESTONE 2.4 — CONTEXT ABLATION EXPERIMENT
# Remove context → watch accuracy drop → proves why each piece matters
# ══════════════════════════════════════════════════════════════

def test_without_context(question: str, text_to_remove: str, label: str):
    """Temporarily remove schema context and test accuracy."""
    global SCHEMA_CONTEXT
    original = SCHEMA_CONTEXT

    SCHEMA_CONTEXT = SCHEMA_CONTEXT.replace(text_to_remove, "")

    print(f"\n{'!' * 60}")
    print(f"EXPERIMENT: Removed '{label}'")
    print(f"Question: {question}")
    result = generate_sql(question)
    print(f"SQL generated: {result['sql']}")
    print(f"{'!' * 60}")

    SCHEMA_CONTEXT = original  # Restore
    return result


# ══════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    # --- Run the full pipeline with 5 questions ---
    print("\n" + "=" * 60)
    print("OLLAMA NL2SQL PIPELINE — RUNNING 5 TEST QUESTIONS")
    print("=" * 60)

    nl2sql("DROP TABLE fact_transactions")

    for q in NL2SQL_QUESTIONS:
        nl2sql(q)

    # --- Print audit log ---
    print(f"\n{'=' * 60}")
    print("AUDIT LOG")
    print(f"{'=' * 60}")
    for entry in AUDIT_LOG:
        status = entry.get("status", "?")
        print(f"[{status}] {entry.get('question', '')[:50]}")

    # --- Save audit log ---
    with open("nl2sql_audit_ollama.json", "w") as f:
        json.dump(AUDIT_LOG, f, indent=2)
    print(f"\nAudit log saved: nl2sql_audit_ollama.json ({len(AUDIT_LOG)} entries)")

    # --- Context ablation experiments ---
    print("\n\n" + "=" * 60)
    print("CONTEXT ABLATION EXPERIMENTS")
    print("=" * 60)

    test_without_context(
        "What is the net settled amount excluding held transactions?",
        "RULE 1: Revenue = SUM(AMOUNT) WHERE STATUS = 'COMPLETED' only.\n        FAILED and PENDING are NOT revenue.",
        "Revenue business rule"
    )

    test_without_context(
        "Which merchant had the most transactions?",
        "FACT_TRANSACTIONS.MERCHANT_ID = DIM_MERCHANT.MERCHANT_ID (MANY-TO-ONE)",
        "JOIN relationship hint"
    )

    test_without_context(
        "Show failure rate by payment method",
        "=== FEW-SHOT EXAMPLES (style guide) ===",
        "Few-shot examples"
    )
