<<<<<<< HEAD
import logging
import shutil
from datetime import datetime
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, lit, broadcast, when, sum, count, max, expr, mode, to_date
from pyspark.sql.types import FloatType, StringType, DateType
import json
import os
=======
import shutil
import logging
import json
from datetime import datetime
>>>>>>> 83d5fc253a8457c3903da527641897b01c810c15

logging.basicConfig(level=logging.INFO)

def ingest_bronze(spark, input_path, output_path, run_date, run_id):
    try:
<<<<<<< HEAD
        logging.info("[Stage: Ingest Bronze] Starting ingestion")
        transactions_df = (spark.read.format("csv")
                          .option("header", "true")
                          .option("inferSchema", "false")
                          .load(input_path))
        
        logging.info(f"[Stage: Ingest Bronze] Input count: {transactions_df.count():,}")
=======
        logging.info("Starting ingest_bronze stage")
        partition_path = f"{output_path}/ingestion_timestamp={run_date}"
        shutil.rmtree(partition_path, ignore_errors=True)  # Idempotency: delete partition before write
        
        transactions_df = (spark.read.option("header", "true")
                           .option("inferSchema", "false")
                           .csv(input_path))
>>>>>>> 83d5fc253a8457c3903da527641897b01c810c15
        
        transactions_df = (transactions_df.withColumn("ingestion_timestamp", lit(run_date))
                           .withColumn("source_file", lit("transactions.csv"))
                          .withColumn("pipeline_run_id", lit(run_id)))
        
<<<<<<< HEAD
        partition_path = f"{output_path}/ingestion_timestamp={run_date}"
        shutil.rmtree(partition_path, ignore_errors=True)
        
        transactions_df.write.mode("overwrite").partitionBy("ingestion_timestamp").parquet(output_path)
        logging.info("[Stage: Ingest Bronze] Ingestion completed successfully")
    except Exception as e:
        logging.error(f"[Stage: Ingest Bronze] Error: {e}")
=======
        input_count = transactions_df.count()
        logging.info(f"[Stage: ingest_bronze] input_count: {input_count:,} rows")
        
        transactions_df.write.partitionBy("ingestion_timestamp").mode("overwrite").parquet(output_path)
        
        output_count = spark.read.parquet(output_path).where(col("ingestion_timestamp") == run_date).count()
        logging.info(f"[Stage: ingest_bronze] output_count: {output_count:,} rows")
        
    except Exception as e:
        logging.error(f"Error in ingest_bronze stage: {e}")
>>>>>>> 83d5fc253a8457c3903da527641897b01c810c15
        raise

def transform_silver(spark, bronze_path, merchants_path, output_path, run_date):
    try:
<<<<<<< HEAD
        logging.info("[Stage: Transform Silver] Starting transformation")
        transactions_df = (spark.read.format("parquet")
                           .load(bronze_path)
                          .where(col("ingestion_timestamp") == run_date))
        
        logging.info(f"[Stage: Transform Silver] Input count: {transactions_df.count():,}")
        
        transactions_df = transactions_df.withColumn("amount", col("amount").cast(FloatType()))
        transactions_df = transactions_df.withColumn("transaction_date", col("transaction_date").cast(DateType()))
        transactions_df = transactions_df.withColumn("transaction_id", col("transaction_id").cast(StringType()))
        transactions_df = transactions_df.withColumn("merchant_id", col("merchant_id").cast(StringType()))
        
        transactions_df = transactions_df.filter((col("transaction_id").isNotNull()) & (col("amount") >= 0))
        logging.info(f"[Stage: Transform Silver] After filter count: {transactions_df.count():,}")
        
        transactions_dedup_df = (transactions_df.orderBy(col("transaction_id"), col("ingestion_timestamp").desc())
                                .dropDuplicates(["transaction_id"]))
        logging.info(f"[Stage: Transform Silver] After dedup count: {transactions_dedup_df.count():,}")
        
        merchants_df = (spark.read.format("csv")
                        .option("header", "true")
                        .option("inferSchema", "false")
                       .load(merchants_path))
        merchants_df = merchants_df.withColumn("merchant_id", col("merchant_id").cast(StringType()))
        spark.catalog.cacheTable("merchants")
        
        enriched_df = (transactions_dedup_df.join(broadcast(merchants_df), "merchant_id", "left_outer")
                        .withColumn("quality_flag", when(col("merchant_id").isNull(), "UNMATCHED").otherwise("CLEAN")))
        
        partition_path = f"{output_path}/transaction_date={run_date}"
        shutil.rmtree(partition_path, ignore_errors=True)
        
        enriched_df.write.mode("overwrite").partitionBy("transaction_date").parquet(output_path)
        logging.info("[Stage: Transform Silver] Transformation completed successfully")
    except Exception as e:
        logging.error(f"[Stage: Transform Silver] Error: {e}")
