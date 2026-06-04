"""
Sigma DataTech ETL — Glue Python Shell Job (Python 3.9)
Reads raw CSV from S3, validates and transforms, writes clean CSV back to S3.
Writes a JSON quality report for every orders run.

Job arguments:
  --bucket_name      S3 bucket (e.g. sigma-datatech-ak)
  --date_partition   Date string YYYY-MM-DD (for orders job type)
  --job_type         'orders' or 'reference'
"""
import boto3
import pandas as pd
import io
import json
import sys
import logging
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)


# ── Argument parsing (no awsglue dependency needed for Python Shell) ─────────
def parse_args() -> dict:
    args = {}
    argv = sys.argv[1:]
    for i in range(0, len(argv) - 1, 2):
        if argv[i].startswith('--'):
            args[argv[i][2:]] = argv[i + 1]
    return args


# ── S3 helpers ────────────────────────────────────────────────────────────────
def read_csv(s3, bucket: str, key: str) -> pd.DataFrame:
    obj = s3.get_object(Bucket=bucket, Key=key)
    df = pd.read_csv(io.BytesIO(obj['Body'].read()))
    logger.info(f"Read {len(df)} rows from s3://{bucket}/{key}")
    return df


def write_csv(s3, df: pd.DataFrame, bucket: str, key: str):
    buffer = io.StringIO()
    df.to_csv(buffer, index=False)
    s3.put_object(Bucket=bucket, Key=key, Body=buffer.getvalue().encode('utf-8'))
    logger.info(f"Wrote {len(df)} rows to s3://{bucket}/{key}")


def write_json(s3, data: dict, bucket: str, key: str):
    s3.put_object(Bucket=bucket, Key=key, Body=json.dumps(data, indent=2).encode('utf-8'))
    logger.info(f"Quality report → s3://{bucket}/{key}")


# ── ETL logic ─────────────────────────────────────────────────────────────────
def process_orders(s3, bucket: str, date_partition: str) -> dict:
    in_key = f'raw/orders/date={date_partition}/orders.csv'
    out_key = f'processed/orders/date={date_partition}/orders.csv'

    df = read_csv(s3, bucket, in_key)
    input_rows = len(df)

    # ── Data quality counts (before fixing) ──────────────────────────────────
    null_customers = int(df['customer_id'].isnull().sum())
    negative_amounts = int((df['amount'] < 0).sum())
    duplicate_orders = int(df.duplicated(subset=['order_id']).sum())

    logger.info(
        f"Quality check → null customer_ids: {null_customers}, "
        f"negative amounts: {negative_amounts}, "
        f"duplicate order_ids: {duplicate_orders}"
    )

    # ── Transformations ───────────────────────────────────────────────────────
    df = df.dropna(subset=['customer_id'])
    df['amount'] = df['amount'].abs()
    df = df.drop_duplicates(subset=['order_id'], keep='first')
    df['processed_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    df['is_high_value'] = (df['amount'] > 10000)

    write_csv(s3, df, bucket, out_key)

    return {
        'date': date_partition,
        'job_type': 'orders',
        'input_rows': input_rows,
        'output_rows': len(df),
        'null_customer_ids': null_customers,
        'negative_amounts': negative_amounts,
        'duplicate_order_ids': duplicate_orders,
        'rows_dropped': input_rows - len(df),
        'status': 'success',
        'processed_at': datetime.now().isoformat(),
    }


def process_reference(s3, bucket: str):
    for table in ('customers', 'products'):
        df = read_csv(s3, bucket, f'raw/{table}/{table}.csv')
        write_csv(s3, df, bucket, f'processed/{table}/{table}.csv')
    logger.info("Reference data processed")


# ── Main ──────────────────────────────────────────────────────────────────────
args = parse_args()
BUCKET = args.get('bucket_name', '')
DATE_PARTITION = args.get('date_partition', '')
JOB_TYPE = args.get('job_type', 'orders')

if not BUCKET:
    raise ValueError("--bucket_name argument is required")

logger.info(f"Starting Sigma DataTech ETL | bucket={BUCKET} | type={JOB_TYPE} | date={DATE_PARTITION}")

s3 = boto3.client('s3', region_name='us-east-1')

try:
    if JOB_TYPE == 'orders':
        if not DATE_PARTITION:
            raise ValueError("--date_partition is required for job_type=orders")
        report = process_orders(s3, BUCKET, DATE_PARTITION)
        write_json(s3, report, BUCKET, f'reports/quality_report_orders_{DATE_PARTITION}.json')

    elif JOB_TYPE == 'reference':
        process_reference(s3, BUCKET)

    else:
        raise ValueError(f"Unknown job_type: {JOB_TYPE}")

    logger.info("ETL job completed successfully")

except Exception as e:
    logger.error(f"ETL job FAILED: {e}")
    raise
