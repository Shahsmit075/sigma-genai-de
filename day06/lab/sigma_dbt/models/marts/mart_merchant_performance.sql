<<<<<<< HEAD
WITH transactions AS (
=======
WITH filtered_transactions AS (
>>>>>>> 83d5fc253a8457c3903da527641897b01c810c15
    SELECT
        transaction_id,
        amount,
        status,
        merchant_id,
        customer_id,
<<<<<<< HEAD
        transaction_date
    FROM {{ ref('stg_transactions') }}
),

merchants AS (
=======
        transaction_date,
        payment_method
    FROM {{ ref('stg_fact_transactions') }}
    WHERE status IN ('COMPLETED', 'FAILED')
),

merchant_details AS (
>>>>>>> 83d5fc253a8457c3903da527641897b01c810c15
    SELECT
        merchant_id,
        merchant_name,
        category,
<<<<<<< HEAD
        city
    FROM {{ ref('stg_merchants') }}
),

aggregated AS (
    SELECT
        merchant_id,
        COUNT(transaction_id) AS total_transactions,
        SUM(CASE WHEN status = 'COMPLETED' THEN amount ELSE 0 END) AS total_revenue,
        COUNT(CASE WHEN status = 'FAILED' THEN 1 END) AS failed_count,
        COUNT(DISTINCT customer_id) AS unique_customers,
        AVG(CASE WHEN status = 'COMPLETED' THEN amount ELSE NULL END) AS avg_transaction_value
    FROM transactions
    GROUP BY merchant_id
)

SELECT
    m.merchant_id,
    m.merchant_name,
    m.category,
    m.city,
    COALESCE(a.total_transactions, 0) AS total_transactions,
    COALESCE(a.total_revenue, 0.0) AS total_revenue,
    COALESCE(a.failed_count, 0) AS failed_count,
    ROUND(
        COALESCE(
            (a.failed_count::FLOAT / NULLIF(a.total_transactions, 0)) * 100.0,
            0.0
        ),
        2
    ) AS failure_rate_pct,
    COALESCE(a.avg_transaction_value, 0.0) AS avg_transaction_value,
    COALESCE(a.unique_customers, 0) AS unique_customers
FROM merchants m
LEFT JOIN aggregated a ON m.merchant_id = a.merchant_id
=======
        city,
        onboarded_date
    FROM {{ ref('dim_merchant') }}
),

aggregated_metrics AS (
    SELECT
        ft.merchant_id,
        COUNT(ft.transaction_id) AS total_transactions,
        COUNT(CASE WHEN ft.status = 'FAILED' THEN 1 END) AS failed_count,
        SUM(CASE WHEN ft.status = 'COMPLETED' THEN ft.amount ELSE 0 END) AS total_revenue,
        AVG(CASE WHEN ft.status = 'COMPLETED' THEN ft.amount ELSE NULL END) AS avg_transaction_value,
        COUNT(DISTINCT ft.customer_id) AS unique_customers
    FROM filtered_transactions ft
    GROUP BY ft.merchant_id
)

SELECT
    md.merchant_id,
    md.merchant_name,
    md.category,
    md.city,
    md.onboarded_date,
    am.total_transactions,
    am.failed_count,
    am.total_revenue,
    am.avg_transaction_value,
    am.unique_customers,
    (am.failed_count::FLOAT / am.total_transactions) * 100 AS failure_rate_pct
FROM aggregated_metrics am
JOIN merchant_details md ON am.merchant_id = md.merchant_id
```

```yaml
version: 2

models:
  - name: mart_merchant_kpis
    description: "Aggregated merchant KPIs including total revenue, total transactions, failed count, failure rate, average transaction value, and unique customers."
    columns:
      - name: merchant_id
        description: "Unique identifier for the merchant."
        tests:
          - not_null
          - unique
          - relationships:
              to: ref('dim_merchant')
              field: merchant_id
      - name: merchant_name
        description: "Name of the merchant."
        tests:
          - not_null
      - name: category
        description: "Category of the merchant."
        tests:
          - not_null
          - accepted_values:
              values: ["Food Delivery", "E-Commerce", "Entertainment", "Travel", "Grocery"]
      - name: city
        description: "City where the merchant is located."
        tests:
          - not_null
      - name: onboarded_date
        description: "Date when the merchant was onboarded."
        tests:
          - not_null
      - name: total_transactions
        description: "Total number of transactions for the merchant."
        tests:
          - not_null
      - name: failed_count
        description: "Number of failed transactions for the merchant."
        tests:
          - not_null
      - name: total_revenue
        description: "Total revenue from completed transactions for the merchant."
        tests:
          - not_null
      - name: avg_transaction_value
        description: "Average value of completed transactions for the merchant."
        tests:
          - not_null
      - name: unique_customers
        description: "Number of unique customers who made transactions with the merchant."
        tests:
          - not_null
      - name: failure_rate_pct
        description: "Failure rate percentage of transactions for the merchant."
>>>>>>> 83d5fc253a8457c3903da527641897b01c810c15
