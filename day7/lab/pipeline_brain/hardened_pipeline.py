import logging
import shutil
from datetime import datetime
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, lit, broadcast, when, sum, count, max, expr, mode, to_date
from pyspark.sql.types import FloatType, StringType, DateType
import json
import os

logging.basicConfig(level=logging.INFO)

def ingest_bronze(spark, input_path, output_path, run_date, run_id):
    try:
        logging.info("[Stage: Ingest Bronze] Starting ingestion")
        transactions_df = (spark.read.format("csv")
                          .option("header", "true")
                          .option("inferSchema", "false")
                          .load(input_path))
        
        logging.info(f"[Stage: Ingest Bronze] Input count: {transactions_df.count():,}")
        
        transactions_df = (transactions_df.withColumn("ingestion_timestamp", lit(run_date))
                           .withColumn("source_file", lit("transactions.csv"))
                          .withColumn("pipeline_run_id", lit(run_id)))
        
        partition_path = f"{output_path}/ingestion_timestamp={run_date}"
        shutil.rmtree(partition_path, ignore_errors=True)
        
        transactions_df.write.mode("overwrite").partitionBy("ingestion_timestamp").parquet(output_path)
        logging.info("[Stage: Ingest Bronze] Ingestion completed successfully")
    except Exception as e:
        logging.error(f"[Stage: Ingest Bronze] Error: {e}")
        raise

def transform_silver(spark, bronze_path, merchants_path, output_path, run_date):
    try:
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
        raise

def build_merchant_performance(spark, silver_path, output_path, run_date):
    try:
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
        raise

def build_customer_ltv(spark, silver_path, output_path):
    try:
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
        raise

def build_daily_summary(spark, silver_path, output_path, run_date):
    try:
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
        raise

def run_gold(spark, silver_path, gold_output_dir, run_date):
    try:
        logging.info("[Stage: Run Gold] Starting gold aggregation")
        build_merchant_performance(spark, silver_path, f"{gold_output_dir}/merchant_performance", run_date)
        build_customer_ltv(spark, silver_path, f"{gold_output_dir}/customer_ltv")
        build_daily_summary(spark, silver_path, f"{gold_output_dir}/daily_summary", run_date)
        
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
            json.dump(run_metadata, f)
        
        raise

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
