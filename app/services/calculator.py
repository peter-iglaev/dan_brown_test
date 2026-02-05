"""Business logic for computing FX rate summaries."""

from typing import Optional, Literal

from app.models import Totals, DailyRate, Pattern, RatePoint


class Calculator:
    """Calculator for FX rate statistics and patterns."""

    @staticmethod
    def compute_summary(
        rates: dict[str, float],
        breakdown: Literal["none", "day"]
    ) -> tuple[Totals, list[DailyRate], Pattern]:
        """
        Compute complete summary statistics.

        Args:
            rates: Dictionary mapping date strings to rates
            breakdown: Whether to include daily breakdown

        Returns:
            Tuple of (totals, daily, pattern)
        """
        sorted_dates = sorted(rates.keys())

        totals = Calculator._compute_totals(rates, sorted_dates)
        daily = Calculator._compute_daily(rates, sorted_dates) if breakdown == "day" else []
        pattern = Calculator._compute_pattern(rates, sorted_dates)

        return totals, daily, pattern

    @staticmethod
    def _compute_totals(rates: dict[str, float], sorted_dates: list[str]) -> Totals:
        """
        Compute total statistics.

        Args:
            rates: Rate dictionary
            sorted_dates: Sorted list of date strings

        Returns:
            Totals object with aggregate statistics
        """
        start_rate = rates[sorted_dates[0]]
        end_rate = rates[sorted_dates[-1]]

        # Handle division by zero
        if start_rate == 0:
            total_pct_change = None
        else:
            total_pct_change = ((end_rate - start_rate) / start_rate) * 100

        mean_rate = sum(rates.values()) / len(rates)

        return Totals(
            start_rate=start_rate,
            end_rate=end_rate,
            total_pct_change=total_pct_change,
            mean_rate=mean_rate
        )

    @staticmethod
    def _compute_daily(rates: dict[str, float], sorted_dates: list[str]) -> list[DailyRate]:
        """
        Compute daily rate changes.

        Args:
            rates: Rate dictionary
            sorted_dates: Sorted list of date strings

        Returns:
            List of DailyRate objects with pct_change vs previous day
        """
        daily = []

        for i, date in enumerate(sorted_dates):
            rate = rates[date]

            # First day has no previous rate
            if i == 0:
                pct_change = None
            else:
                prev_rate = rates[sorted_dates[i - 1]]
                # Handle division by zero
                if prev_rate == 0:
                    pct_change = None
                else:
                    pct_change = ((rate - prev_rate) / prev_rate) * 100

            daily.append(DailyRate(
                date=date,
                rate=rate,
                pct_change=pct_change
            ))

        return daily

    @staticmethod
    def _compute_pattern(rates: dict[str, float], sorted_dates: list[str]) -> Pattern:
        """
        Analyze rate pattern over the period.

        Args:
            rates: Rate dictionary
            sorted_dates: Sorted list of date strings

        Returns:
            Pattern object with direction and min/max
        """
        start_rate = rates[sorted_dates[0]]
        end_rate = rates[sorted_dates[-1]]

        # Determine direction
        if end_rate > start_rate:
            direction = "up"
        elif end_rate < start_rate:
            direction = "down"
        else:
            direction = "flat"

        # Find min and max with dates
        min_date = min(rates.keys(), key=lambda d: rates[d])
        max_date = max(rates.keys(), key=lambda d: rates[d])

        return Pattern(
            direction=direction,
            min_rate=RatePoint(date=min_date, rate=rates[min_date]),
            max_rate=RatePoint(date=max_date, rate=rates[max_date])
        )
