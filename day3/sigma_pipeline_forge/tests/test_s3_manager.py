"""Unit tests for s3_manager.py — all AWS calls are mocked."""
import sys
import os
import json
import pytest
from unittest.mock import MagicMock, patch, call

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from s3_manager import S3Manager


@pytest.fixture
def manager():
    with patch('boto3.client') as mock_boto:
        mock_client = MagicMock()
        mock_boto.return_value = mock_client
        mgr = S3Manager('sigma-datatech-test', 'us-east-1')
        mgr.s3 = mock_client   # override so we control all calls
        return mgr, mock_client


class TestS3ManagerInit:
    def test_bucket_name_stored(self, manager):
        mgr, _ = manager
        assert mgr.bucket == 'sigma-datatech-test'

    def test_region_stored(self, manager):
        mgr, _ = manager
        assert mgr.region == 'us-east-1'

    def test_bucket_url_format(self, manager):
        mgr, _ = manager
        assert mgr.get_bucket_url() == 's3://sigma-datatech-test'


class TestEnsureBucketExists:
    def test_returns_true_when_bucket_exists(self, manager):
        mgr, client = manager
        client.head_bucket.return_value = {}
        assert mgr.ensure_bucket_exists() is True
        client.head_bucket.assert_called_once_with(Bucket='sigma-datatech-test')

    def test_creates_bucket_when_missing(self, manager):
        mgr, client = manager
        client.head_bucket.side_effect = Exception("NoSuchBucket")
        client.create_bucket.return_value = {}
        mgr.ensure_bucket_exists()
        client.create_bucket.assert_called_once_with(Bucket='sigma-datatech-test')

    def test_returns_true_after_creating(self, manager):
        mgr, client = manager
        client.head_bucket.side_effect = Exception("NoSuchBucket")
        client.create_bucket.return_value = {}
        assert mgr.ensure_bucket_exists() is True


class TestFileExists:
    def test_returns_true_when_file_present(self, manager):
        mgr, client = manager
        client.head_object.return_value = {}
        assert mgr.file_exists('raw/orders/test.csv') is True

    def test_returns_false_when_file_missing(self, manager):
        mgr, client = manager
        client.head_object.side_effect = Exception("404")
        assert mgr.file_exists('raw/orders/missing.csv') is False

    def test_uses_correct_bucket_and_key(self, manager):
        mgr, client = manager
        client.head_object.return_value = {}
        mgr.file_exists('some/key.csv')
        client.head_object.assert_called_once_with(
            Bucket='sigma-datatech-test', Key='some/key.csv'
        )


class TestUploadString:
    def test_upload_string_calls_put_object(self, manager):
        mgr, client = manager
        client.put_object.return_value = {}
        result = mgr.upload_string("hello,world\n1,2", "glue-scripts/etl.py")
        assert result is True
        client.put_object.assert_called_once_with(
            Bucket='sigma-datatech-test',
            Key='glue-scripts/etl.py',
            Body=b"hello,world\n1,2"
        )

    def test_encodes_utf8(self, manager):
        mgr, client = manager
        client.put_object.return_value = {}
        mgr.upload_string("नमस्ते", "test.txt")
        args = client.put_object.call_args[1]
        assert isinstance(args['Body'], bytes)


class TestReadJson:
    def test_reads_and_parses_json(self, manager):
        mgr, client = manager
        payload = json.dumps({"status": "success", "input_rows": 500}).encode()
        client.get_object.return_value = {'Body': MagicMock(read=lambda: payload)}
        result = mgr.read_json('reports/quality_report.json')
        assert result['status'] == 'success'
        assert result['input_rows'] == 500

    def test_uses_correct_bucket_and_key(self, manager):
        mgr, client = manager
        client.get_object.return_value = {
            'Body': MagicMock(read=lambda: b'{"x":1}')
        }
        mgr.read_json('reports/test.json')
        client.get_object.assert_called_once_with(
            Bucket='sigma-datatech-test', Key='reports/test.json'
        )


class TestListObjects:
    def test_returns_list_of_keys(self, manager):
        mgr, client = manager
        client.list_objects_v2.return_value = {
            'Contents': [
                {'Key': 'raw/orders/day1.csv'},
                {'Key': 'raw/orders/day2.csv'},
            ]
        }
        keys = mgr.list_objects('raw/orders/')
        assert keys == ['raw/orders/day1.csv', 'raw/orders/day2.csv']

    def test_returns_empty_list_when_no_objects(self, manager):
        mgr, client = manager
        client.list_objects_v2.return_value = {}
        assert mgr.list_objects('empty/prefix/') == []
