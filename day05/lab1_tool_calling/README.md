# 🔧 LAB 1 — Tool Calling with Amazon Nova Lite
**Day 5 | GenAI for Data Engineering | Sigma DataTech Training**

---

## 🎯 Mission Brief

FROM: Priya Nair, Head of Data — Sigma DataTech  
SUBJECT: Automated Table Health Monitor — URGENT

> Our fraud detection team manually runs row-count queries every morning and pastes results into Slack. This takes 30 minutes and is error-prone.  
> **Build an AI assistant that a non-technical analyst can query in plain English and get live Snowflake answers.**

---

## 🧠 How Tool Calling Works (Read This First)

The LLM does NOT run code. Here is the actual round-trip:

```
Step 1 — You → Nova Lite:
         "How many rows in FACT_TRANSACTIONS?"
         + here are the tools you can use (JSON schema)

Step 2 — Nova Lite → You:
         "I need to call get_row_count(table_name=FACT_TRANSACTIONS)"
         (This is NOT an answer — it's a REQUEST to your Python code)

Step 3 — Your code → Snowflake:
         SELECT COUNT(*) FROM FACT_TRANSACTIONS → 50

Step 4 — Your code → Nova Lite:
         "The tool returned: 50 rows"

Step 5 — Nova Lite → You:
         "FACT_TRANSACTIONS currently has 50 rows."
```

> ⚠️ **Key insight**: Two Bedrock API calls per question — not one.
> - Call 1: Question + tools → Nova asks for a tool
> - Call 2: Tool result → Nova gives the final natural language answer

---

## ✅ Pre-Flight Checks

```bash
# 1. Python version (need 3.10+)
python3 --version

# 2. AWS credentials
aws sts get-caller-identity
# Expected: JSON with Account ID and UserId

# 3. Nova Lite on Bedrock (us-east-1)
aws bedrock list-foundation-models --region us-east-1 \
  --query "modelSummaries[?contains(modelId,'nova-lite')].[modelId]" \
  --output table
# Expected: amazon.nova-lite-v1:0 in the list

# 4. Install packages
pip install boto3 snowflake-connector-python

# 5. Quick Bedrock test
python3 preflight.py
# Expected: "Bedrock is working"
```

---

## 🏗️ MILESTONE 1 — Sample Data in Snowflake

**What we're doing:** Creating `SIGMA_DE` database with two tables:
- `FACT_TRANSACTIONS` — 50 rows of payment data (the core table)
- `DIM_MERCHANT` — 5 merchants (Swiggy, Flipkart, etc.)

> ⚠️ This is a **NEW database** (`SIGMA_DE`) — separate from `SIGMA_CATALOGUE` used in the Data Catalogue lab.

### Run this SQL in your Snowflake Worksheet:

