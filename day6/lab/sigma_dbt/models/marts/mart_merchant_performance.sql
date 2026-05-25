WITH transactions AS (
    SELECT
        transaction_id,
        amount,
        status,
        merchant_id,
        customer_id,
        transaction_date
    FROM {{ ref('stg_transactions') }}
),

merchants AS (
    SELECT
        merchant_id,
        merchant_name,
        category,
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
