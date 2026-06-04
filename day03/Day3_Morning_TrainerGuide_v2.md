# Error:  Please run /login · API Error: 403 Model access is denied due to INVALID\_PAYMENT\_INSTRUMENT:A valid payment instrument must be provided.. Your AWS Marketplace subscription for this model cannot be 

#      completed at this time. If you recently fixed this issue, try again after 2 minutes.

#   Day 3 — Coding Assistants: Morning Session (11:00–13:00)

**Trainer Guide \+ Student Handout | Sigma Intelligence Bootcamp**

Format: Trainer demos → Students follow on their laptops All tools free or use existing AWS credits. No Claude Pro needed for students.

---

## Bedrock Model Reference — Claude Code `settings.json`

Use this table to choose which model to set in `~/.claude/settings.json` under `ANTHROPIC_MODEL`.

```json
{
  "env": {
    "CLAUDE_CODE_USE_BEDROCK": "1",
    "AWS_REGION": "us-east-1",
    "ANTHROPIC_MODEL": "<paste model ID from table below>"
  }
}
```

| Model | Model ID for settings.json | Input $/1M | Output $/1M | Best for |
| :---- | :---- | :---- | :---- | :---- |
| Amazon Nova Micro | `us.amazon.nova-micro-v1:0` | $0.035 | $0.14 | Simple Q\&A, summaries |
| Amazon Nova Lite | `us.amazon.nova-lite-v1:0` | $0.06 | $0.24 | Code gen, DE tasks |
| Amazon Nova Pro | `us.amazon.nova-pro-v1:0` | $0.80 | $3.20 | Complex reasoning, low-cost alternative to Sonnet |
| Claude Haiku 4.5 ✅ | `us.anthropic.claude-haiku-4-5-20251001-v1:0` | $0.80 | $4.00 | Code generation — **default for students** |
| Claude Sonnet 4.5 | `us.anthropic.claude-sonnet-4-5-20251001-v1:0` | $3.00 | $15.00 | Best Claude quality — use sparingly |

⚠️ **Verify Sonnet ID in Bedrock Console before use:** AWS Console → Bedrock → Model catalog → Claude Sonnet → copy inference profile ID. The `us.` prefix and date suffix can differ from the table above.

💡 **Recommendation for students:** Start with **Nova Lite** (cheapest for code tasks). Switch to **Haiku 4.5** if output quality is insufficient. Avoid Sonnet unless necessary.

---

## 11:00–11:15 | The Shift: From Browser Tab to Inside Your Editor

**Concept (1 min):** Days 1–2: You copied code from AI into your editor manually. From today: AI lives inside your editor. It reads your files. You never copy-paste again.

**The 3 tools we cover today:**

| Tool | Where it lives | Best for |
| :---- | :---- | :---- |
| Claude Code CLI | Terminal | Multi-file tasks, run tests, git ops |
| Gemini CLI | Terminal | Free alternative, same concept |
| Cursor IDE | Full editor | Multi-file context, understand any codebase |

---

## 11:15–11:45 | Claude Code CLI (Everyone Does This)

✅ Students can run this using their AWS Bedrock credits — no Claude Pro needed.

**What it is (1 line):** A terminal agent that reads your entire project, writes files, runs tests — all from one prompt.

**Step 1 — Install (everyone):**

# Install Node

brew install node

```shell
npm install -g @anthropic-ai/claude-code
claude --version
```

## Alternatively

# Install Homebrew (if not present)

/bin/bash \-c "$(curl \-fsSL [https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh](https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh))"

# Now install Claude Code

## sudo npm install \-g @anthropic-ai/claude-code

**Step 2 — Configure Bedrock (one-time setup):**

**Open the folder where claude is installed**  
\-\> finder \-\> user(AS-mac-1346) \-\> press cmd \+ shift \+ . (Shows hidden files)  
Go to .claude and open terminal  
	Open a terminal and enter the commands  
	\-\>  cd \~/.claude  
	\-\>  touch settings.json (create the settings file)  
	\-\>  now go to the .claude folder and open the file in vs code and paste the below code and save it

```json
{
  "env": {
    "CLAUDE_CODE_USE_BEDROCK": "1",
    "AWS_REGION": "us-east-1",
    "ANTHROPIC_MODEL": "us.anthropic.claude-haiku-4-5-20251001-v1:0"
  }
}
```

If the file already has content, add only the `env` block — do not overwrite. AWS credentials come from your existing `aws configure` setup. No API key needed.  
At the same time go to your AWS account \-\> IAM \-\> Create User \-\> create \-\> nameit \-\> attach policy directly \-\> attach policies (athena full access, glue full access, lambda full access, S3 full access, bedrock full access, EC2 full access, cloudWatch full Access)  
Review and create it

Go to the IAM user \-\> security credentials \-\> create access key \-\> other-\> name it \-\> create  
Now copy the aws key and the secret key and keep it somewhere safe like notes , it will not be seen again

**Step 3 — Start a session:**  
Now create a folder where you want to work today (eg: in desktop)

```shell
cd your-project-folder
aws configure #(enter the aws key and secret key)
claude #(enter as shown)
```

**Demo prompts to show students (pick 2):**

```
# Demo 1 — Init any project
/init
```

