import sys
import json
import io
import logging
from datetime import datetime
import argparse
import boto3
import pandas as pd

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

def run_job():
    logger.info("Starting QuickMart Glue ETL Job")
    
    # Parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('--bucket_name', required=True)
    parser.add_argument('--date_partition', required=True)
    parser.add_argument('--job_type', required=True)
    args, unknown = parser.parse_known_args()
    
    bucket_name = args.bucket_name
    date_partition = args.date_partition
    job_type = args.job_type
    
    logger.info(f"Arguments parsed: bucket_name={bucket_name}, date_partition={date_partition}, job_type={job_type}")
    
    s3 = boto3.client('s3')
    
    if job_type == "orders":
        raw_key = f"raw/orders/date={date_partition}/orders.csv"
        processed_key = f"processed/orders/date={date_partition}/orders.csv"
        report_key = f"reports/quality_report_{date_partition}.json"
        
        logger.info(f"Reading raw orders from s3://{bucket_name}/{raw_key}")
        try:
            response = s3.get_object(Bucket=bucket_name, Key=raw_key)
            df = pd.read_csv(io.BytesIO(response['Body'].read()))
        except Exception as e:
            logger.error(f"Error reading file from S3: {str(e)}")
            raise e
            
        input_rows = len(df)
        logger.info(f"Successfully loaded {input_rows} input rows")
        
        # Count quality issues
        null_customer_ids = int(df['customer_id'].isna().sum())
        negative_amounts = int((df['amount'] < 0).sum())
        duplicate_order_ids = int(df.duplicated(subset=['order_id']).sum())
        
        logger.info(f"Defect counts: null_customer_ids={null_customer_ids}, negative_amounts={negative_amounts}, duplicate_order_ids={duplicate_order_ids}")
        
        # Fix issues
        # Drop null customer_ids
        df_cleaned = df.dropna(subset=['customer_id']).copy()
        
        # abs() negative amounts
        df_cleaned['amount'] = df_cleaned['amount'].abs()
        
        # drop_duplicates on order_id keeping first
        df_cleaned = df_cleaned.drop_duplicates(subset=['order_id'], keep='first').copy()
        
        # Add column processed_at = current UTC timestamp (string)
        current_time = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        df_cleaned['processed_at'] = current_time
        
        # Add column is_high_value = True if amount > 2000 else False (string)
        df_cleaned['is_high_value'] = (df_cleaned['amount'] > 2000).astype(str)
        
        # Add column transaction_tier = "BULK" if quantity >= 10 else "STANDARD"
        df_cleaned['transaction_tier'] = df_cleaned['quantity'].apply(lambda q: "BULK" if q >= 10 else "STANDARD")
        
        output_rows = len(df_cleaned)
        rows_dropped = input_rows - output_rows
        
        status = "CLEAN" if (null_customer_ids == 0 and negative_amounts == 0 and duplicate_order_ids == 0) else "ISSUES_FOUND"
        
        logger.info(f"Cleaned data output: {output_rows} rows. Rows dropped: {rows_dropped}. Status: {status}")
        
        # Write cleaned CSV to S3
        logger.info(f"Writing cleaned CSV to s3://{bucket_name}/{processed_key}")
        csv_data = df_cleaned.to_csv(index=False).encode('utf-8')
        s3.put_object(Bucket=bucket_name, Key=processed_key, Body=csv_data)
        
        # Write JSON quality report to S3
        logger.info(f"Writing quality report to s3://{bucket_name}/{report_key}")
        report_data = {
            "date": date_partition,
            "input_rows": input_rows,
            "output_rows": output_rows,
            "null_customer_ids": null_customer_ids,
            "negative_amounts": negative_amounts,
            "duplicate_order_ids": duplicate_order_ids,
            "rows_dropped": rows_dropped,
            "status": status
        }
        s3.put_object(
            Bucket=bucket_name,
            Key=report_key,
            Body=json.dumps(report_data, indent=2).encode('utf-8'),
            ContentType='application/json'
        )
        logger.info("Orders job successfully completed")
        
    elif job_type == "reference":
        logger.info("Executing reference data copy job")
        
        # Copy customers.csv
        logger.info(f"Copying raw/customers.csv to processed/customers/customers.csv")
        s3.copy_object(
            Bucket=bucket_name,
            CopySource={'Bucket': bucket_name, 'Key': 'raw/customers.csv'},
            Key='processed/customers/customers.csv'
        )
        
        # Copy products.csv
        logger.info(f"Copying raw/products.csv to processed/products/products.csv")
        s3.copy_object(
            Bucket=bucket_name,
            CopySource={'Bucket': bucket_name, 'Key': 'raw/products.csv'},
            Key='processed/products/products.csv'
        )
        logger.info("Reference data copy job successfully completed")
        
    else:
        raise ValueError(f"Unknown job_type: {job_type}")

if __name__ == '__main__':
    try:
        run_job()
    except Exception as e:
        logger.error(f"ETL Job failed with error: {str(e)}")
        raise e
