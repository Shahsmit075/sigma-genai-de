# ============================================================
# sigma_nova_mcp.py
# Sigma DataTech — MCP Client + Nova Lite
# Day 5, Lab 2 — GenAI for Data Engineering
# ============================================================
#
# WHAT THIS FILE IS:
#   The MCP CLIENT that:
#     1. Starts sigma_mcp_server.py as a subprocess
#     2. Asks the server "what tools do you have?"
#     3. Converts those tools to Bedrock format
#     4. Sends questions to Nova Lite on AWS Bedrock
#     5. Routes Nova's tool requests → MCP Server → Snowflake
#
# HOW IT DIFFERS FROM LAB 1:
#   Lab 1: Nova → Python script → Snowflake (direct)
#   Lab 2: Nova → THIS client → MCP Server → Snowflake
#          (the server is a separate process, not a local function)
#
# THE KEY SHIFT:
#   Lab 1:  execute_tool() called get_row_count() — a local function
#   Lab 2:  session.call_tool() calls the MCP server — a separate process
#
# ============================================================

import asyncio
import json
import boto3
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# ── BEDROCK CLIENT ──────────────────────────────────────────────
bedrock   = boto3.client('bedrock-runtime', region_name='us-east-1')
MODEL_ID  = 'amazon.nova-lite-v1:0'

# ── MCP SERVER PARAMETERS ───────────────────────────────────────
# This tells the MCP client HOW to start the server.
# It launches sigma_mcp_server.py as a subprocess and connects
# to it via STDIN/STDOUT — the stdio transport.
SERVER_PARAMS = StdioServerParameters(
    command="python3",
    args=["sigma_mcp_server.py"],
    # The server script must be in the same folder as this file
)


# ── TOOL FORMAT CONVERTER ───────────────────────────────────────
# MCP and Bedrock use slightly different JSON formats for tools.
# MCP tools look like: types.Tool(name=..., description=..., inputSchema=...)
# Bedrock tools look like: {"toolSpec": {"name": ..., "inputSchema": {"json": ...}}}
#
# This function converts MCP format → Bedrock format so Nova
# can read the tools that came from the MCP server.
def mcp_tools_to_bedrock_format(mcp_tools) -> list:
    """
    Converts MCP Tool objects to Bedrock toolSpec format.

    This translation layer is what lets you use ANY MCP server
    with ANY Bedrock model — MCP is model-agnostic.
    """
    bedrock_tools = []
    for tool in mcp_tools:
        bedrock_tools.append({
            "toolSpec": {
                "name":        tool.name,
                "description": tool.description,
                "inputSchema": {
                    "json": tool.inputSchema  # MCP's inputSchema is already a dict
                }
            }
        })
    return bedrock_tools


# ── MAIN CONVERSATION FUNCTION ──────────────────────────────────
async def ask_with_mcp(question: str):
    """
    Full round-trip: question → Nova → MCP Server → Snowflake → answer.

    The flow:
      1. Connect to MCP server, get tool list
      2. Convert tools to Bedrock format
      3. Send question + tools to Nova (Bedrock Call 1)
      4. Nova requests a tool → client calls MCP server
      5. MCP server runs SQL on Snowflake → returns result
      6. Send result to Nova (Bedrock Call 2) → final answer
    """
    print(f"\n{'='*60}")
    print(f"QUESTION: {question}")
    print('='*60)

    # ── CONNECT TO MCP SERVER ────────────────────────────────
    # stdio_client() starts sigma_mcp_server.py as a subprocess.
    # ClientSession handles the MCP protocol over STDIN/STDOUT.
    # Everything inside this block has an active server connection.
    async with stdio_client(SERVER_PARAMS) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # ── STEP 1: GET TOOLS FROM MCP SERVER ──────────────
            # This is the key difference from Lab 1.
            # Instead of reading TOOLS from a local Python list,
            # we ASK the server what tools it has.
            mcp_tool_list  = await session.list_tools()
            bedrock_tools  = mcp_tools_to_bedrock_format(mcp_tool_list.tools)
            print(f"[MCP] Connected. {len(bedrock_tools)} tools available.")

            # ── STEP 2: FIRST CALL TO NOVA LITE ────────────────
            # Exact same pattern as Lab 1 — question + tool list.
            # Nova will NOT answer yet — it asks for a tool.
            messages = [
                {"role": "user", "content": [{"text": question}]}
            ]

            response_1 = bedrock.converse(
                modelId=MODEL_ID,
                system=[{"text": (
                    "You are the Sigma DataTech Data Assistant. "
                    "Use the available tools to answer questions with real data. "
                    "Never guess or estimate numbers."
                )}],
                messages=messages,
                toolConfig={"tools": bedrock_tools}
            )

            stop_reason   = response_1["stopReason"]
            assistant_msg = response_1["output"]["message"]

            # If Nova answered without tools (edge case)
            if stop_reason != "tool_use":
                print(response_1["output"]["message"]["content"][0]["text"])
                return

            # ── STEP 3: EXTRACT ALL TOOL REQUESTS ──────────────
            # Same multi-tool fix from Lab 1 —
            # Nova may request multiple tools at once.
            tool_uses = [
                block["toolUse"]
                for block in assistant_msg["content"]
                if "toolUse" in block
            ]

            # ── STEP 4: ROUTE TOOL CALLS THROUGH MCP SERVER ────
            # THIS IS THE KEY DIFFERENCE FROM LAB 1.
            #
            # Lab 1: tool_result = get_row_count(table_name)
            #        → calls a local Python function directly
            #
            # Lab 2: mcp_result = await session.call_tool(name, args)
            #        → sends a request to the MCP server subprocess
            #        → server runs SQL on Snowflake
            #        → returns result over STDIN/STDOUT
            tool_results = []
            for tool_use in tool_uses:
                print(f"[Nova] Requesting tool: {tool_use['name']}")
                print(f"[Nova] Arguments: {json.dumps(tool_use['input'])}")

                # Call the MCP server — not a local function!
                mcp_result       = await session.call_tool(
                    tool_use["name"],
                    tool_use["input"]
                )
                tool_result_text = mcp_result.content[0].text
                print(f"[MCP]  Result: {tool_result_text[:100]}...")

                tool_results.append({
                    "toolResult": {
                        "toolUseId": tool_use["toolUseId"],
                        "content":   [{"text": tool_result_text}]
                    }
                })

            # ── STEP 5: SECOND CALL TO NOVA LITE ───────────────
            # Send all tool results back → Nova composes final answer.
            # Same two-call pattern as Lab 1.
            messages.append(assistant_msg)
            messages.append({
                "role":    "user",
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
                toolConfig={"tools": bedrock_tools}
            )

            final = response_2["output"]["message"]["content"][0]["text"]
            print(f"\n NOVA ANSWER: {final}")


# ── ENTRY POINT ──────────────────────────────────────────────────
async def main():
    """
    Run 3 test questions — each exercises a different tool.
    """
    questions = [
        "How many rows are in FACT_TRANSACTIONS?",
        "Which payment method has the most failed transactions?",
        "Give me a merchant performance summary.",
    ]

    for q in questions:
        await ask_with_mcp(q)
        print()


if __name__ == "__main__":
    asyncio.run(main())
