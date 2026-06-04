
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



with __dbt__cte__stg_customers as (
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
) select customer_id
from __dbt__cte__stg_customers
where customer_id is null



  
  
      
    ) dbt_internal_test