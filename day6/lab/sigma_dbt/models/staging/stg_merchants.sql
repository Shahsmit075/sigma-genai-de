WITH raw_merchants AS (
    SELECT
        merchant_id,
        merchant_name,
        category,
        city
    FROM {{ source('sigma_analytics', 'dim_merchant') }}
)

SELECT
    LOWER(merchant_id) AS merchant_id,
    merchant_name,
    category,
    city
FROM raw_merchants
