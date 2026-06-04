# ============================================================
# lab1_tool_calling.py
# Sigma DataTech — Tool Calling with Amazon Nova Lite
# Day 5, Lab 1 — GenAI for Data Engineering
# ============================================================
#
# WHAT THIS FILE DOES:
#   Lets a non-technical analyst ask plain English questions
#   about live Snowflake data. Nova Lite decides which tool to
#   call — your Python code actually runs the SQL.
#
# HOW THE ROUND-TRIP WORKS:
#   1. User question + tool list  →  Nova Lite (Bedrock Call 1)
#   2. Nova responds with tool request (NOT an answer yet)
#   3. Python runs the SQL on Snowflake
#   4. SQL result  →  Nova Lite (Bedrock Call 2)
#   5. Nova composes the final natural language answer
#
# ============================================================

import boto3
import snowflake.connector
import json

# ── CONFIGURATION ──────────────────────────────────────────────
# Your Snowflake credentials — same account as Data Catalogue lab
# but different database: SIGMA_DE (created in Milestone 1)
SNOWFLAKE_CONFIG = {
    "user":      "SMITSHAH12",
    "password":  "MVkw8eX4GKpfmR6",
    "account":   "YSIBBUB-WV28708",
    "database":  "SIGMA_DE",       # ← NEW database, not SIGMA_CATALOGUE
    "schema":    "PUBLIC",
    "warehouse": "COMPUTE_WH"
}

# ── BEDROCK CLIENT ─────────────────────────────────────────────
# boto3 picks up AWS credentials from ~/.aws/credentials automatically
# (configured via: aws configure)
bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')
MODEL_ID = 'amazon.nova-lite-v1:0'


# ── TOOL DEFINITIONS ───────────────────────────────────────────
# This JSON schema is what Nova Lite reads to know:
#   - WHAT tools exist
#   - WHEN to call each one (from the description)
#   - WHAT arguments to pass (from inputSchema)
#
# Nova never sees your Python code — only these descriptions.
# Good descriptions = Nova picks the right tool every time.
# Vague descriptions = wrong tool, wrong answer.

TOOLS = [
    {
        "toolSpec": {
            "name": "get_row_count",
            # Nova reads this description to decide WHEN to call this tool.
            # It will call this whenever someone asks "how many rows/records/entries"
            "description": (
                "Returns the total number of rows in a Sigma DataTech "
                "Snowflake table. Use this when the user asks about "
                "row counts, record counts, or how many entries exist "
                "in a table."
            ),
            "inputSchema": {
                "json": {
                    "type": "object",
                    "properties": {
                        "table_name": {
                            "type": "string",
                            "description": (
                                "The exact table name in uppercase. "
                                "Options: FACT_TRANSACTIONS, DIM_MERCHANT"
                            )
                        }
                    },
                    "required": ["table_name"]
                }
            }
        }
    },
    {
        "toolSpec": {
            "name": "get_status_count",
            # Nova calls this whenever someone asks about failed/completed/pending counts
            "description": (
                "Returns the count of transactions grouped by their status "
                "(COMPLETED, FAILED, PENDING) in FACT_TRANSACTIONS. "
                "Use this when the user asks about failed, completed, or "
                "pending transaction counts."
            ),
            "inputSchema": {
                "json": {
                    "type": "object",
                    "properties": {
                        "status": {
                            "type": "string",
                            "description": (
                                "The transaction status to count. "
                                "Must be one of: COMPLETED, FAILED, PENDING. "
                                "Use ALL to get all statuses."
                            )
                        }
                    },
                    "required": ["status"]
                }
            }
        }
    }
]


# ── TOOL EXECUTOR FUNCTIONS ────────────────────────────────────
# These are the ACTUAL Python implementations of the tools.
# Nova Lite cannot run these — it just asks your code to run them.
# All functions return strings because Nova expects text results.

def get_row_count(table_name: str) -> str:
    """
    Connects to Snowflake and returns the row count for a given table.

    Why return a string?
    Nova Lite works with text. Even numbers need to be formatted
    as a sentence so Nova can use them naturally in its answer.
    """
    print(f"  [Snowflake] Running: SELECT COUNT(*) FROM {table_name}")
    conn = snowflake.connector.connect(**SNOWFLAKE_CONFIG)
    cursor = conn.cursor()
    try:
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        result = f"{table_name} has {count:,} rows."
        print(f"  [Snowflake] Result: {result}")
        return result
    except Exception as e:
        return f"Error querying {table_name}: {str(e)}"
    finally:
        # Always close — good practice, prevents connection leaks
        cursor.close()
        conn.close()


