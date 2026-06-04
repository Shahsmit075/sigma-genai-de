# catalog_data.py
# Sigma DataTech — Official Data Catalogue
# 20 tables | Pre-provided — DO NOT MODIFY
# Today's date: 2026-05-22

TABLE_CATALOG = [
    {
        "table_name": "customers",
        "last_updated": "2026-05-21",
        "classification": "PII-Critical",
        "domain": "Identity",
        "owner": "Identity Engineering",
        "description": (
            "Customer master table. Stores personally identifiable information: "
            "full_name, email, phone_number, date_of_birth, residential_address, "
            "PAN number, Aadhaar reference hash. Created on customer onboarding. "
            "4.2M rows. Accessed by Payments, KYC, Risk, and Support teams. "
            "Retention policy: 10 years (RBI mandate). Privacy classification: "
            "Critical PII — requires data masking in non-production environments."
        ),
    },
    {
        "table_name": "kyc_documents",
        "last_updated": "2026-05-20",
        "classification": "PII-Critical",
        "domain": "Compliance",
        "owner": "Compliance Engineering",
        "description": (
            "KYC document verification store. Contains customer document metadata: "
            "document_type (Aadhaar/PAN/Passport/DL), document_number, issuing_authority, "
            "verification_status, verified_at, expiry_date, scanned_image_s3_path. "
            "Directly tied to customer personal identity. CKYC-compliant. "
            "4.2M rows. Restricted to Compliance, Legal, and KYC ops teams only. "
            "Any access requires manager approval — PII is present in every row."
        ),
    },
    {
        "table_name": "user_profiles",
        "last_updated": "2026-05-19",
        "classification": "PII-High",
        "domain": "Identity",
        "owner": "Product Engineering",
        "description": (
            "Extended user profile for app personalization. Contains full_name, "
            "email, profile_picture_url, preferred_language, linked_device_ids, "
            "communication_preferences, notification_opt_ins, last_login_at. "
            "PII fields: full_name, email, device IDs. Updated on every login. "
            "4.1M active rows. Sourced from mobile and web registration flows."
        ),
    },
    {
        "table_name": "payment_cards",
        "last_updated": "2026-05-15",
        "classification": "PII-High",
        "domain": "Payments",
        "owner": "Payments Engineering",
        "description": (
            "Payment card vault. Stores tokenized card details: card_token, "
            "card_last4, card_type (Visa/MC/Amex/RuPay), expiry_month, expiry_year, "
            "issuing_bank, billing_address, cardholder_name. "
            "Full card numbers are never stored — PCI-DSS Level 1 compliant. "
            "PII fields: cardholder_name, billing_address. 2.8M rows. "
            "Last data quality audit: 2026-05-15."
        ),
    },
    {
        "table_name": "beneficiaries",
        "last_updated": "2026-05-06",
        "classification": "PII-High",
        "domain": "Payments",
        "owner": "Payments Engineering",
        "description": (
            "Saved payee and beneficiary details for fund transfers. "
            "Stores beneficiary_name, account_number, IFSC_code, bank_name, "
            "relationship_to_payer, vpa (UPI ID), added_at, last_used_at. "
            "PII fields: beneficiary_name, account_number, IFSC constitute "
            "financial identity. Used in NEFT/IMPS/UPI/RTGS flows. "
            "11.3M rows. Mandatory 5-year retention for AML audit trail."
        ),
    },
    {
        "table_name": "fraud_cases",
        "last_updated": "2026-05-22",
        "classification": "PII-High",
        "domain": "Risk",
        "owner": "Risk & Fraud Engineering",
        "description": (
            "Fraud investigation case records. Captures customer_id, suspected_ip_address, "
            "device_fingerprint, geo_location_coordinates, transaction_ids_flagged, "
            "fraud_type (account_takeover/synthetic_identity/card_fraud), "
            "case_status, assigned_analyst_id, evidence_notes. "
            "Contains personal data of both victims and suspects. "
            "Restricted to Risk, Fraud Ops, and Legal teams. 340K rows."
        ),
    },
    {
        "table_name": "transactions",
        "last_updated": "2026-05-22",
        "classification": "Internal",
        "domain": "Payments",
        "owner": "Payments Engineering",
        "description": (
            "Core payment transaction ledger. Records txn_id, amount, currency, "
            "merchant_id, wallet_id, payment_method, txn_status, initiated_at, "
            "processed_at, settlement_date, failure_reason, gateway_reference. "
            "No direct PII stored — customer linkage via wallet_id foreign key. "
            "110M rows. Partitioned by processed_at (daily). "
            "Source of truth for Finance reconciliation."
        ),
    },
    {
        "table_name": "risk_scores",
        "last_updated": "2026-05-21",
        "classification": "Internal",
        "domain": "Risk",
        "owner": "Risk & Fraud Engineering",
        "description": (
            "Customer risk assessment scores generated by ML risk models. "
            "Stores customer_id, risk_score (0-1000), risk_tier (Low/Medium/High/Critical), "
            "model_version, feature_snapshot_json, calculated_at, valid_until. "
            "Refreshed every 6 hours via Airflow DAG. "
            "Drives real-time transaction limits and fraud alert thresholds. "
            "No raw PII — customer_id is a surrogate key. 4.2M rows."
        ),
    },
    {
        "table_name": "wallets",
        "last_updated": "2026-05-22",
        "classification": "Internal",
        "domain": "Payments",
        "owner": "Payments Engineering",
        "description": (
            "Digital wallet master table. Stores wallet_id, customer_id, balance, "
            "currency, wallet_type (prepaid/postpaid/escrow), kyc_tier, "
            "status (active/frozen/closed), created_at, last_transaction_at. "
            "Balance is real-time (strong consistency). No raw PII in this table — "
            "customer name/contact lives in the customers table. "
            "4.2M rows. Every payment flow reads this table."
        ),
    },
    {
        "table_name": "audit_logs",
        "last_updated": "2026-05-22",
        "classification": "Internal",
        "domain": "Security",
        "owner": "Platform Security",
        "description": (
            "Immutable system-wide audit trail for all data access and state changes. "
            "Captures user_id, session_id, action_type (READ/WRITE/DELETE/EXPORT), "
            "target_table, target_record_id, ip_address, user_agent, timestamp, "
            "change_delta_json. No UPDATE or DELETE permitted — append-only. "
            "2.1 billion rows. Retained 7 years. "
            "Primary evidence source for compliance and forensic investigations."
        ),
    },
    {
        "table_name": "orders",
        "last_updated": "2026-05-18",
        "classification": "Internal",
        "domain": "Commerce",
        "owner": "Commerce Engineering",
        "description": (
            "Purchase order records from Sigma DataTech marketplace. "
            "Stores order_id, customer_id, product_id, quantity, unit_price, "
            "total_amount, discount_applied, order_status, payment_status, "
            "delivery_address_hash, created_at, dispatched_at, fulfilled_at. "
            "delivery_address is SHA-256 hashed — not raw PII. "
            "38M rows. Partitioned monthly. Source for revenue reporting."
        ),
    },
    {
        "table_name": "products",
        "last_updated": "2026-05-09",
        "classification": "Public",
        "domain": "Commerce",
        "owner": "Commerce Engineering",
        "description": (
            "Product master catalogue for the Sigma DataTech marketplace. "
            "Stores product_id, product_name, category, subcategory, brand, "
            "description_text, unit_price, stock_quantity, weight_grams, "
            "dimensions_cm, image_url, is_active, created_at. "
            "No customer or PII data whatsoever. Fully public — "
            "powers storefront, search APIs, and partner integrations. 180K rows."
        ),
    },
    {
        "table_name": "merchants",
        "last_updated": "2026-05-02",
        "classification": "Internal",
        "domain": "Payments",
        "owner": "Merchant Partnerships",
        "description": (
            "Merchant master for the payment acceptance network. "
            "Stores merchant_id, business_name, business_category, MCC_code, "
            "city, state, onboarding_date, settlement_account_number, "
            "merchant_tier (Platinum/Gold/Silver). "
            "Internal field internal_rating classifies merchants as whale/dolphin/minnow "
            "based on monthly GMV — this field is not documented in the official data dictionary. "
            "95K rows. No individual PII — business entity data only."
        ),
    },
    {
        "table_name": "support_tickets",
        "last_updated": "2026-05-13",
        "classification": "Internal",
        "domain": "Operations",
        "owner": "CX Engineering",
        "description": (
            "Customer support case management table. "
            "Stores ticket_id, customer_id, issue_category, issue_description, "
            "priority (P1-P4), assigned_agent_id, status, resolution_notes, "
            "created_at, resolved_at, csat_score. "
            "issue_description may contain verbatim customer messages which can include PII. "
            "Agents are trained to redact before ticket closure, but not enforced technically. "
            "12M rows. Retention: 3 years."
        ),
    },
    {
        "table_name": "notifications",
        "last_updated": "2026-05-19",
        "classification": "Internal",
        "domain": "Engagement",
        "owner": "Growth Engineering",
        "description": (
            "Notification dispatch log for push, SMS, WhatsApp, and email channels. "
            "Stores notification_id, customer_id, channel, template_id, "
            "rendered_message, sent_at, delivery_status, opened_at, clicked_at. "
            "rendered_message may contain personalised PII (customer first name, account last4). "
            "Retained 90 days then purged. 800M rows. High-throughput write path."
        ),
    },
    {
        "table_name": "exchange_rates",
        "last_updated": "2026-05-22",
        "classification": "Reference",
        "domain": "Finance",
        "owner": "Finance Engineering",
        "description": (
            "Real-time currency exchange rate feed. "
            "Stores currency_pair (e.g. USD/INR, EUR/INR), bid_rate, ask_rate, "
            "mid_rate, source (RBI/Bloomberg/internal_model), "
            "effective_from, effective_until, confidence_score. "
            "Refreshed every 15 minutes via a scheduled Lambda. "
            "No customer or PII data. Used for multi-currency settlement. 2.4M rows."
        ),
    },
    {
        "table_name": "merchant_fees",
        "last_updated": "2026-05-20",
        "classification": "Confidential",
        "domain": "Finance",
        "owner": "Finance Engineering",
        "description": (
            "Merchant fee and MDR (Merchant Discount Rate) configuration table. "
            "Stores merchant_id, fee_type (flat/percentage/tiered), fee_rate, "
            "applicable_payment_method, effective_from, effective_until, approved_by. "
            "Commercially sensitive — bilateral contract terms, not shared externally. "
            "No PII. 280K rows. Updated when merchant contracts are renegotiated."
        ),
    },
    {
        "table_name": "system_config",
        "last_updated": "2026-05-17",
        "classification": "Internal",
        "domain": "Platform",
        "owner": "Platform Engineering",
        "description": (
            "Application configuration key-value store for all microservices. "
            "Stores config_key, config_value, config_type (string/int/json/secret), "
            "environment (prod/staging/dev), updated_by, updated_at, description. "
            "Controls feature flags, rate limits, API gateway settings, and service endpoints. "
            "Secret-type values are AES-256 encrypted at rest. No PII. 4.2K rows."
        ),
    },
    {
        "table_name": "compliance_rules",
        "last_updated": "2026-05-14",
        "classification": "Confidential",
        "domain": "Compliance",
        "owner": "Compliance Engineering",
        "description": (
            "Regulatory compliance rule engine configuration. "
            "Stores rule_id, rule_name, regulation (RBI/GDPR/PCI-DSS/PMLA/IT-Act), "
            "rule_description, threshold_value, lookback_window_days, "
            "action_on_breach (block/alert/log/escalate), last_reviewed, reviewed_by. "
            "Governs transaction monitoring, data retention policies, and PII handling. "
            "No PII data itself. 340 active rules. Reviewed quarterly by Compliance team."
        ),
    },
    {
        "table_name": "product_catalog_embeddings",
        "last_updated": "2026-05-21",
        "classification": "Internal",
        "domain": "Commerce",
        "owner": "ML Platform",
        "description": (
            "Extended product metadata for AI-powered search and recommendations. "
            "Stores product_id, embedding_vector (768-dimensional float array), "
            "semantic_tags, search_keywords, similar_product_ids, "
            "review_summary_ai (LLM-generated), last_embedding_refresh. "
            "Powers the semantic search API and collaborative filtering recommender. "
            "No PII. 180K rows. Refreshed nightly by the SageMaker embedding pipeline."
        ),
    },
]
