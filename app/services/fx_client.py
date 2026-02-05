"""FX rate client with API and local fallback support."""

import json
import httpx
from pathlib import Path
from typing import Literal
from datetime import datetime

from app.config import FRANKFURTER_BASE_URL, LOCAL_FALLBACK_PATH, REQUEST_TIMEOUT
from app.models import FrankfurterResponse, LocalFallbackData


class ServiceUnavailableError(Exception):
    """Raised when both API and fallback fail."""
    pass


class FXClient:
    """Client for fetching FX rates from API with local file fallback."""

    def __init__(self, http_client: httpx.AsyncClient):
        """
        Initialize FX client.

        Args:
            http_client: Async HTTP client for API requests
        """
        self.http_client = http_client

    async def fetch_rates(
        self,
        start: str,
        end: str,
        from_currency: str = "EUR",
        to: str = "USD"
    ) -> tuple[dict[str, float], Literal["frankfurter", "local_file"]]:
        """
        Fetch exchange rates for date range.

        Tries Frankfurter API first, falls back to local file on failure.

        Args:
            start: Start date (YYYY-MM-DD)
            end: End date (YYYY-MM-DD)
            from_currency: Source currency code
            to: Target currency code

        Returns:
            Tuple of (rates_dict, source) where rates_dict maps date -> rate

        Raises:
            ServiceUnavailableError: If both API and fallback fail
        """
        # Try API first
        try:
            rates = await self._fetch_from_api(start, end, from_currency, to)
            return rates, "frankfurter"
        except Exception:
            # Fall back to local file
            try:
                rates = self._fetch_from_local(start, end, from_currency, to)
                return rates, "local_file"
            except Exception as e:
                raise ServiceUnavailableError(
                    "Both API and local fallback failed"
                ) from e

    async def _fetch_from_api(
        self,
        start: str,
        end: str,
        from_currency: str,
        to: str
    ) -> dict[str, float]:
        """
        Fetch rates from Frankfurter API.

        Args:
            start: Start date
            end: End date
            from_currency: Source currency
            to: Target currency

        Returns:
            Dictionary mapping date strings to rates
        """
        url = f"{FRANKFURTER_BASE_URL}/{start}..{end}"
        params = {"from": from_currency, "to": to}

        response = await self.http_client.get(
            url,
            params=params,
            timeout=REQUEST_TIMEOUT
        )
        response.raise_for_status()

        data = FrankfurterResponse(**response.json())

        # Transform nested rates to flat dict
        rates = {}
        for date_str, currencies in data.rates.items():
            if to in currencies:
                rates[date_str] = currencies[to]

        return rates

    def _fetch_from_local(
        self,
        start: str,
        end: str,
        from_currency: str,
        to: str
    ) -> dict[str, float]:
        """
        Fetch rates from local fallback file.

        Args:
            start: Start date
            end: End date
            from_currency: Source currency
            to: Target currency

        Returns:
            Dictionary mapping date strings to rates, filtered by date range
        """
        file_path = Path(LOCAL_FALLBACK_PATH)
        with open(file_path, "r") as f:
            data = LocalFallbackData(**json.load(f))

        # Validate currency match
        if data.base != from_currency or data.to != to:
            raise ValueError(
                f"Local file has {data.base}->{data.to}, "
                f"requested {from_currency}->{to}"
            )

        # Filter rates by date range
        start_date = datetime.strptime(start, "%Y-%m-%d")
        end_date = datetime.strptime(end, "%Y-%m-%d")

        filtered_rates = {}
        for date_str, rate in data.rates.items():
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            if start_date <= date_obj <= end_date:
                filtered_rates[date_str] = rate

        return filtered_rates