=======
        logging.info("Starting transform_silver stage")
        partition_path = f"{output_path}/transaction_date={run_date}"
        shutil.rmtree(partition_path, ignore_errors=True)  # Idempotency: delete partition before write
        
        transactions_df = (spark.read.parquet(bronze_path)
                          .where(col("ingestion_timestamp") == run_date))  # Partition pruning
        
        transactions_df = (transactions_df.withColumn("amount", col("amount").cast(FloatType()))
                          .withColumn("transaction_date", col("transaction_date").cast(DateType())))
        
        filtered_df = transactions_df.filter((col("transaction_id").isNotNull()) & (col("amount") >= 0))
        after_filter_count = filtered_df.count()
        logging.info(f"[Stage: transform_silver] after_filter_count: {after_filter_count:,} rows")
        
        deduped_df = (filtered_df.groupBy("transaction_id")
                  .agg(max_("ingestion_timestamp").alias("latest_timestamp")))
        deduped_transactions_df = filtered_df.join(deduped_df, on=["transaction_id", "ingestion_timestamp"], how="left_semi")
        after_dedup_count = deduped_transactions_df.count()
        logging.info(f"[Stage: transform_silver] after_dedup_count: {after_dedup_count:,} rows")
        
        merchants_df = (spark.read.option("header", "true")
                       .option("inferSchema", "false")
                       .csv(merchants_path)
                      .withColumn("merchant_id", col("merchant_id").cast(StringType())))
        merchants_df = merchants_df.cache()
        
        enriched_df = (deduped_transactions_df.join(merchants_df, on="merchant_id", how="left")
                      .withColumn("quality_flag", coalesce(col("merchant_name"), lit("UNMATCHED"))))
        
        enriched_df.write.partitionBy("transaction_date").mode("overwrite").parquet(output_path)
        
        output_count = spark.read.parquet(output_path).where(col("transaction_date") == run_date).count()
        logging.info(f"[Stage: transform_silver] output_count: {output_count:,} rows")
        
    except Exception as e:
        logging.error(f"Error in transform_silver stage: {e}")
>>>>>>> 83d5fc253a8457c3903da527641897b01c810c15
        raise

def build_merchant_performance(spark, silver_path, output_path, run_date):
    try:
<<<<<<< HEAD
        logging.info("[Stage: Build Merchant Performance] Starting build")
        silver_df = (spark.read.parquet(silver_path)
                    .where(col("transaction_date") == run_date)
                     .withColumn("amount", col("amount").cast(FloatType())))
        
        completed_txns = silver_df.filter(col("status") == "COMPLETED")
        
        merchant_performance_df = (completed_txns.groupBy("merchant_id", "merchant_name", "category", "city", "transaction_date")
                                  .agg(sum("amount").alias("total_revenue"),
                                       count("*").alias("txn_count")))
        
        all_txns = silver_df.groupBy("merchant_id").agg(count("*").alias("total_txns"),
                                                        count(col("status").isin("FAILED")).alias("failed_txns"))
        failure_rate_df = all_txns.withColumn("failure_rate_pct", (col("failed_txns") / col("total_txns") * 100).cast(FloatType()))
        
        final_df = merchant_performance_df.join(failure_rate_df, on=["merchant_id"], how="left")
        
        partition_path = f"{output_path}/date={run_date}"
        shutil.rmtree(partition_path, ignore_errors=True)
        
        final_df.write.partitionBy("date").mode("overwrite").parquet(output_path)
        logging.info("[Stage: Build Merchant Performance] Build completed successfully")
    except Exception as e:
        logging.error(f"[Stage: Build Merchant Performance] Error: {e}")
