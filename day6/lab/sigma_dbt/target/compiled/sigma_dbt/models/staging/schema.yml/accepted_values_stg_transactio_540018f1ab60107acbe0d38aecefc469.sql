
    
    

with  __dbt__cte__stg_transactions as (
WITH raw_transactions AS (
    SELECT 
        transaction_id,
        amount,
        status,
        merchant_id,
        customer_id,
        transaction_date,
        payment_method
    FROM 
        SIGMA_DE.PUBLIC.fact_transactions
),

cleaned_transactions AS (
    SELECT 
        LOWER(transaction_id) AS transaction_id,
        CAST(amount AS DECIMAL(10,2)) AS amount,
        UPPER(status) AS status,
        LOWER(merchant_id) AS merchant_id,
        LOWER(customer_id) AS customer_id,
        CAST(transaction_date AS DATE) AS transaction_date,
        UPPER(payment_method) AS payment_method,
        CURRENT_TIMESTAMP() AS loaded_at
    FROM 
        raw_transactions
    WHERE 
        merchant_id NOT LIKE 'test_%'
)

SELECT * FROM cleaned_transactions
), all_values as (

    select
        status as value_field,
        count(*) as n_records

    from __dbt__cte__stg_transactions
    group by status

)

select *
from all_values
where value_field not in (
    'COMPLETED','FAILED','PENDING'
)


