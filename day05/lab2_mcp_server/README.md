# 🔌 LAB 2 — Build Your Own Python MCP Server
**Day 5 | GenAI for Data Engineering | Sigma DataTech Training**

---

## 🎯 Mission Brief

FROM: Rahul Verma, Platform Architect — Sigma DataTech

> In Lab 1 you hardcoded tool definitions inside a single script.  
> Sigma DataTech has 12 data teams. Each team would copy-paste the same  
> Snowflake tool code. When the password rotates — 12 people update 12 scripts.  
> **Build a single MCP Server that wraps Snowflake. Any AI app connects to it.**

---

## 🧠 What Changed from Lab 1 → Lab 2

```
LAB 1 (not scalable):
─────────────────────────────────
Script A: Nova + tools (hardcoded)
Script B: Nova + tools (copy-pasted)
Script C: Nova + tools (outdated)

Problem: 3 codebases, 3 sets of credentials, 3 maintenance headaches

LAB 2 — MCP ARCHITECTURE (production-ready):
─────────────────────────────────────────────
                   ┌──────────────────────────┐
Script A ─────────►│                          │
Script B ─────────►│  MCP Server              ├──► Snowflake
Script C ─────────►│  (tools defined once)    │
Nova Lite ────────►│                          │
                   └──────────────────────────┘

Solution: One server. Tools defined once. Any client connects.
```

---

## 🧠 How MCP Communication Works

```
MCP uses a simple protocol over STDIN/STDOUT (called stdio transport).
It's like an HTTP API but over process I/O — JSON messages go back and forth.

Client                              Server
  │                                   │
  │── "list_tools" request ──────────►│
  │◄─ [get_row_count, run_sql, ...] ──│
  │                                   │
  │── "call_tool: get_row_count" ────►│
  │                    (server runs SQL on Snowflake)
  │◄─ "FACT_TRANSACTIONS has 50 rows"─│
```

---

## 🧠 How Tool Registration Works in MCP (vs Lab 1)

```
LAB 1 — Tools registered by passing JSON to Bedrock API call:
  bedrock.converse(toolConfig={"tools": TOOLS})
  ❌ Must be passed every single API call
  ❌ Hardcoded in your script

LAB 2 — Tools registered on the SERVER with a decorator:
  @app.list_tools()
  async def handle_list_tools():
      return [Tool(name="get_row_count", ...)]
  ✅ Client asks server "what tools do you have?"
  ✅ Server answers — defined once, used by everyone
  ✅ Credentials live only on the server
```

---

## ✅ Pre-Flight Checks

```bash
# 1. Lab 1 data must exist (SIGMA_DE database)
# Run in Snowflake:
# SELECT COUNT(*) FROM SIGMA_DE.PUBLIC.FACT_TRANSACTIONS;
# Expected: 50

# 2. Install MCP SDK
pip install mcp snowflake-connector-python

# 3. Verify MCP installed
python3 -c "import importlib.metadata; print('MCP version:', importlib.metadata.version('mcp'))"
# Expected: MCP version: 1.x.x
```

---

## 🏗️ MILESTONE 1 — Scaffold the MCP Server

**What we're doing:** Creating the basic server shell.
Confirms the MCP SDK is working before we add any tools.

### File: `sigma_mcp_server.py`

Test scaffold imports cleanly:
```bash
python3 -c "import sigma_mcp_server; print('Server scaffold OK')"
```

**✔ Expected:**
```
[SigmaMCPServer] Server module loaded. Waiting for client connection...
Server scaffold OK
```

---

## 🏗️ MILESTONE 2 — Register 3 Tools on the Server

**What we're doing:** Telling the MCP server what tools it exposes.

The `@app.list_tools()` decorator handles the client's question:
*"What tools do you have?"*

The `@app.call_tool()` decorator handles:
*"Run this tool with these arguments."*

### The 3 Tools:

| Tool | SQL it runs | When Nova calls it |
|------|------------|-------------------|
| `get_row_count` | `SELECT COUNT(*) FROM <table>` | "How many rows in X?" |
| `run_sql` | Any custom SELECT Nova writes | Complex analysis questions |
| `get_merchant_summary` | JOIN FACT_TRANSACTIONS + DIM_MERCHANT | "Give me merchant performance" |

> See `sigma_mcp_server.py` for full implementation.

---

## 🏗️ MILESTONE 3 — Build the MCP Client

**What we're doing:** Writing the Python client that:
1. Starts the MCP server as a subprocess
2. Asks it "what tools do you have?"
3. Converts those tools to Bedrock format
4. Sends questions to Nova Lite with those tools
5. Routes Nova's tool requests → through MCP → to Snowflake

### The Key Difference from Lab 1:

```
Lab 1:
  Nova requests tool → Your script runs the Python function directly

Lab 2:
  Nova requests tool → MCP Client asks MCP Server → Server runs Snowflake
```

> See `sigma_nova_mcp.py` for full implementation.

---

## 🚀 How to Run

```bash
# The client starts the server automatically as a subprocess
python3 sigma_nova_mcp.py
```

**✔ Expected output:**
```
============================================================
QUESTION: How many rows are in FACT_TRANSACTIONS?
============================================================
[MCP] Connected. 3 tools available.
[Nova] Requesting tool: get_row_count
[Nova] Arguments: {"table_name": "FACT_TRANSACTIONS"}
[MCP] Result: FACT_TRANSACTIONS contains 50 rows.
NOVA ANSWER: The FACT_TRANSACTIONS table currently contains 50 rows.

============================================================
QUESTION: Which payment method has the most failed transactions?
============================================================
[MCP] Connected. 3 tools available.
[Nova] Requesting tool: run_sql
[MCP] Result: DEBIT_CARD | 6
NOVA ANSWER: DEBIT_CARD has the most failed transactions with 6 failures.
```

---

## 📁 Files in This Folder

```
lab2_mcp_server/
├── README.md               ← This file — full walkthrough
├── sigma_mcp_server.py     ← The MCP server (Milestones 1 + 2)
└── sigma_nova_mcp.py       ← The MCP client + Nova Lite (Milestone 3)
```

---

## 🌟 Stretch Goals

### Option 1 — Make it Interactive
Replace the hardcoded questions with a live input loop:
```python
while True:
    q = input("Ask a question (or 'quit'): ")
    if q == "quit": break
    await ask_with_mcp(q)
```

### Option 2 — Add a Security Layer (4th tool + allow-list)
```
Add tool: get_table_schema → returns column names and data types
Add allow-list to run_sql → reject queries on tables not in whitelist
```
This is how production data teams secure AI tool access.
The MCP server becomes a **policy enforcement point**.

---

## 📚 Key Concepts Learned

| Concept | Lab 1 | Lab 2 (MCP) |
|---------|-------|------------|
| Tool definitions | Hardcoded JSON in script | `@app.list_tools()` decorator on server |
| Tool execution | Python function in script | `@app.call_tool()` on server |
| Credentials | In every script | Only in the server |
| Scalability | Copy-paste per team | One server, all teams connect |
| Transport | Direct Bedrock API | stdio (process I/O) |

---

## 🏭 Enterprise Note

In production, the MCP server runs as a persistent HTTPS service:

| Lab | Enterprise |
|-----|-----------|
| stdio (process I/O) | HTTPS / SSE transport |
| Credentials hardcoded | AWS Secrets Manager |
| Single user, local | Multi-tenant, authenticated |
| Run manually | Always-on, auto-scaled |
| One MCP server | Dozens (one per domain team) |

The tool definitions and execution logic stay **exactly the same**.
Only the transport and deployment changes.