=======
        logging.info("Starting build_merchant_performance stage")
        partition_path = f"{output_path}/date={run_date}"
        shutil.rmtree(partition_path, ignore_errors=True)  # Idempotency: delete partition before write
        
        silver_df = spark.read.parquet(silver_path).filter(col("date") == run_date)  # Partition pruning
        
        completed_df = silver_df.filter(col("status") == "COMPLETED")
        
        revenue_df = completed_df.groupBy("merchant_id", "merchant_name", "category", "city", "date") \
          .agg(sum("amount").alias("total_revenue"), count("*").alias("txn_count"))
        
        all_txns_df = silver_df.groupBy("merchant_id", "merchant_name", "category", "city", "date") \
          .agg(count("*").alias("total_txns"), count(when(col("status") == "FAILED", 1)).alias("failed_txns"))
        
        failure_rate_df = all_txns_df.withColumn("failure_rate_pct", (col("failed_txns") / col("total_txns") * 100).cast(FloatType()))
        
        merchant_performance_df = revenue_df.join(failure_rate_df, ["merchant_id", "merchant_name", "category", "city", "date"], "left") \
            .select("merchant_id", "merchant_name", "category", "city", "date", "total_revenue", "txn_count", "failure_rate_pct")
        
        merchant_performance_df.write.partitionBy("date").mode("overwrite").parquet(output_path)
        
    except Exception as e:
        logging.error(f"Error in build_merchant_performance stage: {e}")
>>>>>>> 83d5fc253a8457c3903da527641897b01c810c15
        raise

def build_customer_ltv(spark, silver_path, output_path):
    try:
<<<<<<< HEAD
        logging.info("[Stage: Build Customer LTV] Starting build")
        silver_df = (spark.read.parquet(silver_path)
                    .where(col("status") == "COMPLETED")
                    .withColumn("amount", col("amount").cast(FloatType())))
        
        ltv_df = (silver_df.groupBy("customer_id")
                 .agg(sum("amount").alias("total_spent"),
                      count("*").alias("total_txns"),
                      expr("avg(amount)").alias("avg_txn_value"),
                      min("transaction_date").alias("first_txn_date"),
                      max("transaction_date").alias("last_txn_date"),
                      mode("payment_method").over(Window.partitionBy("customer_id")).alias("preferred_payment_method")))
        
        shutil.rmtree(output_path, ignore_errors=True)
        
        ltv_df.write.mode("overwrite").parquet(output_path)
        logging.info("[Stage: Build Customer LTV] Build completed successfully")
    except Exception as e:
        logging.error(f"[Stage: Build Customer LTV] Error: {e}")
=======
        logging.info("Starting build_customer_ltv stage")
        
        silver_df = spark.read.parquet(silver_path)
        
        completed_df = silver_df.filter(col("status") == "COMPLETED")
        
        ltv_df = completed_df.groupBy("customer_id") \
          .agg(sum("amount").alias("total_spent"), count("*").alias("total_txns"), avg("amount").alias("avg_txn_value"), 
                 first("transaction_date").alias("first_txn_date"), last("transaction_date").alias("last_txn_date"), 
                 mode("payment_method").alias("preferred_payment_method"))
        
        ltv_df.write.mode("overwrite").parquet(output_path)
        
    except Exception as e:
        logging.error(f"Error in build_customer_ltv stage: {e}")
>>>>>>> 83d5fc253a8457c3903da527641897b01c810c15
        raise

def build_daily_summary(spark, silver_path, output_path, run_date):
    try:
