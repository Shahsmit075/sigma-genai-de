"""Unit tests for prompt_builder.py — no AWS calls required."""
import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from prompt_builder import (
    build_glue_etl_prompt,
    build_nl2sql_prompt,
    build_data_quality_prompt,
    build_query_explanation_prompt,
    build_health_summary_prompt,
    SCHEMA_CONTEXT,
    QUICK_QUESTIONS,
    SYSTEM_PROMPT,
)


class TestGlueEtlPrompt:
    def test_bucket_name_in_prompt(self):
        p = build_glue_etl_prompt('my-test-bucket', ['order_id', 'amount'])
        assert 'my-test-bucket' in p

    def test_all_columns_in_prompt(self):
        cols = ['order_id', 'customer_id', 'amount', 'city']
        p = build_glue_etl_prompt('bucket', cols)
        for col in cols:
            assert col in p

    def test_key_requirements_present(self):
        p = build_glue_etl_prompt('bucket', ['order_id'])
        assert 'logging' in p.lower()
        assert 'null' in p.lower()
        assert 'duplicate' in p.lower()
        assert 'negative' in p.lower()

    def test_both_job_types_mentioned(self):
        p = build_glue_etl_prompt('bucket', ['order_id'])
        assert 'orders' in p
        assert 'reference' in p

    def test_no_markdown_fence_instruction(self):
        p = build_glue_etl_prompt('bucket', ['order_id'])
        assert 'No explanation' in p or 'no markdown' in p.lower()

    def test_returns_string(self):
        p = build_glue_etl_prompt('bucket', [])
        assert isinstance(p, str)
        assert len(p) > 100


class TestNl2SqlPrompt:
    def test_question_in_prompt(self):
        p = build_nl2sql_prompt("top 5 customers by revenue", SCHEMA_CONTEXT)
        assert "top 5 customers by revenue" in p

    def test_schema_context_in_prompt(self):
        p = build_nl2sql_prompt("any question", SCHEMA_CONTEXT)
        assert 'sigma_db' in p
        assert 'orders' in p
        assert 'customers' in p

    def test_athena_sql_instructions(self):
        p = build_nl2sql_prompt("q", SCHEMA_CONTEXT)
        assert 'Athena' in p or 'Presto' in p

    def test_no_markdown_instruction(self):
        p = build_nl2sql_prompt("q", SCHEMA_CONTEXT)
        assert 'no markdown' in p.lower() or 'no code fences' in p.lower()


class TestDataQualityPrompt:
    def test_report_data_in_prompt(self):
        report = '{"input_rows": 500, "null_customer_ids": 3, "status": "success"}'
        p = build_data_quality_prompt(report)
        assert '500' in p
        assert '3' in p

    def test_asks_for_status(self):
        p = build_data_quality_prompt('{}')
        assert 'HEALTHY' in p or 'status' in p.lower()

    def test_asks_for_recommendation(self):
        p = build_data_quality_prompt('{}')
        assert 'recommendation' in p.lower() or 'recommend' in p.lower()


class TestQueryExplanationPrompt:
    def test_question_in_prompt(self):
        p = build_query_explanation_prompt("top customers", "SELECT 1", "5 rows")
        assert "top customers" in p

    def test_sql_in_prompt(self):
        p = build_query_explanation_prompt("q", "SELECT city FROM orders", "3 rows")
        assert "SELECT city FROM orders" in p

    def test_result_summary_in_prompt(self):
        p = build_query_explanation_prompt("q", "SELECT 1", "42 rows returned")
        assert "42 rows" in p

    def test_no_jargon_instruction(self):
        p = build_query_explanation_prompt("q", "SELECT 1", "1 row")
        assert 'jargon' in p.lower() or 'plain' in p.lower()


class TestHealthSummaryPrompt:
    def test_reports_data_in_prompt(self):
        reports = '[{"date": "2024-01-15", "input_rows": 500}]'
        p = build_health_summary_prompt(reports)
        assert '2024-01-15' in p
        assert '500' in p

    def test_asks_for_executive_summary(self):
        p = build_health_summary_prompt('[]')
        assert 'executive' in p.lower() or 'summary' in p.lower()


class TestSchemaAndConstants:
    def test_schema_has_all_three_tables(self):
        for table in ('orders', 'customers', 'products'):
            assert table in SCHEMA_CONTEXT

    def test_schema_has_partition_key(self):
        assert 'partition' in SCHEMA_CONTEXT.lower()

    def test_quick_questions_count(self):
        assert len(QUICK_QUESTIONS) == 5

    def test_quick_questions_are_non_empty_strings(self):
        for q in QUICK_QUESTIONS:
            assert isinstance(q, str) and len(q) > 15

    def test_system_prompt_is_non_empty(self):
        assert isinstance(SYSTEM_PROMPT, str) and len(SYSTEM_PROMPT) > 50
