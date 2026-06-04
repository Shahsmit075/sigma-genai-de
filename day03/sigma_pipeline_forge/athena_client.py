"""Athena query client for Sigma DataTech analytics."""
import boto3
import time
import pandas as pd
import logging

logger = logging.getLogger(__name__)

DATABASE = 'sigma_db'


class AthenaClient:
    def __init__(self, bucket_name: str, region: str = 'us-east-1'):
        self.bucket = bucket_name
        self.region = region
        self.athena = boto3.client('athena', region_name=region)
        self.results_location = f's3://{bucket_name}/athena-results/'
        self.database = DATABASE

    # ── Core query execution ────────────────────────────────────────────────────
    def execute_query(self, sql: str, database: str = None) -> str:
        response = self.athena.start_query_execution(
            QueryString=sql,
            QueryExecutionContext={'Database': database or self.database},
            ResultConfiguration={'OutputLocation': self.results_location}
        )
        return response['QueryExecutionId']

    def wait_for_query(self, execution_id: str, timeout: int = 60) -> str:
        deadline = time.time() + timeout
        while time.time() < deadline:
            response = self.athena.get_query_execution(QueryExecutionId=execution_id)
            state = response['QueryExecution']['Status']['State']
            if state == 'SUCCEEDED':
                return 'SUCCEEDED'
            if state in ('FAILED', 'CANCELLED'):
                reason = response['QueryExecution']['Status'].get('StateChangeReason', '')
                raise Exception(f"Athena query {state}: {reason}")
            time.sleep(2)
        raise Exception("Athena query timed out")

    def get_results(self, execution_id: str) -> pd.DataFrame:
        result = self.athena.get_query_results(QueryExecutionId=execution_id)
        columns = [c['Label'] for c in result['ResultSet']['ResultSetMetadata']['ColumnInfo']]
        rows = [
            [col.get('VarCharValue', '') for col in row['Data']]
            for row in result['ResultSet']['Rows'][1:]   # skip header row
        ]
        return pd.DataFrame(rows, columns=columns)

    def run_query(self, sql: str, database: str = None) -> pd.DataFrame:
        exec_id = self.execute_query(sql, database)
        self.wait_for_query(exec_id)
        return self.get_results(exec_id)

    # ── One-time setup ──────────────────────────────────────────────────────────
    def setup_database(self) -> bool:
        exec_id = self.execute_query(
            f'CREATE DATABASE IF NOT EXISTS {self.database}',
            database='default'
        )
        self.wait_for_query(exec_id)
        logger.info(f"Database {self.database} ready")
        return True

    def create_orders_table(self) -> bool:
        ddl = f"""
        CREATE EXTERNAL TABLE IF NOT EXISTS {self.database}.orders (
            order_id        STRING,
            customer_id     STRING,
            product_id      STRING,
            amount          DOUBLE,
            status          STRING,
            payment_method  STRING,
            created_at      STRING,
            city            STRING,
            processed_at    STRING,
            is_high_value   STRING
        )
        PARTITIONED BY (date STRING)
        ROW FORMAT DELIMITED
        FIELDS TERMINATED BY ','
        STORED AS TEXTFILE
        LOCATION 's3://{self.bucket}/processed/orders/'
        TBLPROPERTIES ('skip.header.line.count'='1')
        """
        exec_id = self.execute_query(ddl)
        self.wait_for_query(exec_id)
        logger.info("orders table created")
        return True

    def create_customers_table(self) -> bool:
        ddl = f"""
        CREATE EXTERNAL TABLE IF NOT EXISTS {self.database}.customers (
            customer_id  STRING,
            name         STRING,
            email        STRING,
            phone        STRING,
            city         STRING,
            tier         STRING,
            signup_date  STRING
        )
        ROW FORMAT DELIMITED
        FIELDS TERMINATED BY ','
        STORED AS TEXTFILE
        LOCATION 's3://{self.bucket}/processed/customers/'
        TBLPROPERTIES ('skip.header.line.count'='1')
        """
        exec_id = self.execute_query(ddl)
        self.wait_for_query(exec_id)
        logger.info("customers table created")
        return True

    def create_products_table(self) -> bool:
        ddl = f"""
        CREATE EXTERNAL TABLE IF NOT EXISTS {self.database}.products (
            product_id  STRING,
            name        STRING,
            category    STRING,
            price       DOUBLE,
            is_active   STRING
        )
        ROW FORMAT DELIMITED
        FIELDS TERMINATED BY ','
        STORED AS TEXTFILE
        LOCATION 's3://{self.bucket}/processed/products/'
        TBLPROPERTIES ('skip.header.line.count'='1')
        """
        exec_id = self.execute_query(ddl)
        self.wait_for_query(exec_id)
        logger.info("products table created")
        return True

    def refresh_partitions(self) -> bool:
        exec_id = self.execute_query(f'MSCK REPAIR TABLE {self.database}.orders')
        self.wait_for_query(exec_id)
        logger.info("Partitions refreshed")
        return True

    def table_exists(self, table_name: str) -> bool:
        try:
            result = self.run_query(
                f"SHOW TABLES IN {self.database} LIKE '{table_name}'"
            )
            return len(result) > 0
        except Exception:
            return False
