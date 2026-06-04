-- ============================================================
-- Sigma DataTech — Data Catalogue Setup
-- Sigma Intelligence Bootcamp · Day 4
-- Run this entire script in your Snowflake trial account
-- (Worksheet → paste → Run All)
-- ============================================================

-- Step 1: Create database and schema
CREATE DATABASE IF NOT EXISTS SIGMA_CATALOGUE;
USE DATABASE SIGMA_CATALOGUE;
USE SCHEMA PUBLIC;

-- Step 2: Create Sigma DataTech catalogue tables with rich COMMENTs
-- The COMMENT field is what gets embedded into FAISS.
-- Tags [classification:...] [owner:...] [domain:...] are parsed by Python.

CREATE OR REPLACE TABLE CUSTOMERS (
    customer_id     VARCHAR,
    full_name       VARCHAR,
    email           VARCHAR,
    phone           VARCHAR,
    aadhaar_hash    VARCHAR,
    pan_number      VARCHAR,
    date_of_birth   DATE,
    created_at      TIMESTAMP
)
COMMENT = 'Core customer identity table storing personally identifiable information including full name, email, phone, Aadhaar hash, and PAN number. Used for KYC verification and compliance reporting. Every transaction links back to this table. [classification:PII-Critical] [owner:Identity Engineering] [domain:compliance]';

CREATE OR REPLACE TABLE TRANSACTIONS (
    transaction_id   VARCHAR,
    customer_id      VARCHAR,
    merchant_id      VARCHAR,
    amount           NUMBER(18,2),
    currency         VARCHAR,
    status           VARCHAR,
    created_at       TIMESTAMP
)
COMMENT = 'High-volume payments ledger recording every UPI, card, and wallet transaction processed by Sigma DataTech. 4.2 million transactions per day. Used for revenue reporting, fraud detection, and RBI regulatory submissions. No direct PII stored — joins to CUSTOMERS via customer_id. [classification:Internal] [owner:Payments Engineering] [domain:payments]';

CREATE OR REPLACE TABLE KYC_DOCUMENTS (
    doc_id          VARCHAR,
    customer_id     VARCHAR,
    doc_type        VARCHAR,
    doc_number      VARCHAR,
    verified_at     TIMESTAMP,
    verified_by     VARCHAR,
    expiry_date     DATE
)
COMMENT = 'Stores scanned KYC document metadata for all onboarded customers. Contains Aadhaar number, PAN, passport, and driving licence references. Subject to RBI KYC master direction and GDPR right-to-erasure obligations. Highest sensitivity table in the catalogue. [classification:PII-Critical] [owner:Compliance] [domain:compliance]';

CREATE OR REPLACE TABLE RISK_SCORES (
    customer_id     VARCHAR,
    score           NUMBER(5,2),
    risk_band       VARCHAR,
    model_version   VARCHAR,
    scored_at       TIMESTAMP,
    features_json   VARIANT
)
COMMENT = 'Machine-learning-generated fraud and credit risk scores for each customer. Risk band values: LOW, MEDIUM, HIGH, CRITICAL. Refreshed every 6 hours using transaction velocity and behavioural features. Used by the fraud decisioning engine to block or flag transactions in real time. [classification:Confidential] [owner:Risk Engineering] [domain:risk]';

CREATE OR REPLACE TABLE MERCHANT_PROFILES (
    merchant_id     VARCHAR,
    business_name   VARCHAR,
    category        VARCHAR,
    onboarded_at    TIMESTAMP,
    status          VARCHAR,
    internal_rating VARCHAR
)
COMMENT = 'Master record for all registered merchants on the Sigma DataTech platform. Includes business name, MCC category, and onboarding status. Internal field internal_rating classifies merchants as whale/dolphin/minnow based on monthly GMV — this field is not documented in the official data dictionary. [classification:Internal] [owner:Merchant Success] [domain:merchant]';

CREATE OR REPLACE TABLE FRAUD_CASES (
    case_id         VARCHAR,
    customer_id     VARCHAR,
    transaction_id  VARCHAR,
    case_type       VARCHAR,
    reported_at     TIMESTAMP,
    resolved_at     TIMESTAMP,
    outcome         VARCHAR,
    investigator_id VARCHAR
)
COMMENT = 'Active and historical fraud investigation records linked to customers and transactions. Contains customer PII indirectly via customer_id join. Case types include account takeover, card cloning, UPI phishing, and merchant collusion. Restricted to Risk Engineering and Compliance teams only. [classification:PII-High] [owner:Risk Engineering] [domain:risk]';

CREATE OR REPLACE TABLE AUDIT_LOGS (
    log_id          VARCHAR,
    event_type      VARCHAR,
    actor_id        VARCHAR,
    resource_type   VARCHAR,
    resource_id     VARCHAR,
    event_at        TIMESTAMP,
    ip_address      VARCHAR,
    metadata_json   VARIANT
)
COMMENT = 'Immutable audit trail of all privileged actions performed on the Sigma DataTech platform — including data access, schema changes, and admin operations. Retained for 7 years per RBI circular. Used for security forensics and compliance audits. Updated in real time. [classification:Internal] [owner:Platform Engineering] [domain:governance]';

CREATE OR REPLACE TABLE WALLETS (
    wallet_id       VARCHAR,
    customer_id     VARCHAR,
    balance         NUMBER(18,2),
    currency        VARCHAR,
    last_transaction_at TIMESTAMP,
    status          VARCHAR
)
COMMENT = 'Real-time wallet balance ledger for all Sigma DataTech prepaid wallet accounts. Balance updated on every credit or debit event. Used for settlement reconciliation and RBI prepaid instrument reporting. No PII stored directly. [classification:Internal] [owner:Payments Engineering] [domain:payments]';

-- ============================================================
-- Step 3: Verify — run this after creating tables
-- ============================================================
SELECT
    TABLE_NAME,
    LEFT(COMMENT, 80) AS COMMENT_PREVIEW,
    LAST_ALTERED
FROM INFORMATION_SCHEMA.TABLES
WHERE TABLE_SCHEMA = 'PUBLIC'
  AND TABLE_TYPE   = 'BASE TABLE'
  AND COMMENT IS NOT NULL
ORDER BY TABLE_NAME;

-- Expected: 8 rows with non-empty COMMENT_PREVIEW
-- If you see 0 rows — check you are in the SIGMA_CATALOGUE database
