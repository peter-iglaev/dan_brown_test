"""Validation utilities for dates."""

from datetime import datetime


def validate_date_format(date_str: str) -> datetime:
    """
    Validate and parse date string in YYYY-MM-DD format.

    Args:
        date_str: Date string to validate

    Returns:
        Parsed datetime object

    Raises:
        ValueError: If date format is invalid
    """
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        raise ValueError(f"Date must be in YYYY-MM-DD format, got: {date_str}")


def validate_date_range(start: str, end: str) -> None:
    """
    Validate that start date is before or equal to end date.

    Args:
        start: Start date string
        end: End date string

    Raises:
        ValueError: If start > end
    """
    start_date = validate_date_format(start)
    end_date = validate_date_format(end)

    if start_date > end_date:
        raise ValueError("start date must be before or equal to end date")