<<<<<<< HEAD
        logging.info("[Stage: Build Daily Summary] Starting build")
        silver_df = (spark.read.parquet(silver_path)
                    .where(col("transaction_date") == run_date)
                    .withColumn("amount", col("amount").cast(FloatType())))
        
        daily_summary_df = (silver_df.groupBy("transaction_date")
                         .agg(sum("amount").alias("total_revenue"),
                               count("*").alias("total_txns"),
                               countDistinct("customer_id").alias("unique_customers"),
                               countDistinct("merchant_id").alias("unique_merchants")))
        
        all_txns = silver_df.groupBy("transaction_date").agg(count("*").alias("total_txns"),
                                                             count(col("status").isin("FAILED")).alias("failed_txns"))
        failure_rate_df = all_txns.withColumn("failure_rate_pct", (col("failed_txns") / col("total_txns") * 100).cast(FloatType()))
        
        final_df = daily_summary_df.join(failure_rate_df, on=["transaction_date"], how="left")
        
        partition_path = f"{output_path}/date={run_date}"
        shutil.rmtree(partition_path, ignore_errors=True)
        
        final_df.write.partitionBy("date").mode("overwrite").parquet(output_path)
        logging.info("[Stage: Build Daily Summary] Build completed successfully")
    except Exception as e:
        logging.error(f"[Stage: Build Daily Summary] Error: {e}")
=======
        logging.info("Starting build_daily_summary stage")
        partition_path = f"{output_path}/date={run_date}"
        shutil.rmtree(partition_path, ignore_errors=True)  # Idempotency: delete partition before write
        
        silver_df = spark.read.parquet(silver_path).filter(col("date") == run_date)  # Partition pruning
        
        total_revenue_df = silver_df.filter(col("status") == "COMPLETED") \
           .groupBy("date").agg(sum("amount").alias("total_revenue"), count("*").alias("total_txns"))
        
        unique_customers_df = silver_df.groupBy("date").agg(countDistinct("customer_id").alias("unique_customers"))
        
        unique_merchants_df = silver_df.groupBy("date").agg(countDistinct("merchant_id").alias("unique_merchants"))
        
        all_txns_df = silver_df.groupBy("date").agg(count("*").alias("total_txns"), count(when(col("status") == "FAILED", 1)).alias("failed_txns"))
        
        failure_rate_df = all_txns_df.withColumn("failure_rate_pct", (col("failed_txns") / col("total_txns") * 100).cast(FloatType()))
        
        daily_summary_df = total_revenue_df.join(unique_customers_df, "date", "inner") \
          .join(unique_merchants_df, "date", "inner") \
          .join(failure_rate_df, "date", "left") \
          .select("date", "total_revenue", "total_txns", "unique_customers", "unique_merchants", "failure_rate_pct")
        
        daily_summary_df.write.partitionBy("date").mode("overwrite").parquet(output_path)
        
    except Exception as e:
        logging.error(f"Error in build_daily_summary stage: {e}")
>>>>>>> 83d5fc253a8457c3903da527641897b01c810c15
        raise

def run_gold(spark, silver_path, gold_output_dir, run_date):
    try:
<<<<<<< HEAD
        logging.info("[Stage: Run Gold] Starting gold aggregation")
=======
        logging.info("Starting run_gold stage")
        
        run_metadata = {"run_date": run_date, "silver_path": silver_path, "gold_output_dir": gold_output_dir}
        
>>>>>>> 83d5fc253a8457c3903da527641897b01c810c15
        build_merchant_performance(spark, silver_path, f"{gold_output_dir}/merchant_performance", run_date)
        build_customer_ltv(spark, silver_path, f"{gold_output_dir}/customer_ltv")
        build_daily_summary(spark, silver_path, f"{gold_output_dir}/daily_summary", run_date)
        
