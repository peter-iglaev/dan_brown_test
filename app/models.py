"""Pydantic models for the FX Summary Service."""

from typing import Optional, Literal
from pydantic import BaseModel, Field, field_validator
from datetime import datetime


class SummaryQueryParams(BaseModel):
    """Query parameters for the summary endpoint."""
    start: str = Field(..., description="Start date in YYYY-MM-DD format")
    end: str = Field(..., description="End date in YYYY-MM-DD format")
    breakdown: Literal["none", "day"] = Field(default="none", description="Breakdown type")
    from_currency: str = Field(default="EUR", alias="from", description="Source currency")
    to: str = Field(default="USD", description="Target currency")

    @field_validator("start", "end")
    @classmethod
    def validate_date_format(cls, v: str) -> str:
        """Validate date format is YYYY-MM-DD."""
        try:
            datetime.strptime(v, "%Y-%m-%d")
            return v
        except ValueError:
            raise ValueError(f"Date must be in YYYY-MM-DD format, got: {v}")

    def validate_date_range(self):
        """Validate that start date is before or equal to end date."""
        start_date = datetime.strptime(self.start, "%Y-%m-%d")
        end_date = datetime.strptime(self.end, "%Y-%m-%d")
        if start_date > end_date:
            raise ValueError("start date must be before or equal to end date")


class MetaInfo(BaseModel):
    """Metadata about the response."""
    cache: Literal["HIT", "MISS"]
    source: Literal["frankfurter", "local_file"]
    base: str
    quote: str
    start: str
    end: str
    breakdown: Literal["day", "none"]

    class Config:
        populate_by_name = True


class Totals(BaseModel):
    """Total statistics for the date range."""
    start_rate: float
    end_rate: float
    total_pct_change: Optional[float]
    mean_rate: float


class DailyRate(BaseModel):
    """Daily rate information."""
    date: str
    rate: float
    pct_change: Optional[float]


class RatePoint(BaseModel):
    """A single rate point with date."""
    date: str
    rate: float


class Pattern(BaseModel):
    """Pattern analysis of rates."""
    direction: Literal["up", "down", "flat"]
    min_rate: RatePoint
    max_rate: RatePoint


class SummaryResponse(BaseModel):
    """Complete summary response."""
    meta: MetaInfo
    totals: Totals
    daily: list[DailyRate]
    pattern: Pattern


class FrankfurterResponse(BaseModel):
    """Response from Frankfurter API."""
    amount: float
    base: str
    start_date: str
    end_date: str
    rates: dict[str, dict[str, float]]


class LocalFallbackData(BaseModel):
    """Structure of local fallback JSON file."""
    base: str
    to: str
    rates: dict[str, float]
