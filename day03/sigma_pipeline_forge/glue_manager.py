"""Glue Python Shell job management for Sigma DataTech pipeline."""
import boto3
import json
import time
import logging

logger = logging.getLogger(__name__)

JOB_NAME = 'sigma-datatech-etl'
ROLE_NAME = 'SigmaGlueServiceRole'


class GlueManager:
    def __init__(self, bucket_name: str, region: str = 'us-east-1'):
        self.bucket = bucket_name
        self.region = region
        self.glue = boto3.client('glue', region_name=region)
        self.iam = boto3.client('iam', region_name=region)
        self.sts = boto3.client('sts', region_name=region)

    # ── IAM ────────────────────────────────────────────────────────────────────
    def ensure_iam_role(self) -> str:
        try:
            role = self.iam.get_role(RoleName=ROLE_NAME)
            logger.info(f"IAM role {ROLE_NAME} exists")
            return role['Role']['Arn']
        except self.iam.exceptions.NoSuchEntityException:
            logger.info(f"Creating IAM role {ROLE_NAME}...")
            assume = {
                "Version": "2012-10-17",
                "Statement": [{
                    "Effect": "Allow",
                    "Principal": {"Service": "glue.amazonaws.com"},
                    "Action": "sts:AssumeRole"
                }]
            }
            role = self.iam.create_role(
                RoleName=ROLE_NAME,
                AssumeRolePolicyDocument=json.dumps(assume),
                Description='Sigma DataTech Glue ETL Role'
            )
            self.iam.attach_role_policy(
                RoleName=ROLE_NAME,
                PolicyArn='arn:aws:iam::aws:policy/service-role/AWSGlueServiceRole'
            )
            self.iam.attach_role_policy(
                RoleName=ROLE_NAME,
                PolicyArn='arn:aws:iam::aws:policy/AmazonS3FullAccess'
            )
            logger.info("IAM role created. Waiting 12s for propagation...")
            time.sleep(12)
            return role['Role']['Arn']

    # ── Job deployment ──────────────────────────────────────────────────────────
    def deploy_job(self, script_s3_key: str) -> bool:
        role_arn = self.ensure_iam_role()
        script_location = f's3://{self.bucket}/{script_s3_key}'

        # Delete existing job if present
        try:
            self.glue.delete_job(JobName=JOB_NAME)
            logger.info(f"Deleted existing job {JOB_NAME}")
        except Exception:
            pass

        self.glue.create_job(
            Name=JOB_NAME,
            Role=role_arn,
            Command={
                'Name': 'pythonshell',
                'ScriptLocation': script_location,
                'PythonVersion': '3.9'
            },
            DefaultArguments={
                '--TempDir': f's3://{self.bucket}/temp/',
                '--enable-job-insights': 'false',
            },
            MaxCapacity=0.0625,   # 1/16 DPU — cheapest, sufficient for 500-row CSVs
            MaxRetries=0,
            Timeout=10,           # 10-minute hard cap
            Description='Sigma DataTech ETL — AI-Assisted Pipeline Forge'
        )
        logger.info(f"Glue job {JOB_NAME} deployed")
        return True

    # ── Job execution ───────────────────────────────────────────────────────────
    def run_job(self, job_type: str = 'orders', date_partition: str = '') -> str:
        response = self.glue.start_job_run(
            JobName=JOB_NAME,
            Arguments={
                '--bucket_name': self.bucket,
                '--date_partition': date_partition,
                '--job_type': job_type,
            }
        )
        run_id = response['JobRunId']
        logger.info(f"Started job run {run_id} (type={job_type}, date={date_partition})")
        return run_id

    def get_job_status(self, run_id: str) -> dict:
        response = self.glue.get_job_run(JobName=JOB_NAME, RunId=run_id)
        run = response['JobRun']
        return {
            'status': run['JobRunState'],
            'duration_seconds': run.get('ExecutionTime', 0),
            'error': run.get('ErrorMessage', ''),
        }

    def wait_for_completion(self, run_id: str, timeout: int = 300) -> dict:
        deadline = time.time() + timeout
        while time.time() < deadline:
            status = self.get_job_status(run_id)
            if status['status'] in ('SUCCEEDED', 'FAILED', 'ERROR', 'STOPPED'):
                return status
            time.sleep(5)
        return {'status': 'TIMEOUT', 'duration_seconds': 0, 'error': 'Timed out'}

    def job_exists(self) -> bool:
        try:
            self.glue.get_job(JobName=JOB_NAME)
            return True
        except Exception:
            return False
