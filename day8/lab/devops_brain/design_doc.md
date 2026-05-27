# Data Pipeline Design Document

## What This Pipeline Does
This pipeline ingests transaction data, enriches it with merchant information, and then aggregates it into two gold tables: merchant performance metrics and daily transaction summaries.

## Data Flow Diagram

```
+---------------------+       +---------------------+       +---------------------+
|   Source Data       | --->  |  Bronze Transactions | --->  |  Silver Transactions |
+---------------------+       +---------------------+       +---------------------+
| TRANSACTIONS_CLEAN  |       |  bronze_transactions |       |  silver_transactions |
| TRANSACTIONS_DIRTY   |       |                      |       |                      |
+---------------------+       +---------------------+       +---------------------+
                                                                    |
                                                                    V
                                                            +---------------------+
                                                            |   Gold Tables        |
                                                            +---------------------+
                                                                    |
                                                                    V
                                                            +---------------------+       +---------------------+
                                                            | Gold Merchant        | --->  | Gold Daily Summary   |
                                                            | Performance          |       |                      |
                                                            |                      |       |                      |
                                                            | gold_merchant_perf   |       | gold_daily_summary   |
                                                            +---------------------+       +---------------------+
```

## Key Design Decisions
- **Layered Data Processing**: The pipeline uses a three-tier architecture (Bronze, Silver, Gold) to separate raw data ingestion, data cleaning, and aggregation.
- **Quality Flags**: Introduced quality flags in the Silver layer to distinguish between clean and dirty data.
- **Date-Partitioned Gold Tables**: The Gold layer tables are partitioned by date to facilitate time-series analysis.
- **Data Enrichment**: Merchant information is joined with transaction data in the Silver layer to enrich the dataset.

## Known Limitations
- **Data Quality**: The pipeline assumes that the `MERCHANTS` data is complete and accurate. Any missing merchant data will result in incomplete Silver transactions.
- **Performance**: The pipeline processes all transactions in memory, which may not scale well for very large datasets.
- **Error Handling**: The pipeline uses a simple `try-except` block for error handling, which may not capture all possible exceptions.
- **Data Freshness**: The pipeline runs once daily, which may not meet real-time data needs.

## Dependencies
- **DuckDB**: The pipeline relies on DuckDB for data storage and processing.
- **MERCHANTS Data**: A list of merchant details used for enriching transaction data.
- **TRANSACTIONS_CLEAN and TRANSACTIONS_DIRTY**: Source data files containing transaction records.