```sql
-- Step 1: Create database and schema
CREATE DATABASE IF NOT EXISTS SIGMA_DE;
USE DATABASE SIGMA_DE;
CREATE SCHEMA IF NOT EXISTS PUBLIC;
USE SCHEMA PUBLIC;

-- Step 2: Create transactions table
CREATE OR REPLACE TABLE FACT_TRANSACTIONS (
    TRANSACTION_ID   VARCHAR(50)    NOT NULL,
    AMOUNT           DECIMAL(10,2)  NOT NULL,
    STATUS           VARCHAR(20)    NOT NULL,   -- COMPLETED / FAILED / PENDING
    MERCHANT_ID      VARCHAR(50)    NOT NULL,
    CUSTOMER_ID      VARCHAR(50)    NOT NULL,
    TXN_DATE         DATE           NOT NULL,
    PAYMENT_METHOD   VARCHAR(30)    NOT NULL
);

-- Step 3: Insert 50 rows of sample data
INSERT INTO FACT_TRANSACTIONS VALUES
('TXN001','120.50','COMPLETED','MERCH_001','CUST_001','2024-01-15','UPI'),
('TXN002','45.00','FAILED','MERCH_002','CUST_002','2024-01-15','CREDIT_CARD'),
('TXN003','890.00','COMPLETED','MERCH_003','CUST_003','2024-01-16','DEBIT_CARD'),
('TXN004','23.75','PENDING','MERCH_001','CUST_004','2024-01-16','UPI'),
('TXN005','567.00','COMPLETED','MERCH_004','CUST_005','2024-01-17','CREDIT_CARD'),
('TXN006','12.00','FAILED','MERCH_005','CUST_006','2024-01-17','DEBIT_CARD'),
('TXN007','340.00','COMPLETED','MERCH_002','CUST_007','2024-01-18','UPI'),
('TXN008','89.99','COMPLETED','MERCH_001','CUST_008','2024-01-18','CREDIT_CARD'),
('TXN009','450.00','FAILED','MERCH_003','CUST_009','2024-01-19','DEBIT_CARD'),
('TXN010','67.50','COMPLETED','MERCH_004','CUST_010','2024-01-19','UPI'),
('TXN011','230.00','PENDING','MERCH_005','CUST_011','2024-01-20','CREDIT_CARD'),
('TXN012','178.25','COMPLETED','MERCH_001','CUST_012','2024-01-20','DEBIT_CARD'),
('TXN013','95.00','FAILED','MERCH_002','CUST_013','2024-01-21','UPI'),
('TXN014','412.00','COMPLETED','MERCH_003','CUST_014','2024-01-21','CREDIT_CARD'),
('TXN015','56.00','COMPLETED','MERCH_004','CUST_015','2024-01-22','DEBIT_CARD'),
('TXN016','789.00','FAILED','MERCH_005','CUST_016','2024-01-22','UPI'),
('TXN017','34.50','COMPLETED','MERCH_001','CUST_017','2024-01-23','CREDIT_CARD'),
('TXN018','123.00','COMPLETED','MERCH_002','CUST_018','2024-01-23','DEBIT_CARD'),
('TXN019','267.75','PENDING','MERCH_003','CUST_019','2024-01-24','UPI'),
('TXN020','543.00','COMPLETED','MERCH_004','CUST_020','2024-01-24','CREDIT_CARD'),
('TXN021','88.00','FAILED','MERCH_005','CUST_021','2024-01-25','DEBIT_CARD'),
('TXN022','156.50','COMPLETED','MERCH_001','CUST_022','2024-01-25','UPI'),
('TXN023','390.00','COMPLETED','MERCH_002','CUST_023','2024-01-26','CREDIT_CARD'),
('TXN024','45.25','FAILED','MERCH_003','CUST_024','2024-01-26','DEBIT_CARD'),
('TXN025','678.00','COMPLETED','MERCH_004','CUST_025','2024-01-27','UPI'),
('TXN026','102.00','PENDING','MERCH_005','CUST_026','2024-01-27','CREDIT_CARD'),
('TXN027','215.75','COMPLETED','MERCH_001','CUST_027','2024-01-28','DEBIT_CARD'),
('TXN028','489.00','COMPLETED','MERCH_002','CUST_028','2024-01-28','UPI'),
('TXN029','67.00','FAILED','MERCH_003','CUST_029','2024-01-29','CREDIT_CARD'),
('TXN030','334.50','COMPLETED','MERCH_004','CUST_030','2024-01-29','DEBIT_CARD'),
('TXN031','91.25','COMPLETED','MERCH_005','CUST_031','2024-01-30','UPI'),
('TXN032','567.00','PENDING','MERCH_001','CUST_032','2024-01-30','CREDIT_CARD'),
('TXN033','23.00','FAILED','MERCH_002','CUST_033','2024-01-31','DEBIT_CARD'),
('TXN034','445.75','COMPLETED','MERCH_003','CUST_034','2024-01-31','UPI'),
('TXN035','189.00','COMPLETED','MERCH_004','CUST_035','2024-01-15','CREDIT_CARD'),
('TXN036','78.50','FAILED','MERCH_005','CUST_036','2024-01-16','DEBIT_CARD'),
('TXN037','312.00','COMPLETED','MERCH_001','CUST_037','2024-01-17','UPI'),
('TXN038','654.25','COMPLETED','MERCH_002','CUST_038','2024-01-18','CREDIT_CARD'),
('TXN039','43.00','PENDING','MERCH_003','CUST_039','2024-01-19','DEBIT_CARD'),
('TXN040','891.50','COMPLETED','MERCH_004','CUST_040','2024-01-20','UPI'),
('TXN041','167.00','FAILED','MERCH_005','CUST_041','2024-01-21','CREDIT_CARD'),
('TXN042','298.75','COMPLETED','MERCH_001','CUST_042','2024-01-22','DEBIT_CARD'),
('TXN043','52.00','FAILED','MERCH_004','CUST_037','2024-01-29','CREDIT_CARD'),
('TXN044','380.00','COMPLETED','MERCH_002','CUST_038','2024-01-29','DEBIT_CARD'),
('TXN045','19.99','PENDING','MERCH_001','CUST_039','2024-01-30','UPI'),
('TXN046','725.00','COMPLETED','MERCH_005','CUST_040','2024-01-30','CREDIT_CARD'),
('TXN047','36.00','FAILED','MERCH_003','CUST_041','2024-01-30','DEBIT_CARD'),
('TXN048','255.50','COMPLETED','MERCH_004','CUST_042','2024-01-31','UPI'),
('TXN049','142.00','COMPLETED','MERCH_002','CUST_043','2024-01-31','CREDIT_CARD'),
('TXN050','78.25','FAILED','MERCH_001','CUST_044','2024-01-31','DEBIT_CARD');

-- Step 4: Create merchants table
CREATE OR REPLACE TABLE DIM_MERCHANT (
    MERCHANT_ID    VARCHAR(50)  NOT NULL,
    MERCHANT_NAME  VARCHAR(100) NOT NULL,
    CATEGORY       VARCHAR(50)  NOT NULL,
    CITY           VARCHAR(50)  NOT NULL
);

INSERT INTO DIM_MERCHANT VALUES
('MERCH_001','Swiggy','Food Delivery','Bengaluru'),
('MERCH_002','Flipkart','E-Commerce','Bengaluru'),
('MERCH_003','BookMyShow','Entertainment','Mumbai'),
('MERCH_004','MakeMyTrip','Travel','Gurugram'),
('MERCH_005','Zepto','Grocery Delivery','Mumbai');

-- Step 5: Verify
SELECT 'FACT_TRANSACTIONS' AS table_name, COUNT(*) AS row_count FROM FACT_TRANSACTIONS
UNION ALL
SELECT 'DIM_MERCHANT', COUNT(*) FROM DIM_MERCHANT;
```

