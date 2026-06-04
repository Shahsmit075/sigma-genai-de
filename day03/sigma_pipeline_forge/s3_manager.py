"""S3 operations for Sigma DataTech pipeline."""
import boto3
import json
import logging

logger = logging.getLogger(__name__)


class S3Manager:
    def __init__(self, bucket_name: str, region: str = 'us-east-1'):
        self.bucket = bucket_name
        self.region = region
        self.s3 = boto3.client('s3', region_name=region)

    def ensure_bucket_exists(self) -> bool:
        try:
            self.s3.head_bucket(Bucket=self.bucket)
            logger.info(f"Bucket {self.bucket} already exists")
            return True
        except Exception:
            self.s3.create_bucket(Bucket=self.bucket)
            logger.info(f"Created bucket {self.bucket}")
            return True

    def upload_file(self, local_path: str, s3_key: str) -> bool:
        self.s3.upload_file(local_path, self.bucket, s3_key)
        logger.info(f"Uploaded {local_path} → s3://{self.bucket}/{s3_key}")
        return True

    def upload_string(self, content: str, s3_key: str) -> bool:
        self.s3.put_object(Bucket=self.bucket, Key=s3_key, Body=content.encode('utf-8'))
        logger.info(f"Uploaded string → s3://{self.bucket}/{s3_key}")
        return True

    def file_exists(self, s3_key: str) -> bool:
        try:
            self.s3.head_object(Bucket=self.bucket, Key=s3_key)
            return True
        except Exception:
            return False

    def read_json(self, s3_key: str) -> dict:
        obj = self.s3.get_object(Bucket=self.bucket, Key=s3_key)
        return json.loads(obj['Body'].read().decode('utf-8'))

    def list_objects(self, prefix: str) -> list:
        response = self.s3.list_objects_v2(Bucket=self.bucket, Prefix=prefix)
        return [obj['Key'] for obj in response.get('Contents', [])]

    def get_bucket_url(self) -> str:
        return f"s3://{self.bucket}"
