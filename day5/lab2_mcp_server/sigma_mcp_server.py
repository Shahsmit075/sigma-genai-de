# ============================================================
# sigma_mcp_server.py
# Sigma DataTech MCP Server — wraps Snowflake for AI clients
# Day 5, Lab 2 — GenAI for Data Engineering
# ============================================================
#
# WHAT THIS FILE IS:
#   An MCP (Model Context Protocol) server that exposes 3 Snowflake
#   query tools. Any MCP client — including our Nova Lite client —
#   can connect and use these tools without knowing anything about
#   Snowflake credentials or SQL.
#
# HOW TOOL REGISTRATION WORKS HERE (vs Lab 1):
#   Lab 1: TOOLS = [...] passed into every bedrock.converse() call
#   Lab 2: @app.list_tools() decorator answers "what tools exist?"
#          @app.call_tool() decorator runs the tool when called
#
# HOW IT RUNS:
#   This server communicates over STDIN/STDOUT (stdio transport).
#   The client starts it as a subprocess and sends JSON messages.
#   You never run this file directly — the client starts it for you.
#
# ============================================================

import asyncio
import json
import sys
import snowflake.connector
from mcp.server import Server
from mcp.server.stdio import stdio_server
import mcp.types as types

# ── CONFIGURATION ──────────────────────────────────────────────
# In production this would come from AWS Secrets Manager.
# For the lab, credentials are hardcoded here.
# This is the KEY advantage of MCP — credentials live in ONE place.
SNOWFLAKE_CONFIG = {
    "user":      "SMITSHAH12",
    "password":  "MVkw8eX4GKpfmR6",
    "account":   "YSIBBUB-WV28708",
    "database":  "SIGMA_DE",
    "schema":    "PUBLIC",
    "warehouse": "COMPUTE_WH"
}

# ── CREATE THE SERVER INSTANCE ──────────────────────────────────
# Server() takes a name — this is what clients see when they connect.
# Think of it as the service name in a microservices architecture.
app = Server("sigma-datatech-snowflake")


# ── SAFE LOGGING ───────────────────────────────────────────────
# MCP servers communicate over stdio (STDIN/STDOUT).
# If you use print() for debug logs, it corrupts the MCP protocol.
# Use sys.stderr instead — it goes to your terminal without
# interfering with the JSON protocol messages.
def log(message: str):
    print(f"[SigmaMCPServer] {message}", file=sys.stderr)


log("Server module loaded. Waiting for client connection...")


# ── HELPER: SNOWFLAKE QUERY ─────────────────────────────────────
# Central function all tools use to hit Snowflake.
# Opens a connection, runs the query, closes cleanly.
def run_snowflake_query(sql: str) -> list:
    """
    Executes a SQL query against Sigma DataTech Snowflake.
    Returns a list of rows as tuples.
    """
    conn = snowflake.connector.connect(**SNOWFLAKE_CONFIG)
    cursor = conn.cursor()
    try:
        cursor.execute(sql)
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