**✔ Expected verification output:**
```
TABLE_NAME          ROW_COUNT
FACT_TRANSACTIONS   50
DIM_MERCHANT        5
```

---

## 🏗️ MILESTONE 2 — Define Tool Schemas

**What we're doing:** Writing the JSON descriptions that tell Nova Lite what tools
exist and when to use them. Think of this as the "API documentation" the LLM reads.

**Why this matters:**
- `name` → what Nova Lite says when it wants to call the tool
- `description` → HOW Nova decides when to call it — write this carefully, vague = wrong tool
- `inputSchema` → what arguments Nova passes to your code

> See `lab1_tool_calling.py` — TOOLS section.

---

## 🏗️ MILESTONE 3 — Build Tool Executor Functions

**What we're doing:** The actual Python functions that run the SQL on Snowflake.
Nova Lite *requests* a tool → your Python code *executes* it → returns result as a string.

**Why strings?** Nova Lite expects text results. Even if the answer is a number, return it
as a formatted string like `"FACT_TRANSACTIONS has 50 rows."` — that's what Nova uses
to compose its final answer.

> See `lab1_tool_calling.py` — TOOL EXECUTOR FUNCTIONS section.

---

## 🏗️ MILESTONE 4 — Wire the Full Conversation Loop

**What we're doing:** The complete flow:
1. User question → sent to Nova with tool list (Bedrock Call 1)
2. Nova responds with a tool request (NOT an answer yet)
3. Python runs the tool → gets Snowflake result
4. Result sent back to Nova (Bedrock Call 2)
5. Nova composes final natural language answer

> See `lab1_tool_calling.py` — ask_nova() function.

---

## 🚀 How to Run

```bash
python3 lab1_tool_calling.py
```

**Expected output:**
```
============================================================
QUESTION: How many rows are in FACT_TRANSACTIONS?
============================================================
[Snowflake] Running: SELECT COUNT(*) FROM FACT_TRANSACTIONS
[Snowflake] Result: FACT_TRANSACTIONS has 50 rows.
[Nova] Requesting tool: get_row_count
NOVA ANSWER: FACT_TRANSACTIONS currently has 50 rows.

============================================================
QUESTION: How many transactions failed?
============================================================
[Nova] Requesting tool: get_status_count
NOVA ANSWER: There are X failed transactions in FACT_TRANSACTIONS.
```

---

## 📁 Files in This Folder

```
lab1_tool_calling/
├── README.md               ← This file — full walkthrough
├── preflight.py            ← Bedrock connection test
└── lab1_tool_calling.py    ← Main script (Milestones 2, 3, 4)
```

---

## 📚 Key Concepts Learned

| Concept | What it means |
|---------|--------------|
| Tool Calling | LLM decides WHAT to ask, Python decides HOW to do it |
| Two-call pattern | Call 1 = get tool request, Call 2 = get final answer |
| Tool schema | JSON description the LLM reads to know available tools |
| Tool executor | Python function that actually runs the SQL |
| Bedrock Converse API | AWS API for multi-turn LLM conversations with tools |
