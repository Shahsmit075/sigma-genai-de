"""Unit tests for athena_client.py — all AWS calls are mocked."""
import sys
import os
import pytest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from athena_client import AthenaClient


@pytest.fixture
def client():
    with patch('boto3.client') as mock_boto:
        mock_athena = MagicMock()
        mock_boto.return_value = mock_athena
        ac = AthenaClient('sigma-datatech-test', 'us-east-1')
        ac.athena = mock_athena
        return ac, mock_athena


class TestAthenaClientInit:
    def test_results_location_format(self, client):
        ac, _ = client
        assert ac.results_location == 's3://sigma-datatech-test/athena-results/'

    def test_database_name(self, client):
        ac, _ = client
        assert ac.database == 'sigma_db'

    def test_bucket_name_stored(self, client):
        ac, _ = client
        assert ac.bucket == 'sigma-datatech-test'


class TestExecuteQuery:
    def test_returns_execution_id(self, client):
        ac, mock = client
        mock.start_query_execution.return_value = {'QueryExecutionId': 'exec-abc-123'}
        exec_id = ac.execute_query('SELECT 1')
        assert exec_id == 'exec-abc-123'

    def test_uses_correct_results_location(self, client):
        ac, mock = client
        mock.start_query_execution.return_value = {'QueryExecutionId': 'x'}
        ac.execute_query('SELECT 1')
        call_kwargs = mock.start_query_execution.call_args[1]
        assert call_kwargs['ResultConfiguration']['OutputLocation'] == \
               's3://sigma-datatech-test/athena-results/'

    def test_uses_sigma_db_by_default(self, client):
        ac, mock = client
        mock.start_query_execution.return_value = {'QueryExecutionId': 'x'}
        ac.execute_query('SELECT 1')
        call_kwargs = mock.start_query_execution.call_args[1]
        assert call_kwargs['QueryExecutionContext']['Database'] == 'sigma_db'

    def test_accepts_custom_database(self, client):
        ac, mock = client
        mock.start_query_execution.return_value = {'QueryExecutionId': 'x'}
        ac.execute_query('SELECT 1', database='default')
        call_kwargs = mock.start_query_execution.call_args[1]
        assert call_kwargs['QueryExecutionContext']['Database'] == 'default'


class TestWaitForQuery:
    def test_returns_succeeded_on_success(self, client):
        ac, mock = client
        mock.get_query_execution.return_value = {
            'QueryExecution': {'Status': {'State': 'SUCCEEDED'}}
        }
        result = ac.wait_for_query('exec-id')
        assert result == 'SUCCEEDED'

    def test_raises_on_failed_state(self, client):
        ac, mock = client
        mock.get_query_execution.return_value = {
            'QueryExecution': {
                'Status': {'State': 'FAILED', 'StateChangeReason': 'Syntax error near SELECT'}
            }
        }
        with pytest.raises(Exception, match='FAILED'):
            ac.wait_for_query('exec-id')

    def test_raises_on_cancelled_state(self, client):
        ac, mock = client
        mock.get_query_execution.return_value = {
            'QueryExecution': {'Status': {'State': 'CANCELLED', 'StateChangeReason': ''}}
        }
        with pytest.raises(Exception, match='CANCELLED'):
            ac.wait_for_query('exec-id')


class TestGetResults:
    def test_parses_columns_correctly(self, client):
        ac, mock = client
        mock.get_query_results.return_value = {
            'ResultSet': {
                'ResultSetMetadata': {
                    'ColumnInfo': [{'Label': 'city'}, {'Label': 'revenue'}]
                },
                'Rows': [
                    {'Data': [{'VarCharValue': 'city'}, {'VarCharValue': 'revenue'}]},
                    {'Data': [{'VarCharValue': 'Mumbai'}, {'VarCharValue': '250000.0'}]},
                    {'Data': [{'VarCharValue': 'Delhi'}, {'VarCharValue': '180000.0'}]},
                ]
            }
        }
        df = ac.get_results('exec-id')
        assert list(df.columns) == ['city', 'revenue']
        assert len(df) == 2
        assert df.iloc[0]['city'] == 'Mumbai'

    def test_skips_header_row(self, client):
        ac, mock = client
        mock.get_query_results.return_value = {
            'ResultSet': {
                'ResultSetMetadata': {'ColumnInfo': [{'Label': 'count'}]},
                'Rows': [
                    {'Data': [{'VarCharValue': 'count'}]},    # header — must be skipped
                    {'Data': [{'VarCharValue': '42'}]},
                ]
            }
        }
        df = ac.get_results('exec-id')
        assert len(df) == 1
        assert df.iloc[0]['count'] == '42'

    def test_handles_empty_varchar(self, client):
        ac, mock = client
        mock.get_query_results.return_value = {
            'ResultSet': {
                'ResultSetMetadata': {'ColumnInfo': [{'Label': 'col'}]},
                'Rows': [
                    {'Data': [{'VarCharValue': 'col'}]},
                    {'Data': [{}]},   # missing VarCharValue
                ]
            }
        }
        df = ac.get_results('exec-id')
        assert df.iloc[0]['col'] == ''


class TestOrdersTableDDL:
    def test_orders_ddl_references_correct_bucket(self, client):
        ac, mock = client
        mock.start_query_execution.return_value = {'QueryExecutionId': 'ddl-id'}
        mock.get_query_execution.return_value = {
            'QueryExecution': {'Status': {'State': 'SUCCEEDED'}}
        }
        ac.create_orders_table()
        sql_used = mock.start_query_execution.call_args[1]['QueryString']
        assert 'sigma-datatech-test' in sql_used
        assert 'processed/orders/' in sql_used

    def test_customers_ddl_references_correct_bucket(self, client):
        ac, mock = client
        mock.start_query_execution.return_value = {'QueryExecutionId': 'ddl-id'}
        mock.get_query_execution.return_value = {
            'QueryExecution': {'Status': {'State': 'SUCCEEDED'}}
        }
        ac.create_customers_table()
        sql_used = mock.start_query_execution.call_args[1]['QueryString']
        assert 'sigma-datatech-test' in sql_used
        assert 'processed/customers/' in sql_used
