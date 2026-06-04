import pandas as pd
from datetime import datetime


def validate_orders(df: pd.DataFrame) -> bool:
    """Validate orders DataFrame for data quality issues.

    Args:
        df: pandas DataFrame with columns: order_id, amount, created_at

    Returns:
        True if all validations pass

    Raises:
        ValueError: if any validation fails
        KeyError: if required columns are missing
    """
    required_columns = {'order_id', 'amount', 'created_at'}
    missing_cols = required_columns - set(df.columns)
    if missing_cols:
        raise KeyError(f"Missing required columns: {missing_cols}")

    # Check for null order_ids
    null_order_ids = df['order_id'].isna().sum()
    if null_order_ids > 0:
        raise ValueError(
            f"Found {null_order_ids} null order_id(s)"
        )

    # Check that amount is positive
    non_positive = (df['amount'] <= 0).sum()
    if non_positive > 0:
        raise ValueError(
            f"Found {non_positive} row(s) with non-positive amount"
        )

    # Check that created_at is a valid date
    try:
        pd.to_datetime(df['created_at'])
    except (ValueError, TypeError) as e:
        raise ValueError(
            f"Invalid date format in created_at: {str(e)}"
        )

    return True
