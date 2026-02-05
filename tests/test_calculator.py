"""Tests for calculator business logic."""

import pytest
from app.services.calculator import Calculator


def test_compute_totals():
    """Test totals calculation."""
    rates = {
        "2025-07-01": 1.07,
        "2025-07-02": 1.08,
        "2025-07-03": 1.06
    }
    sorted_dates = sorted(rates.keys())

    totals = Calculator._compute_totals(rates, sorted_dates)

    assert totals.start_rate == 1.07
    assert totals.end_rate == 1.06
    assert totals.total_pct_change is not None
    assert abs(totals.total_pct_change - ((1.06 - 1.07) / 1.07 * 100)) < 0.01
    assert totals.mean_rate == sum(rates.values()) / len(rates)


def test_compute_totals_division_by_zero():
    """Test totals when start_rate is zero."""
    rates = {
        "2025-07-01": 0.0,
        "2025-07-02": 1.08
    }
    sorted_dates = sorted(rates.keys())

    totals = Calculator._compute_totals(rates, sorted_dates)

    assert totals.start_rate == 0.0
    assert totals.end_rate == 1.08
    assert totals.total_pct_change is None


def test_compute_daily():
    """Test daily breakdown with pct_change."""
    rates = {
        "2025-07-01": 1.07,
        "2025-07-02": 1.08,
        "2025-07-03": 1.06
    }
    sorted_dates = sorted(rates.keys())

    daily = Calculator._compute_daily(rates, sorted_dates)

    assert len(daily) == 3

    # First day should have None pct_change
    assert daily[0].date == "2025-07-01"
    assert daily[0].rate == 1.07
    assert daily[0].pct_change is None

    # Second day
    assert daily[1].date == "2025-07-02"
    assert daily[1].rate == 1.08
    expected_pct = ((1.08 - 1.07) / 1.07) * 100
    assert abs(daily[1].pct_change - expected_pct) < 0.01

    # Third day
    assert daily[2].date == "2025-07-03"
    assert daily[2].rate == 1.06
    expected_pct = ((1.06 - 1.08) / 1.08) * 100
    assert abs(daily[2].pct_change - expected_pct) < 0.01


def test_compute_daily_division_by_zero():
    """Test daily breakdown when previous rate is zero."""
    rates = {
        "2025-07-01": 0.0,
        "2025-07-02": 1.08,
        "2025-07-03": 1.06
    }
    sorted_dates = sorted(rates.keys())

    daily = Calculator._compute_daily(rates, sorted_dates)

    assert daily[0].pct_change is None  # First day
    assert daily[1].pct_change is None  # Previous rate was 0
    assert daily[2].pct_change is not None  # Previous rate was 1.08


def test_compute_pattern_up():
    """Test pattern detection for upward trend."""
    rates = {
        "2025-07-01": 1.07,
        "2025-07-02": 1.08,
        "2025-07-03": 1.09
    }
    sorted_dates = sorted(rates.keys())

    pattern = Calculator._compute_pattern(rates, sorted_dates)

    assert pattern.direction == "up"
    assert pattern.min_rate.rate == 1.07
    assert pattern.min_rate.date == "2025-07-01"
    assert pattern.max_rate.rate == 1.09
    assert pattern.max_rate.date == "2025-07-03"


def test_compute_pattern_down():
    """Test pattern detection for downward trend."""
    rates = {
        "2025-07-01": 1.09,
        "2025-07-02": 1.08,
        "2025-07-03": 1.07
    }
    sorted_dates = sorted(rates.keys())

    pattern = Calculator._compute_pattern(rates, sorted_dates)

    assert pattern.direction == "down"
    assert pattern.min_rate.rate == 1.07
    assert pattern.min_rate.date == "2025-07-03"
    assert pattern.max_rate.rate == 1.09
    assert pattern.max_rate.date == "2025-07-01"


def test_compute_pattern_flat():
    """Test pattern detection for flat trend."""
    rates = {
        "2025-07-01": 1.08,
        "2025-07-02": 1.09,
        "2025-07-03": 1.08
    }
    sorted_dates = sorted(rates.keys())

    pattern = Calculator._compute_pattern(rates, sorted_dates)

    assert pattern.direction == "flat"
    assert pattern.min_rate.rate == 1.08
    assert pattern.max_rate.rate == 1.09
    assert pattern.max_rate.date == "2025-07-02"


def test_compute_summary_with_breakdown():
    """Test complete summary computation with daily breakdown."""
    rates = {
        "2025-07-01": 1.07,
        "2025-07-02": 1.08,
        "2025-07-03": 1.06
    }

    totals, daily, pattern = Calculator.compute_summary(rates, "day")

    assert totals.start_rate == 1.07
    assert len(daily) == 3
    assert pattern.direction == "down"


def test_compute_summary_without_breakdown():
    """Test complete summary computation without daily breakdown."""
    rates = {
        "2025-07-01": 1.07,
        "2025-07-02": 1.08,
        "2025-07-03": 1.06
    }

    totals, daily, pattern = Calculator.compute_summary(rates, "none")

    assert totals.start_rate == 1.07
    assert len(daily) == 0
    assert pattern.direction == "down"
