select *
from {{ ref('mart_merchant_performance') }}
where total_revenue < 0