Watch Claude read the folder and write CLAUDE.md automatically.

```
# Demo 2 — Generate a validator function with tests
Write a Python function validate_orders(df) that checks:
- no null order_ids
- amount must be positive
- created_at must be a valid date
Include 4 pytest cases. Follow PEP8.
```

```
# Demo 3 — Debug with full context
Airflow DAG failed with this error: [paste any error log]
Read the DAG file and fix the root cause.
```

**Key point to tell students:**

"CLAUDE.md is your standing brief. Write your stack, conventions, constraints once. Every session reads it. You never repeat yourself."

---

## 11:45–12:15 | Gemini CLI (Students Do This Themselves)

**What it is (1 line):** Google's free terminal AI agent. Same concept as Claude Code. Works without paid subscription.

**Install:**

```shell
npm install -g @google/gemini-cli
```

**Authenticate (free Google account):**

```shell
gemini
# Browser opens → sign in with Google account → done
```

**First prompt — let students try:**

```
Explain what this Python function does and suggest one improvement:

def proc(df):
    df2 = df.dropna()
    df3 = df2[df2['amt'] > 0]
    return df3
```

**Second prompt — DE flavour:**

```
I am a data engineer at a fintech company.
Write a Python function that reads a CSV from S3 using boto3,
validates that columns order_id, customer_id, amount exist,
and returns a pandas DataFrame. Add error handling and logging.
```

**Discuss with class:**

- Same output quality as Claude Code for simple tasks?  
- What's different about the response style?  
- When would you pick Gemini CLI over Claude Code?

---

## 12:15–12:40 | Cursor IDE (Students Install and Try)

**What it is (1 line):** VS Code — but AI is built into the architecture, not added as a plugin. It indexes your entire codebase so you can ask questions across all files at once.

**Install:**

```
cursor.com → Download → Install → Import VS Code settings (say Yes)
Sign in with GitHub or email → Free tier: 500 requests/month
```

**Create .cursorrules in your project root:**

```
You are a Data Engineering assistant for Sigma Intelligence (fintech startup).
Python 3.10+. Always use type hints. Use logging not print().
Follow existing code patterns. Every new function needs a docstring and 3 pytests.
```

**3 things to try right now:**

**1\. Inline edit (Ctrl+K):** Select any function → Ctrl+K → type:

```
Add input validation and logging to this function
```

**2\. Chat with codebase (Ctrl+L):**

```
@codebase What does this project do? What are the main files?
```

**3\. Multi-file edit (Ctrl+Shift+I — Composer):**

```
Add a processed_at timestamp column to every function
that writes a DataFrame to S3. Show me each change before applying.
```

**Key point:**

"Copilot sees one file. Cursor sees your whole project. Use Cursor when your task touches more than 2 files."

---

## 12:40–12:50 | CoWork \+ Windsurf — 2-Min Intros

**CoWork (Anthropic):**

- Not a code editor. It's a desktop agent that controls your browser and terminal.  
- DE use case: automate repetitive AWS Console clicks, schedule health checks.  
- Status: Beta. We use it in Week 3\.

**Windsurf:**

- Full IDE like Cursor, built on VS Code.  
- Powered by Codeium (not Claude/GPT).  
- Free tier more generous than Cursor (no request limit on basic).  
- Use it if you hit Cursor's 500 request limit.  
- Download: windsurf.com

Quick show: open windsurf.com on screen.

---

## 12:50–13:00 | Effective Prompting Inside IDEs

**5 rules — write these down:**

**Rule 1 — Name your stack explicitly**

```
# Bad
Write a function to read the orders table

# Good
Write a Python 3.10 function using snowflake-connector-python
to read sigma.orders. Return a pandas DataFrame.
Handle connection timeout with 3 retries.
```

**Rule 2 — Reference your own code**

```
# Bad
Write a new Airflow DAG

# Good
Write a new Airflow DAG following the same retry logic
and Slack alert hooks as customer_pipeline.py
```

**Rule 3 — Set scope boundaries**

```
# Bad
Fix the bug

# Good
Fix the null check in validate_order() only.
Do not change any other function or the function signature.
```

**Rule 4 — Always ask for tests**

```
Write clean_orders() AND a pytest with:
happy path, all-null order_id column, negative amount values.
```

**Rule 5 — Prompt-Driven TDD** Step 1 → Write the test first (describe the contract) Step 2 → Ask AI to write code that passes the tests Step 3 → Run tests, paste failures back, ask AI to fix

```
# Step 1 — Ask for tests first
Write a pytest for validate_nulls(df, required_cols).
Tests needed:
- 4% nulls → should pass
- 6% nulls → should raise ValueError
- empty DataFrame → should raise ValueError
- missing column name → should raise KeyError

# Step 2 — Then ask for implementation
Now write validate_nulls() so all 4 tests pass.
Add type hints and docstring.
```

Key insight: "Tests define the contract. Code implements it. AI writes both. You review both. Bugs surface before review — not in production."

---

## 13:00 | Lunch Break

**Homework for after lunch:** Students should have Gemini CLI working and Cursor installed before 14:30.

---

*Next: 14:30 — Vibe Coding for Data Engineering \+ Sigma Pipeline Forge*  
