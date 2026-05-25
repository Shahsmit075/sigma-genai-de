-- Query to get high spending customer emails and their signup dates
SELECT customer_name, email, signup_date, SUM(amount) AS total_amount
FROM dim_customer, fact_transactions
WHERE dim_customer.customer_id = fact_transactions.customer_id
GROUP BY customer_name, signup_date;
