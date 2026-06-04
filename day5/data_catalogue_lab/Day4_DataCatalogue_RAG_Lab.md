# 🔍 Mission: Compliance Command Centre
## Day 4 Lab 2 — Data Catalogue RAG with FAISS
**Sigma Intelligence Bootcamp · 22 May 2026 | Post-lunch session**

---

## 🚨 SITUATION BRIEF

> **13:02 IST. Message from CISO Radhika Menon (Slack #engineering-alerts):**
>
> *"Surprise RBI + GDPR joint audit kicks off at 14:00 today. Auditors want to query  
> our data catalogue live — in natural language. Our 'catalogue' is a Snowflake database  
> that nobody touched since Q4. I need an AI system that answers  
> compliance questions in real time. Build it before lunch ends.*
>
> *First question they'll ask: **'Which of your tables contain customer PII?'**  
> Second: **'What data was modified in the last 7 days?'**  
> The auditors are not forgiving. Neither am I."*

**What is this about?**
RBI (Reserve Bank of India) can walk into any fintech company and ask: *"Show us which databases store customer personal data."* If you can't answer in minutes — you fail the audit and face heavy fines. Your job today: build an AI tool that answers this instantly.

**PII = Personally Identifiable Information** — any data that can identify a specific person. Examples: name, phone number, Aadhaar number, PAN card, email address. Companies must protect this data carefully by law.

---

## 🏆 Mission Scoring (90 pts)

| # | Mission | Points | You prove it by… |
|---|---------|--------|-----------------|
| 🔴 | **Mission 1 — Build the Arsenal** | 30 | FAISS index built from Snowflake, smoke-test output screenshot |
| 🟡 | **Mission 2 — Run the Investigations** | 30 | Both required queries return correct results |
| 🟢 | **Mission 3 — Command Centre Live** | 30 | Streamlit app running, results color-coded |

**Rule:** No skipping. Screenshot every milestone. Screenshots = points.

**Easter Egg (+5):** There's something hidden in the catalogue that even the CISO doesn't know about. Find it and tell the trainer before anyone else.

## HOW TO SUBMIT PROOF AT EVERY STAGE - Create a Google document with the name - <YOURNAME_Datacataloguelab> in Google Drive (GenAI - Results - Day5) and keep saving each mission results (Copy past if text or screenshot if web page)

---

## 🛫 Pre-Flight Check

Run all checks before touching any code. Fix failures before proceeding.

```bash
# 1. Python version
python3 --version
# Need: 3.10 or higher

# 2. Install all dependencies
pip install langchain langchain-community langchain-aws langchain-ollama langchain-core faiss-cpu streamlit boto3 snowflake-connector-python

# 3. Ollama running and embedding model ready
ollama list
# Need: nomic-embed-text listed. If not: ollama pull nomic-embed-text

# 4. Snowflake connection test (after Step 1 below)
python3 snowflake_catalog.py
# Need: "✅ Snowflake catalogue loaded — 8 tables found."
```

**#IMPORTANT — QUICKLY GLANCE THE TABLES AND NOTE THE CONTENT (THIS IS IMPORTANT FOR DE ROLE)**

---

## ❄️ Step 1: Create Your Snowflake Tables (10 mins)

Think of this as setting up the filing cabinet before the auditor arrives.

You will create 8 Sigma DataTech tables in Snowflake. Each table has a description (stored in the COMMENT field) — this is what the AI will search later.

### 1a — Open Snowflake Worksheet
Log in to your Snowflake trial account → Worksheets → New Worksheet.

### 1b — Run the Setup SQL
Open `setup_snowflake.sql` from the project folder. Paste the entire file into your Snowflake worksheet and click **Run All**.

### 1c — Verify
The last query in the script should return **8 rows**. Screenshot this.

If you see 0 rows → make sure `SIGMA_CATALOGUE` is selected as your active database at the top of the worksheet.

### 1d — Add Your Credentials
Open `snowflake_catalog.py` and fill in your Snowflake login details:

```python
SNOWFLAKE_CONFIG = {
    "user":      "your_username",
    "password":  "your_password",
    "account":   "abc12345.us-east-1",   # from your trial welcome email
    "warehouse": "COMPUTE_WH",
    "database":  "SIGMA_CATALOGUE",
    "schema":    "PUBLIC",
}
```

**Where to find your account ID:** Snowflake trial welcome email → look for your account URL → copy the part before `.snowflakecomputing.com`.

### 1e — Test the connection

```bash
python3 snowflake_catalog.py
```

Expected output:
```
✅ Snowflake catalogue loaded — 8 tables found.
```

If it fails → recheck your credentials. Do not move forward until this works.

---

## 📁 Project Files

```
data_catalogue_lab/
├── setup_snowflake.sql     ← Run this in Snowflake first
├── snowflake_catalog.py    ← Add your credentials here
├── indexer.py              ← YOUR WORK — 3 gaps to fill
└── app.py                  ← PRE-PROVIDED — runs once indexer.py is complete
```

---

## 🔴 Mission 1: Build the Arsenal (30 pts)

**What you're doing:** Taking the 8 table descriptions from Snowflake and loading them into FAISS so the AI can search them.

Open `indexer.py`. Find and fill the three `[YOUR CODE HERE]` sections.

---

### Gap 1 — `build_documents()`

`snowflake_catalog.py` already fetched your 8 tables and gave them to you as a Python list. But FAISS doesn't understand Python lists directly — it needs each table wrapped in a special format called a `Document`.

**Think of it as:** putting each table description into a standard envelope before dropping it into the AI's inbox.

- `page_content` = the description text → this is what gets searched
- `metadata` = the table's details (name, owner, date) → used for filtering, not searching

```python
def build_documents() -> list[Document]:
    documents = []
    for table in TABLE_CATALOG:
        doc = Document(
            page_content=table["description"],
            metadata={
                "table_name":     table["table_name"],
                "last_updated":   table["last_updated"],
                "classification": table["classification"],
                "domain":         table["domain"],
                "owner":          table["owner"],
            }
        )
        documents.append(doc)
    return documents
```

**Before you type:** Why do we put the description in `page_content` and not the table name?

---

### Gap 2 — `build_index()`

Now you have 8 Documents. This step does two things at once:
1. Converts each description into a vector (a list of numbers that captures meaning)
2. Loads all vectors into FAISS so it can search them instantly

**Think of it as:** scanning all 8 envelopes and sorting them on a smart shelf where similar topics sit next to each other.

```python
def build_index() -> FAISS:
    embeddings = OllamaEmbeddings(model="nomic-embed-text")
    docs = build_documents()
    vectorstore = FAISS.from_documents(docs, embeddings)
    return vectorstore
```

---

### Gap 3 — `search_catalog()`

The shelf is ready. Someone asks a question — this function searches FAISS and returns the top matching tables with scores.

**Score = distance. Lower score = better match.** (0.2 is better than 0.8)

```python
def search_catalog(query: str, vectorstore: FAISS, k: int = 5) -> list:
    results = vectorstore.similarity_search_with_score(query, k=k)
    return results
```

---

### Smoke-Test — Validate Mission 1

```bash
python3 indexer.py
```

**Expected output:**
```
✅ Snowflake catalogue loaded — 8 tables found.
Building FAISS index for Sigma DataTech catalogue...
Index built. Total documents: 8

--- Query: 'Which tables contain customer PII?' ---
  [0.2xxx] customers — PII-Critical
  [0.3xxx] kyc_documents — PII-Critical
  [0.3xxx] fraud_cases — PII-High
  ...

--- Recent tables (last 7 days, metadata filter) ---
  2026-05-22  customers (PII-Critical)
  2026-05-22  transactions (Internal)
  ...
```

📸 **Screenshot this output. This is your Mission 1 ACCOMPLISHED PROOF.**

> 🏁 Once done → click **"Mark Mission 1 Done"** in the Streamlit sidebar.

Open the Streamlit app: `python3 -m streamlit run app.py`

---

## 🟡 Mission 2: Run the Investigations (30 pts)

The auditor has arrived. Run both questions the CISO warned you about.

### Required Query 1

```
"Which tables contain customer PII?"
```

**What to look for:** `customers` and `kyc_documents` must appear at the top (they store Aadhaar, PAN, email — real personal data). `fraud_cases` should also appear. `transactions` and `wallets` should NOT be at the top — they store payment amounts, not personal identity data.

---

### Required Query 2

```
"Show me all tables updated in the last 7 days"
```

⚠️ **Stop and think before you run this:**

FAISS searches the *description text* of each table. It finds tables whose descriptions use words like "recent", "updated", "nightly". It does NOT look at the actual date the table was last changed.

**Team question (discuss and write one sentence answer):**
> Will FAISS correctly return only tables updated in the last 7 days? Why or why not?

Tell the trainer your answer when asked.

Run it. Look at the results. Then click **"Last 7 Days"** button to see what the correct date-filtered answer looks like.

📸 **Screenshot both results. This is your Mission 2 proof.**

> 🏁 Click **"Mark Mission 2 Done"** in the sidebar.

---

## 🟢 Mission 3: Command Centre Live (30 pts)

The Streamlit app is your live dashboard — what you'd actually show the auditor.

```bash
streamlit run app.py
```

Open `http://localhost:8501` in your browser.

**Confirm all of these work:**

- [ ] Red banner at top showing audit countdown
- [ ] 3 tiles showing: PII table count, total tables, recently changed tables
- [ ] Query 1 shows red cards for PII tables, green for safe tables
- [ ] Each card shows: table name, who owns it, when it was last updated
- [ ] Relevance score visible on every card
- [ ] Left sidebar shows mission progress and score

📸 **Screenshot the running app. This is your Mission 3 proof.**

> 🏁 Click **"Mark Mission 3 Done"** in the sidebar.

---

## 🗓️ Explore: Last 7 Days Filter

Click **"Last 7 Days"** button in the app. Then run this in your Snowflake worksheet:

```sql
SELECT TABLE_NAME, LAST_ALTERED
FROM SIGMA_CATALOGUE.INFORMATION_SCHEMA.TABLES
WHERE TABLE_SCHEMA = 'PUBLIC'
  AND LAST_ALTERED >= DATEADD(day, -7, CURRENT_TIMESTAMP())
ORDER BY LAST_ALTERED DESC;
```

**Do the two results match?**

The key lesson: FAISS reads words and finds meaning. It cannot read a date. The app solves this by fetching FAISS results first, then filtering by actual date from Snowflake in Python — two separate steps working together.

📸 **Screenshot the "Last 7 Days" result. Add to your Google Doc.**

---

## ✅ Validation Checklist

```
☐ setup_snowflake.sql ran — 8 rows returned
☐ snowflake_catalog.py prints "✅ Snowflake catalogue loaded — 8 tables found."
☐ python3 indexer.py runs without error, shows 8 documents
☐ Query 1 returns customers, kyc_documents, fraud_cases at the top
☐ Query 2 results and "Last 7 Days" results are different — you know why
☐ Streamlit app shows correct metric tiles and color-coded cards
☐ All 3 missions marked done in the sidebar (score: 90)
☐ You can explain in 30 seconds why FAISS cannot filter by date
```

---

## 🌟 Stretch Goal: Build the Audit Report (Vibe Coding)

The auditor doesn't want to stare at a Streamlit screen — they want a document they can take away.

Add a **"📥 Export Audit Report"** button to `app.py` that generates a text report and lets the auditor download it.

**4 clues to guide you:**

**Clue 1 — Add the button**
In `app.py`, after the Legend section, add:
```python
if st.button("📥 Export Audit Report"):
```

**Clue 2 — Run both searches inside the button**
```python
    pii_hits   = search_catalog("Which tables contain customer PII?", vectorstore, k=6)
    recent_hits = search_recent_tables(vectorstore, days=7)
```

**Clue 3 — Build the report text**
Create a list of lines. Add a header, then loop through `pii_hits` and `recent_hits` to add each table as a line. Join with `"\n"`.
```python
    lines = ["# Sigma DataTech — Audit Report", f"Generated: {datetime.now()}", ""]
    lines.append("## PII Tables")
    for doc, score in pii_hits:
        if "PII" in doc.metadata["classification"]:
            lines.append(f"- {doc.metadata['table_name']} | Owner: {doc.metadata['owner']} | {doc.metadata['classification']}")
    # YOUR CODE: add Section 2 for recent_hits
```

**Clue 4 — Add the download button**
```python
    st.download_button("⬇️ Download Report", "\n".join(lines), file_name="sigma_audit_report.txt")
```

📸 **Screenshot the downloaded report file. Bonus points for Stretch Goal.**

---

*Sigma DataTech is a fictional company. All Snowflake tables are created in your personal trial account for training purposes only.*

**Additional Reading:-**

What's real in today's lab:

1) Snowflake INFORMATION_SCHEMA + COMMENT fields — real companies actually store table descriptions here. Airbnb, Uber, every serious data team does this. It's called a data catalogue.
2) Natural language search over metadata — tools like Atlan, Alation, AWS DataZone, Collibra, DataHub (LinkedIn built it, now open source) do exactly this. You just built a stripped-down version of a $50M product.
3) PII discovery before an audit — this is a real job. Companies hire "Data Governance Engineers" specifically to build and maintain this. RBI and GDPR audits actually happen and they actually ask these questions.
4) FAISS for search — Meta uses it in production at billion-scale. The exact same library.

**Raw FAISS (what we use today):**

a) Search engine only — pure math, finds nearest vectors
b) No metadata store built in
c) No database
d) No disk storage by default — lives in RAM, gone when Python exits

How we handle metadata today:
We store it ourselves inside LangChain's Document object. LangChain wraps FAISS and keeps the metadata alongside the vectors in memory. That's not FAISS doing it — that's LangChain doing it on top of FAISS.

**Enterprise FAISS (Meta's production setup):**

Meta runs FAISS at billion-scale but they built their own storage layer around it — a separate database stores the metadata, a separate system handles persistence. FAISS still just does the search part.