# ── TOOL REGISTRATION: list_tools ──────────────────────────────
# This is how MCP registers tools — completely different from Lab 1.
#
# When a client connects and asks "what tools do you have?",
# MCP calls this function and returns the list.
#
# Lab 1 equivalent: the TOOLS = [...] list you passed to toolConfig
# Lab 2 here: @app.list_tools() decorator does the same thing,
#             but the server answers dynamically when asked.
@app.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """
    Returns the list of tools this MCP server exposes.
    Called automatically when a client connects and asks for tools.
    """
    return [
        # ── TOOL 1: get_row_count ──────────────────────────
        # Simple COUNT(*) for any table.
        # Nova calls this when asked about row counts.
        types.Tool(
            name="get_row_count",
            description=(
                "Returns the total number of rows in a Sigma DataTech "
                "Snowflake table. Use this when the user asks about "
                "row counts, record counts, or how many entries exist "
                "in a table."
            ),
            inputSchema={
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
        ),

        # ── TOOL 2: run_sql ────────────────────────────────
        # The most powerful tool — Nova writes its OWN SQL and
        # this tool executes it. This is what makes the assistant
        # truly flexible for any analytical question.
        # Only SELECT queries allowed (enforced below).
        types.Tool(
            name="run_sql",
            description=(
                "Executes a custom SQL SELECT query on Sigma DataTech "
                "Snowflake tables and returns the results. Use this for "
                "complex analytical questions like aggregations, filters, "
                "joins, or any question not covered by other tools. "
                "Only SELECT queries are permitted."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "sql": {
                        "type": "string",
                        "description": (
                            "A valid SQL SELECT statement. "
                            "Available tables: FACT_TRANSACTIONS, DIM_MERCHANT. "
                            "Do not use any DML statements (INSERT, UPDATE, DELETE)."
                        )
                    }
                },
                "required": ["sql"]
            }
        ),

        # ── TOOL 3: get_merchant_summary ───────────────────
        # Pre-built JOIN query — merchant performance report.
        # Nova calls this for merchant-related business questions.
        types.Tool(
            name="get_merchant_summary",
            description=(
                "Returns a merchant performance summary by joining "
                "FACT_TRANSACTIONS with DIM_MERCHANT. Shows total transactions, "
                "completed, failed, and total revenue per merchant. "
                "Use this for merchant performance or business summary questions."
            ),
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
    ]


# ── TOOL EXECUTION: call_tool ───────────────────────────────────
# When a client calls a tool, MCP routes it here.
# This decorator is the execution engine — it receives the tool name
# and arguments, runs the right SQL, and returns the result.
#
# Lab 1 equivalent: your execute_tool() function + the individual
#                   get_row_count(), get_status_count() functions
# Lab 2 here: everything lives on the server, not the client script.
@app.call_tool()
async def handle_call_tool(
    name: str,
    arguments: dict
) -> list[types.TextContent]:
    """
    Executes the requested tool and returns the result.
    Called automatically when a client sends a tool call request.
    """
    log(f"Tool called: {name} with args: {arguments}")

    try:
        # ── TOOL 1 HANDLER: get_row_count ──────────────────
        if name == "get_row_count":
            table_name = arguments["table_name"].upper()
            rows = run_snowflake_query(f"SELECT COUNT(*) FROM {table_name}")
            count = rows[0][0]
            result = f"{table_name} contains {count:,} rows."

        # ── TOOL 2 HANDLER: run_sql ────────────────────────
        elif name == "run_sql":
            sql = arguments["sql"]

            # Security check: only allow SELECT statements
            # This is a basic allow-list — production would be stricter
            if not sql.strip().upper().startswith("SELECT"):
                result = "Error: Only SELECT queries are permitted."
            else:
                rows = run_snowflake_query(sql)
                if not rows:
                    result = "Query returned no results."
                else:
                    # Format rows as pipe-separated text for Nova to read
                    result = "\n".join(
                        " | ".join(str(cell) for cell in row)
                        for row in rows
                    )

        # ── TOOL 3 HANDLER: get_merchant_summary ───────────
        elif name == "get_merchant_summary":
            sql = """
                SELECT
                    m.MERCHANT_NAME,
                    m.CATEGORY,
                    m.CITY,
                    COUNT(t.TRANSACTION_ID)                          AS total_transactions,
                    SUM(CASE WHEN t.STATUS = 'COMPLETED' THEN 1 ELSE 0 END) AS completed,
                    SUM(CASE WHEN t.STATUS = 'FAILED'    THEN 1 ELSE 0 END) AS failed,
                    SUM(CASE WHEN t.STATUS = 'COMPLETED' THEN t.AMOUNT ELSE 0 END) AS revenue
                FROM FACT_TRANSACTIONS t
                JOIN DIM_MERCHANT m ON t.MERCHANT_ID = m.MERCHANT_ID
                GROUP BY m.MERCHANT_NAME, m.CATEGORY, m.CITY
                ORDER BY revenue DESC
            """
            rows = run_snowflake_query(sql)
            lines = ["Merchant | Category | City | Total | Completed | Failed | Revenue"]
            lines += [
                f"{r[0]} | {r[1]} | {r[2]} | {r[3]} | {r[4]} | {r[5]} | ${r[6]:,.2f}"
                for r in rows
            ]
            result = "\n".join(lines)

        else:
            result = f"Unknown tool: {name}"

    except Exception as e:
        result = f"Tool execution error: {str(e)}"
        log(f"ERROR in {name}: {str(e)}")

    log(f"Tool result: {result[:100]}...")

    # MCP expects results as a list of TextContent objects
    return [types.TextContent(type="text", text=result)]


# ── SERVER ENTRY POINT ──────────────────────────────────────────
# stdio_server() wires up STDIN/STDOUT as the transport layer.
# The client connects by launching this script as a subprocess.
async def main():
    async with stdio_server() as (read_stream, write_stream):
        log("MCP Server started. Listening for client connections...")
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())