def get_status_count(status: str) -> str:
    """
    Returns transaction counts by status from FACT_TRANSACTIONS.

    If status is ALL, returns all three statuses (COMPLETED, FAILED, PENDING).
    Otherwise filters to the specific status requested by Nova.
    """
    if status.upper() == "ALL":
        query = """
            SELECT STATUS, COUNT(*) AS COUNT
            FROM FACT_TRANSACTIONS
            GROUP BY STATUS
            ORDER BY STATUS
        """
    else:
        query = f"""
            SELECT STATUS, COUNT(*) AS COUNT
            FROM FACT_TRANSACTIONS
            WHERE STATUS = '{status.upper()}'
            GROUP BY STATUS
        """

    print(f"  [Snowflake] Running status count query for: {status}")
    conn = snowflake.connector.connect(**SNOWFLAKE_CONFIG)
    cursor = conn.cursor()
    try:
        cursor.execute(query)
        rows = cursor.fetchall()
        if not rows:
            return f"No transactions found with status: {status}"
        # Format as readable text for Nova
        result_lines = [f"{row[0]}: {row[1]:,} transactions" for row in rows]
        result = " | ".join(result_lines)
        print(f"  [Snowflake] Result: {result}")
        return result
    except Exception as e:
        return f"Error querying status count: {str(e)}"
    finally:
        cursor.close()
        conn.close()


# ── TOOL ROUTER ────────────────────────────────────────────────
# When Nova requests a tool, this function figures out WHICH
# Python function to call and with WHAT arguments.
# Nova sends: {"name": "get_row_count", "input": {"table_name": "FACT_TRANSACTIONS"}}
# This function maps that to: get_row_count("FACT_TRANSACTIONS")

def execute_tool(tool_name: str, tool_input: dict) -> str:
    """
    Routes Nova's tool request to the correct Python function.

    This is the bridge between Nova's JSON request and your Python code.
    In larger systems this would be a proper registry/dispatcher.
    """
    if tool_name == "get_row_count":
        return get_row_count(tool_input["table_name"])
    elif tool_name == "get_status_count":
        return get_status_count(tool_input["status"])
    else:
        return f"Unknown tool: {tool_name}"


# ── MAIN CONVERSATION FUNCTION ─────────────────────────────────
# This is the full two-call pattern:
#   Call 1: Question + tools → Nova asks for a tool
#   Call 2: Tool result → Nova gives the final answer

def ask_nova(question: str) -> str:
    """
    Full tool-calling round trip with Nova Lite.

    Args:
        question: Plain English question from the analyst

    Returns:
        Nova's final natural language answer, backed by live Snowflake data
    """
    print(f"\n{'='*60}")
    print(f"QUESTION: {question}")
    print('='*60)

    # ── BEDROCK CALL 1 ──────────────────────────────────────
    # Send the question + available tools to Nova.
    # Nova will NOT answer directly — it will ask for a tool.
    messages = [
        {"role": "user", "content": [{"text": question}]}
    ]

    response_1 = bedrock.converse(
        modelId=MODEL_ID,
        system=[{"text": (
            "You are the Sigma DataTech Data Assistant. "
            "Use the available tools to answer questions with real data. "
            "Never guess or estimate numbers — always use a tool."
        )}],
        messages=messages,
        toolConfig={"tools": TOOLS}
    )

    stop_reason = response_1["stopReason"]
    assistant_msg = response_1["output"]["message"]

    # If Nova answered directly without using a tool (shouldn't happen
    # for data questions, but handle it gracefully)
    if stop_reason != "tool_use":
        return assistant_msg["content"][0]["text"]

    # ── EXTRACT ALL TOOL REQUESTS ────────────────────────────
    # Nova can request MULTIPLE tools in a single response.
    # E.g. "Give me all statuses" → Nova calls get_status_count
    # for COMPLETED, FAILED, PENDING all at once.
    # Bedrock REQUIRES us to return a toolResult for EVERY toolUseId
    # in its response — missing even one causes a ValidationException.
    tool_uses = [
        block["toolUse"]
        for block in assistant_msg["content"]
        if "toolUse" in block
    ]

    # ── RUN ALL TOOLS & COLLECT RESULTS ──────────────────────
    tool_results = []
    for tool_use in tool_uses:
        print(f"  [Nova] Requesting tool: {tool_use['name']}")
        print(f"  [Nova] Arguments: {json.dumps(tool_use['input'])}")

        tool_result_text = execute_tool(tool_use["name"], tool_use["input"])

        # Each result must reference its own unique toolUseId
        tool_results.append({
            "toolResult": {
                "toolUseId": tool_use["toolUseId"],
                "content": [{"text": tool_result_text}]
            }
        })

    # ── BEDROCK CALL 2 ──────────────────────────────────────
    # Send ALL tool results back in ONE message.
    # content = list of all toolResult blocks (one per tool Nova called)
    messages.append(assistant_msg)
    messages.append({
        "role": "user",
        "content": tool_results
    })

    response_2 = bedrock.converse(
        modelId=MODEL_ID,
        system=[{"text": (
            "You are the Sigma DataTech Data Assistant. "
            "Use the available tools to answer questions with real data. "
            "Never guess or estimate numbers."
        )}],
        messages=messages,
        toolConfig={"tools": TOOLS}
    )

    # Nova's second response IS the final answer
    final_answer = response_2["output"]["message"]["content"][0]["text"]
    print(f"\n  NOVA ANSWER: {final_answer}")
    return final_answer


# ── ENTRY POINT ────────────────────────────────────────────────
# Run 3 test questions to verify the full pipeline works.
# Each question exercises a different tool.

if __name__ == "__main__":
    questions = [
        "How many rows are in FACT_TRANSACTIONS?",
        "How many transactions failed?",
        "Give me a breakdown of all transaction statuses.",
    ]

    for q in questions:
        ask_nova(q)
        print()
