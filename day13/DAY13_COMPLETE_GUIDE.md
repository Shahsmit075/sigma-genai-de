# Day 13 — Data Lineage, Governance & Cataloguing Complete Guide
## Focus: Mystery B (On-Demand Delivery Domain)

---

## 0. TL;DR (Too Long; Didn't Read)
In this lab, you are handed an undocumented dbt project representing a database schema from an unknown company. By analyzing the columns, SQL joins, and schemas, you will discover that **Mystery B** represents a two-sided gig economy food and grocery delivery platform (similar to Swiggy, Zomato, or UberEats) connecting users, outlets, and riders. You will run a Lineage and Governance Agent on AWS Bedrock to automatically scan the SQL files, deduce the industry, classify PII data, map column-level lineage, and recommend data access permissions. The lab tests the boundaries between AI speed and human domain expertise—specifically highlighting cases where AI fails to recognize local context, such as corporate tax IDs (GST) leaking personal tax IDs (PAN), or food licenses (FSSAI) carrying regulatory risk.

---

## 1. Mystery B Domain: The Layman's Explanation
**Mystery B** is a data warehouse representing a **food and on-demand grocery delivery platform** (think Swiggy, Zomato, or Zepto). 

### How the Business Works:
The company acts as a coordinator between three major groups:
1.  **Customers (Users):** Order food or groceries, pay platform fees, and get orders delivered to their home or office.
2.  **Outlets (Restaurants/Merchants):** Prepare the orders, pay commissions to the platform, and provide menus/ratings.
3.  **Riders (Delivery Agents):** Pick up orders from outlets, navigate using GPS coordinates, and deliver them to customers.

### The Data Landscape:
To keep this service running, the platform collects highly sensitive data. It tracks exactly where customers live and work using GPS lat/long coordinates, retains riders' driver's license numbers for verification, holds rider bank account numbers for payouts, and records food hygiene licenses (FSSAI) for restaurant compliance.

---

## 2. Mystery B Database Schema & Column Dictionary
The dbt project contains 8 files. Here is the structural breakdown of each model:

```
                  ┌─────────────────┐
                  │   stg_ratings   │
                  └────────┬────────┘
                           │ Left Join
┌────────────┐   ┌─────────▼────────┐   ┌─────────────┐
│ stg_users  ├──>│   stg_orders     │<──┤ stg_riders  │
└─────┬──────┘   └────────┬─────────┘   └─────────────┘
      │                   │ Join
      │ Left Join         ▼
┌─────▼──────┐   ┌──────────────────┐
│  dim_users │   │  fct_deliveries  │
└────────────┘   └──────────────────┘
```

