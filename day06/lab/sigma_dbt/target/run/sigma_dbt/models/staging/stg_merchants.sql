
  create or replace   view SIGMA_DE.PUBLIC.stg_merchants
  
  
  
  
  as (
    WITH raw_merchants AS (
    SELECT
        merchant_id,
        merchant_name,
        category,
        city,
        onboarded_date
    FROM SIGMA_DE.PUBLIC.dim_merchant
)

SELECT
    LOWER(merchant_id) AS merchant_id,
    merchant_name,
    category,
    city,
    CAST(onboarded_date AS DATE) AS onboarded_date
FROM raw_merchants
  );

