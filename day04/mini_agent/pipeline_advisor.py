"""
Mini Agentic AI — Sigma DataTech Pipeline Advisor
Tests: AWS Bedrock (Nova Lite) + tool use (function calling) on a student laptop.

The agent has 2 tools:
  1. get_table_info   — returns schema/owner for a table from the catalogue
  2. check_pipeline   — returns fake pipeline run status for a given pipeline name

Run: python pipeline_advisor.py
Ask: "Who owns the customers table and did its pipeline run successfully today?"
The agent will call BOTH tools automatically and combine the answer.
"""

import boto3, json

client = boto3.client("bedrock-runtime", region_name="us-east-1")
MODEL  = "us.amazon.nova-lite-v1:0"   # change to us.anthropic.claude-haiku-... if available

# ── Fake data (no real AWS infra needed) ──────────────────────────────────

TABLE_INFO = {
    "customers":     {"owner": "Identity Engineering", "classification": "PII-Critical", "rows": "4.2M"},
    "transactions":  {"owner": "Payments Engineering", "classification": "Internal",     "rows": "110M"},
    "risk_scores":   {"owner": "Risk Engineering",     "classification": "Internal",     "rows": "4.2M"},
    "kyc_documents": {"owner": "Compliance",           "classification": "PII-Critical", "rows": "4.2M"},
}

PIPELINE_STATUS = {
    "customers_ingestion":    {"status": "SUCCESS", "last_run": "2026-05-22 06:00", "duration": "4m 12s", "owner": "Identity Engineering"},
    "transactions_ingestion": {"status": "SUCCESS", "last_run": "2026-05-22 06:15", "duration": "18m 03s", "owner": "Payments Engineering"},
    "risk_score_refresh":     {"status": "FAILED",  "last_run": "2026-05-22 06:30", "duration": "2m 01s", "owner": "Risk Engineering"},
    "kyc_validation":         {"status": "SUCCESS", "last_run": "2026-05-22 05:45", "duration": "7m 55s", "owner": "Compliance"},
}

# ── Tool definitions (sent to the LLM so it knows what's available) ───────

TOOLS = [
    {
        "toolSpec": {
            "name": "get_table_info",
            "description": "Returns the owner, data classification, and row count for a table in the Sigma DataTech catalogue.",
            "inputSchema": {
                "json": {
                    "type": "object",
                    "properties": {
                        "table_name": {"type": "string", "description": "Name of the table, e.g. 'customers'"}
                    },
                    "required": ["table_name"]
                }
            }
        }
    },
    {
        "toolSpec": {
            "name": "check_pipeline",
            "description": "Returns the last run status, timestamp, and duration for a data pipeline.",
            "inputSchema": {
                "json": {
                    "type": "object",
                    "properties": {
                        "pipeline_name": {"type": "string", "description": "Pipeline name, e.g. 'customers_ingestion'"}
                    },
                    "required": ["pipeline_name"]
                }
            }
        }
    },
]

# ── Tool execution (real logic would call AWS Glue, Airflow, etc.) ────────

def run_tool(name: str, inputs: dict) -> str:
    if name == "get_table_info":
        t = inputs.get("table_name", "").lower()
        info = TABLE_INFO.get(t)
        return json.dumps(info) if info else f"Table '{t}' not found in catalogue."

    if name == "check_pipeline":
        p = inputs.get("pipeline_name", "").lower()
        status = PIPELINE_STATUS.get(p)
        return json.dumps(status) if status else f"Pipeline '{p}' not found."

    return "Unknown tool."

# ── Agentic loop ──────────────────────────────────────────────────────────

def run_agent(user_question: str):
    print(f"\n{'='*55}")
    print(f"  Question: {user_question}")
    print(f"{'='*55}")

    messages = [{"role": "user", "content": [{"text": user_question}]}]
    system   = [{"text": "You are a data engineering assistant for Sigma DataTech. "
                          "Use the available tools to answer questions about tables and pipelines. "
                          "Always call the relevant tools before answering."}]

    # Agentic loop — keeps going until the model stops calling tools
    while True:
        response = client.converse(
            modelId=MODEL,
            system=system,
            messages=messages,
            toolConfig={"tools": TOOLS},
        )

        stop_reason    = response["stopReason"]
        assistant_msg  = response["output"]["message"]
        messages.append(assistant_msg)

        # Model wants to call a tool
        if stop_reason == "tool_use":
            tool_results = []
            for block in assistant_msg["content"]:
                if "toolUse" in block:                    # ← correct key in boto3 response
                    tool_name   = block["toolUse"]["name"]
                    tool_inputs = block["toolUse"]["input"]
                    tool_use_id = block["toolUse"]["toolUseId"]

                    print(f"\n  🔧 Agent calling tool: {tool_name}({tool_inputs})")
                    result = run_tool(tool_name, tool_inputs)
                    print(f"     → {result}")

                    tool_results.append({
                        "toolResult": {                   # ← correct wrapper for Bedrock
                            "toolUseId": tool_use_id,
                            "content": [{"text": result}],
                        }
                    })

            # Feed tool results back to the model
            messages.append({"role": "user", "content": tool_results})

        # Model is done — print final answer
        elif stop_reason == "end_turn":
            for block in assistant_msg["content"]:
                if "text" in block:
                    print(f"\n  💬 Agent answer:\n  {block['text']}")
            break

        else:
            print(f"  Unexpected stop reason: {stop_reason}")
            break


# ── Try it ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Question 1: forces agent to call BOTH tools
    run_agent("Who owns the customers table and did its pipeline run successfully today?")

    # Question 2: pipeline failure
    run_agent("The risk_score_refresh pipeline failed — what team should I notify?")

    # Bonus: try your own
    print("\n" + "="*55)
    q = input("  Your question (or Enter to skip): ").strip()
    if q:
        run_agent(q)
