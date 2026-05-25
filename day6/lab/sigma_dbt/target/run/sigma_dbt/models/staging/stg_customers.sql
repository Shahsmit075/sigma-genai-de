
  create or replace   view SIGMA_DE.PUBLIC.stg_customers
  
  
  
  
  as (
    WITH raw_customers AS (
    SELECT
        customer_id,
        customer_name,
        email,
        tier,
        signup_date,
        city
    FROM SIGMA_DE.PUBLIC.dim_customer
)

SELECT
    LOWER(customer_id) AS customer_id,
    customer_name,
    email,
    UPPER(tier) AS tier,
    CAST(signup_date AS DATE) AS signup_date,
    city
FROM raw_customers
  );

