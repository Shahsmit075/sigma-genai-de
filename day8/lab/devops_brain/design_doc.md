# Data Pipeline Design Document

## What This Pipeline Does
<<<<<<< HEAD
This pipeline ingests transaction data, enriches it with merchant information, and then aggregates it into two gold tables: merchant performance metrics and daily transaction summaries.
=======
This pipeline ingests transaction data from both clean and dirty sources, processes it, and stores it in three layers: Bronze, Silver, and Gold. The Bronze layer stores raw data, the Silver layer stores cleaned and enriched data, and the Gold layer stores aggregated metrics.
>>>>>>> 83d5fc253a8457c3903da527641897b01c810c15

## Data Flow Diagram

```
<<<<<<< HEAD
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
=======
+----------------+      +--------------------+      +--------------------+      +--------------------+
| TRANSACTIONS   | ---> | bronze_transactions| ---> | silver_transactions| ---> | gold_merchant_perf |
| (Clean & Dirty)|      |                    |      |                    |      |                    |
+----------------+      +--------------------+      +--------------------+      +--------------------+
                                                                                     |
                                                                                 +--------------------+
                                                                                 | gold_daily_summary  |
                                                                                 +--------------------+
```

## Key Design Decisions
- **Layered Approach**: The pipeline uses a three-tier architecture (Bronze, Silver, Gold) to separate raw data, cleaned data, and aggregated metrics.
- **Data Enrichment**: The Silver layer enriches transaction data by joining it with merchant information, making it more useful for analysis.
- **Aggregation**: The Gold layer computes metrics like merchant performance and daily summaries, providing valuable insights.
- **Data Quality Flags**: The Silver layer includes quality flags to distinguish between clean and potentially problematic data.

## Known Limitations
- **Data Duplication**: The pipeline does not handle duplicate transactions within a single run.
- **Limited Error Handling**: The pipeline has minimal error handling, which could be improved for robustness.
- **Single-Run Processing**: The pipeline processes all transactions in a single run, which may not be suitable for very large datasets.
- **Static Merchant Data**: Merchant data is loaded once and not updated unless the pipeline is rerun.

## Dependencies
- **DuckDB**: The pipeline uses DuckDB for data storage and processing.
- **MERCHANTS**: A list of merchant data used for enriching transactions.
- **TRANSACTIONS_CLEAN and TRANSACTIONS_DIRTY**: Lists of clean and dirty transaction data, respectively.
>>>>>>> 83d5fc253a8457c3903da527641897b01c810c15
