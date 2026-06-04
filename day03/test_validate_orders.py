import pytest
import pandas as pd
from validate_orders import validate_orders


def test_validate_orders_happy_path():
    """Test valid orders pass validation."""
    df = pd.DataFrame({
        'order_id': [1, 2, 3],
        'amount': [100.50, 200.00, 50.25],
        'created_at': ['2024-01-15', '2024-01-16', '2024-01-17']
    })
    assert validate_orders(df) is True


def test_validate_orders_null_order_ids():
    """Test that null order_ids raise ValueError."""
    df = pd.DataFrame({
        'order_id': [1, None, 3],
        'amount': [100.0, 200.0, 300.0],
        'created_at': ['2024-01-15', '2024-01-16', '2024-01-17']
    })
    with pytest.raises(ValueError, match="null order_id"):
        validate_orders(df)


def test_validate_orders_non_positive_amount():
    """Test that non-positive amounts raise ValueError."""
    df = pd.DataFrame({
        'order_id': [1, 2, 3],
        'amount': [100.0, -50.0, 300.0],
        'created_at': ['2024-01-15', '2024-01-16', '2024-01-17']
    })
    with pytest.raises(ValueError, match="non-positive amount"):
        validate_orders(df)


def test_validate_orders_invalid_date():
    """Test that invalid dates raise ValueError."""
    df = pd.DataFrame({
        'order_id': [1, 2, 3],
        'amount': [100.0, 200.0, 300.0],
        'created_at': ['2024-01-15', 'not-a-date', '2024-01-17']
    })
    with pytest.raises(ValueError, match="Invalid date format"):
        validate_orders(df)
