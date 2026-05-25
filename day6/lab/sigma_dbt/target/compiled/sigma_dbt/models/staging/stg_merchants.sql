WITH raw_merchants AS (
    SELECT
        merchant_id,
        merchant_name,
        category,
        city
    FROM SIGMA_DE.PUBLIC.dim_merchant
)

SELECT
    LOWER(merchant_id) AS merchant_id,
    merchant_name,
    category,
    city
FROM raw_merchants