### Staging Tables (Raw Layer)
*   **[stg_users.sql](file:///Users/as-mac-1320/Downloads/gen-ai-github/sigma-genai-de/day13/lab/mystery_b/stg_users.sql):** Raw customer records. Contains `full_name`, `registered_email`, `mobile_number`, physical home and office addresses with exact GPS coordinates (`home_lat`, `home_lng`, `office_lat`, `office_lng`), `date_of_birth`, `device_id`, and `wallet_balance`.
*   **[stg_riders.sql](file:///Users/as-mac-1320/Downloads/gen-ai-github/sigma-genai-de/day13/lab/mystery_b/stg_riders.sql):** Gig worker onboarding records. Contains `full_name`, contacts, `dl_number` (Driver's License), `dl_expiry_date`, `vehicle_number`, `bank_account_number`, `ifsc_code`, `home_address`, `background_check_status`, and real-time location metrics (`current_lat`, `current_lng`).
*   **[stg_outlets.sql](file:///Users/as-mac-1320/Downloads/gen-ai-github/sigma-genai-de/day13/lab/mystery_b/stg_outlets.sql):** Restaurant/Merchant data. Contains `outlet_name`, owner PII (mobile/email), coordinates, business listings, and critical registration numbers: `fssai_number` (Food Safety Licence) and `gst_number` (Merchant Tax ID).
*   **[stg_orders.sql](file:///Users/as-mac-1320/Downloads/gen-ai-github/sigma-genai-de/day13/lab/mystery_b/stg_orders.sql):** Transactional ledger. Tracks order status, delivery address, drop coordinates, fee structures, payment methods, and verification hashes (`otp_verified`).
*   **[stg_ratings.sql](file:///Users/as-mac-1320/Downloads/gen-ai-github/sigma-genai-de/day13/lab/mystery_b/stg_ratings.sql):** Double-sided feedback logging customer scores for food and rider quality, along with rider reviews of customers.

### Analytics & Dimension Tables (Refined Layer)
*   **[int_user_behaviour.sql](file:///Users/as-mac-1320/Downloads/gen-ai-github/sigma-genai-de/day13/lab/mystery_b/int_user_behaviour.sql):** Intermediary model grouping orders to calculate user metrics (average order value, cancel frequencies, preferred payment methods, and ratings).
*   **[dim_users.sql](file:///Users/as-mac-1320/Downloads/gen-ai-github/sigma-genai-de/day13/lab/mystery_b/dim_users.sql):** Analytical user view. **Crucially, raw location details are excluded.** Email and phone numbers are cryptographically masked using `SHA2(..., 256)`.
*   **[fct_deliveries.sql](file:///Users/as-mac-1320/Downloads/gen-ai-github/sigma-genai-de/day13/lab/mystery_b/fct_deliveries.sql):** Master operations table logging fulfillment durations, payments, surge rates, and scores.

---

## 3. Terminal Execution: Prompt Answers
When you execute Step 1, the script will halt and prompt you for manual inputs. Copy and paste the exact answers below:

```bash
# Command to run Step 1 (Mystery B):
python lab/lineage_agent.py --lab 1 --mystery lab/mystery_b/
```

### Prompt 1:
`What industry do you think this is?`
> **Copy-Paste Answer:** `Food & On-Demand Delivery Platform (Zomato/Swiggy/UberEats style)`

### Prompt 2:
`Name 3 columns you think are most sensitive:`
> **Copy-Paste Answer:** `stg_riders.bank_account_number, stg_riders.dl_number, stg_users.home_lat`

### Prompt 3:
`Which table would a hacker target first?`
> **Copy-Paste Answer:** `stg_users` (contains raw GPS tracking, home addresses, phone numbers, and emails) or `stg_riders` (contains cleartext banking and license numbers).

---

## 4. The 3 Governance Questions: Model Answers
In Phase 3, the agent uses its catalog to answer three core questions. Below are the model answers you will see in the output catalog and should prepare for debate:

### Q1: Most Damaging Column
*   **Target Column:** `stg_users.home_lat` (coupled with `stg_users.home_lng`)
*   **Why:** Leaking GPS coordinates alongside user IDs exposes customers to physical safety and tracking risks. Unlike credit card numbers or passwords, physical home coordinates cannot be rotated or changed. A malicious actor could map user habits, determine wealth indexes based on home locations, and coordinate physical stalking or targeted crimes.

### Q2: Hacker Target Table
*   **Target Table:** `stg_riders`
*   **Why:** A hacker targeting `stg_riders` gains immediate read access to cleartext financial details (`bank_account_number`, `ifsc_code`) and government identities (`dl_number`). This data can be sold to run financial redirect fraud or identity theft rings targeting independent gig workers.
*   **Damage Estimate:** `Catastrophic` (results in massive regulatory fines, class-action lawsuits, driver onboarding bans, and damage to brand reputation).

### Q3: Europe Expansion (GDPR Compliance)
*   **Columns Needing Consent:** 
    1.  `stg_users.home_lat` & `stg_users.home_lng` (Precise location tracking data under GDPR Article 4)
    2.  `stg_users.date_of_birth` (Profiling data requiring legal basis)
    3.  `stg_ratings.user_comment` (Unstructured comments that may contain free-form sensitive health or political information)
*   **Why:** Location tracking is subject to strict consent mechanisms under GDPR. The user must be able to opt-out and invoke the "Right to be Forgotten" (deletion of historic location tracking files) without losing core app accessibility.
*   **Columns Already Compliant:** 
    *   `dim_users.email_hash` and `dim_users.phone_hash`. These are hashed using `SHA2(..., 256)`. Because they are pseudonymized, they conform to GDPR's recommendation (Article 25) for data minimization.

---

## 5. Oral Q&A Prep Guide

### Q1: "Your agent classified `dl_number` (Driving License) as HIGH. Why not CRITICAL?"
> **Answer:** A driving license is a government ID that can be used for identity fraud. However, standard classification systems mark it as **HIGH** because a leak does not directly compromise payment gateways (unlike credit card numbers or bank keys) or cause immediate physical danger. 
> 
> *However, a human expert can argue it is CRITICAL in India because the DL is frequently linked to Aadhaar. If a hacker links the DL to a centralized Aadhaar profile, they can bypass KYC procedures, opening fraudulent accounts across fintech networks.*

### Q2: "A new engineer joins your team. They ask for SELECT access to `stg_users` vs `dim_users`. Grant or deny? Why?"
> **Answer:** 
> - **DENY `stg_users`:** This staging table contains raw, unmasked PII (physical addresses, phone numbers, and GPS coordinates). No general software engineer needs raw coordinates to optimize or write queries.
> - **GRANT `dim_users`:** This analytics table is safe for general queries. It hashes phone numbers and emails (`SHA256`) and excludes exact coordinate variables, allowing engineers to analyze trends safely.

### Q3: "Name one column in your warehouse where the agent got the governance wrong. What did it miss?"
> **Answer:** The agent misclassified **`stg_outlets.gst_number`** as LOW severity because it treated it as a corporate tax identifier. 
> 
> *What the AI missed:* In India, a GSTIN (Goods and Services Tax Identification Number) is a 15-character code where characters 3 through 12 represent the business owner's **PAN (Permanent Account Number)**. For sole proprietorship restaurants, this exposes the owner's personal government-issued tax ID (PAN), which is highly sensitive PII. The agent lacks this local domain expertise and failed to flag the leak.

---

## 6. Post-Reveal Discussion Answers

### Q1: Did both mysteries have `bank_account_number`? What's different about the risk?
> **Answer:** Yes. Mystery A (HR Software) and Mystery B (Food Delivery) both store bank account numbers, but the risk profiles are completely different:
> - **Mystery A (Corporate Payroll):** Accounts belong to internal corporate employees. The vulnerability lies in insider threats or internal phishing. The volume of payment transactions is low (once a month).
> - **Mystery B (Gig Economy Payouts):** Accounts belong to thousands of independent gig riders. The payments are high-frequency (weekly/daily). Because gig workers are remote and use personal devices, they are highly vulnerable to social engineering and external phishing. Compromising the database allows attackers to hijack rider payouts en masse.

### Q2: Which industry had harder governance decisions? Why?
> **Answer:** **Mystery B (Food Delivery)** has much harder governance decisions. 
> 
> *Why:* It processes two-sided real-time location data. To deliver food, the app must track the customer (`drop_lat`/`drop_lng`) and the rider (`current_lat`/`current_lng`). This data is dynamic, precise, and dangerous if exposed. Managing the trade-off between operational efficiency (routing the driver quickly) and privacy (hiding the user's home from the driver post-delivery) is a highly complex threat model.

### Q3: What would change if this company expanded to Europe?
> **Answer:** 
> 1.  **Right to Erasure (Article 17):** Delivery apps must build routines to scrub user address histories and rider coordinates upon request.
> 2.  **Location Anonymization:** Raw coordinates cannot be retained long-term. They must be rounded or converted to spatial grids (like Uber's H3 or Geohashes) to remove individual precision.
> 3.  **Strict Consent Frameworks:** Driver tracking and matching algorithms must prove they do not engage in automated discriminatory scoring.

---

## 7. Step-by-Step Lab Execution Guide

### Lab 1: Undocumented dbt Project

#### Step 1: Install Dependencies
Run the installation scripts:
```bash
cd repo/day13
pip install -r lab/requirements.txt
aws sts get-caller-identity
```

#### Step 2: Run the Lineage Agent for Mystery B
Start the agent pointing to the Mystery B directory:
```bash
python lab/lineage_agent.py --lab 1 --mystery lab/mystery_b/
```
*   The script will halt and prompt you for the **three manual assessment answers** compiled in **Section 3** above.
*   Once inputted, it will trigger the Bedrock LLM loop (`nova-lite`).

#### Step 3: Verify the Output File
Check the newly written JSON catalog:
```bash
cat lab/agent_outputs/catalogue_mystery_b.json
```
*   Verify that all 8 tables were analyzed.
*   Verify that `pii_surface_area` successfully caught at least 5 sensitive columns.

---

### Lab 2: Cataloguing Your Day 6 Project
After evaluating the mystery project, point the lineage agent at your own dbt repository from Day 6:

```bash
python lab/lineage_agent.py --lab 2 --models ../day6/sigma_dbt/models/
```
*   The script will prompt you for sensitive columns and tables in your own project.
*   It will output `lab/agent_outputs/catalogue_sigma.json`, which serves as your final client catalog deliverable.

---

### Run Final Validator
Verify that all catalogs, guesses, and files are complete and structured correctly:

```bash
python tests/validate_day13.py
```
*Expected Output:*
```
OK  catalogue_mystery_b.json — 8 tables catalogued
OK  mystery_guess.json — manual answers saved
OK  PII columns found — at least 5
OK  three_questions answered
```

---

## 8. Reflection: AI vs. Human Governance
The lab demonstrates the limits of AI capability in data engineering:

*   **Where AI Wins:** speed and scale. The agent mapped columns, resolved table joins, identified PII columns, and wrote standard GDPR guidelines for 8 models in under **90 seconds**. A human analyst would spend half a day manually documenting this.
*   **Where Human Wins:** local business context. The AI does not know local tax laws (e.g., that a GST number contains a private individual's PAN). It cannot appreciate that a restaurant food license (FSSAI) is a key corporate asset, or that a rider's failed background check status requires extreme privacy safeguards to avoid defamation risks.

> *Rule of thumb: AI creates the catalog. Humans define the policies.*