<<<<<<< HEAD
        run_metadata = {
            "run_date": run_date,
            "silver_path": silver_path,
            "gold_output_dir": gold_output_dir,
            "tables_built": ["merchant_performance", "customer_ltv", "daily_summary"],
            "run_status": "SUCCESS",
            "started_at": datetime.now().isoformat(),
            "completed_at": datetime.now().isoformat()
        }
        
        with open(f"{gold_output_dir}/run_metadata.json", "w") as f:
            json.dump(run_metadata, f)
        
        logging.info("[Stage: Run Gold] Gold aggregation completed successfully")
    except Exception as e:
        logging.error(f"[Stage: Run Gold] Error: {e}")
        run_metadata = {
            "run_date": run_date,
            "silver_path": silver_path,
            "gold_output_dir": gold_output_dir,
            "tables_built": ["merchant_performance", "customer_ltv", "daily_summary"],
            "run_status": "FAILED",
            "error_message": str(e),
            "started_at": datetime.now().isoformat(),
            "completed_at": datetime.now().isoformat()
        }
        
        with open(f"{gold_output_dir}/run_metadata.json", "w") as f:
=======
        spark.sparkContext.parallelize([run_metadata]).write.json(f"{gold_output_dir}/run_metadata")
        
    except Exception as e:
        logging.error(f"Error in run_gold stage: {e}")
        raise

def main():
    try:
        logging.info("Starting main function")
        
        spark = (SparkSession.builder
                .appName("Sigma DataTech Transaction Analytics Pipeline")
                 .getOrCreate())
        
        input_path = "s3://sigma-datatech/bronze/transactions.csv"
        bronze_path = "s3://sigma-datatech/silver/transactions"
        merchants_path = "s3://sigma-datatech/bronze/merchants.csv"
        output_path = "s3://sigma-datatech/silver/transactions"
        gold_output_dir = "s3://sigma-datatech/gold"
        run_date = "2026-05-27"
        run_id = "run_id_20260527"
        
        started_at = datetime.now().isoformat()
        
        ingest_bronze(spark, input_path, bronze_path, run_date, run_id)
        transform_silver(spark, bronze_path, merchants_path, output_path, run_date)
        
        run_gold(spark, output_path, gold_output_dir, run_date)
        
        completed_at = datetime.now().isoformat()
        
        run_metadata = {
            "pipeline_name": "Sigma DataTech Transaction Analytics Pipeline",
            "run_date": run_date,
            "run_id": run_id,
            "run_status": "SUCCESS",
            "started_at": started_at,
            "completed_at": completed_at
        }
        
        with open(f"s3://sigma-datatech/metadata/run_metadata_{run_date}.json", "w") as f:
            json.dump(run_metadata, f)
            
    except Exception as e:
        logging.error(f"Error in main function: {e}")
        run_metadata["run_status"] = "FAILED"
        run_metadata["error_message"] = str(e)
        
        with open(f"s3://sigma-datatech/metadata/run_metadata_{run_date}.json", "w") as f:
>>>>>>> 83d5fc253a8457c3903da527641897b01c810c15
            json.dump(run_metadata, f)
        
        raise

<<<<<<< HEAD
def main():
    spark = (SparkSession.builder
            .appName("Sigma DataTech Transaction Analytics Pipeline")
             .getOrCreate())
    
    input_path = "s3://smitday7-genai/bronze/"
    bronze_path = "s3://smitday7-genai/silver/"
    merchants_path = "s3://smitday7-genai/dimensions/merchants.csv"
    output_path = "s3://smitday7-genai/silver/"
    gold_output_dir = "s3://smitday7-genai/gold/"
    run_date = "2026-05-27"
    run_id = "run_id_20260527"
    
    ingest_bronze(spark, input_path, output_path, run_date, run_id)
    transform_silver(spark, f"{bronze_path}/ingestion_timestamp={run_date}", merchants_path, f"{output_path}/transaction_date={run_date}", run_date)
    run_gold(spark, f"{output_path}/transaction_date={run_date}", gold_output_dir, run_date)

if __name__ == "__main__":
    main()
=======
if __name__ == "__main__":
    main()
>>>>>>> 83d5fc253a8457c3903da527641897b01c810c15
