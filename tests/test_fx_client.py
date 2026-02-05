"""Tests for FX client with API and fallback."""

import json
import pytest
import httpx
from unittest.mock import AsyncMock, patch, mock_open, MagicMock

from app.services.fx_client import FXClient, ServiceUnavailableError


@pytest.mark.asyncio
async def test_fetch_from_api_success():
    """Test successful API fetch."""
    mock_response = {
        "amount": 1.0,
        "base": "EUR",
        "start_date": "2025-07-01",
        "end_date": "2025-07-03",
        "rates": {
            "2025-07-01": {"USD": 1.07},
            "2025-07-02": {"USD": 1.08},
            "2025-07-03": {"USD": 1.06}
        }
    }

    mock_http_response = MagicMock()
    mock_http_response.json.return_value = mock_response
    mock_http_response.raise_for_status = MagicMock()

    mock_http_client = AsyncMock(spec=httpx.AsyncClient)
    mock_http_client.get = AsyncMock(return_value=mock_http_response)

    client = FXClient(mock_http_client)
    rates, source = await client.fetch_rates("2025-07-01", "2025-07-03", "EUR", "USD")

    assert source == "frankfurter"
    assert rates == {
        "2025-07-01": 1.07,
        "2025-07-02": 1.08,
        "2025-07-03": 1.06
    }


@pytest.mark.asyncio
async def test_fetch_fallback_on_api_error():
    """Test fallback to local file when API fails."""
    mock_http_client = AsyncMock(spec=httpx.AsyncClient)
    mock_http_client.get.side_effect = httpx.RequestError("Network error")

    local_data = {
        "base": "EUR",
        "to": "USD",
        "rates": {
            "2025-07-01": 1.07,
            "2025-07-02": 1.08,
            "2025-07-03": 1.06,
            "2025-07-04": 1.065,
            "2025-07-05": 1.075
        }
    }

    with patch("builtins.open", mock_open(read_data=json.dumps(local_data))):
        client = FXClient(mock_http_client)
        rates, source = await client.fetch_rates("2025-07-01", "2025-07-03", "EUR", "USD")

    assert source == "local_file"
    assert rates == {
        "2025-07-01": 1.07,
        "2025-07-02": 1.08,
        "2025-07-03": 1.06
    }


@pytest.mark.asyncio
async def test_local_file_date_filtering():
    """Test local file filters by date range."""
    mock_http_client = AsyncMock(spec=httpx.AsyncClient)
    mock_http_client.get.side_effect = httpx.RequestError("Network error")

    local_data = {
        "base": "EUR",
        "to": "USD",
        "rates": {
            "2025-07-01": 1.07,
            "2025-07-02": 1.08,
            "2025-07-03": 1.06,
            "2025-07-04": 1.065,
            "2025-07-05": 1.075
        }
    }

    with patch("builtins.open", mock_open(read_data=json.dumps(local_data))):
        client = FXClient(mock_http_client)
        rates, source = await client.fetch_rates("2025-07-02", "2025-07-04", "EUR", "USD")

    assert rates == {
        "2025-07-02": 1.08,
        "2025-07-03": 1.06,
        "2025-07-04": 1.065
    }


@pytest.mark.asyncio
async def test_service_unavailable_error():
    """Test error when both API and fallback fail."""
    mock_http_client = AsyncMock(spec=httpx.AsyncClient)
    mock_http_client.get.side_effect = httpx.RequestError("Network error")

    with patch("builtins.open", side_effect=FileNotFoundError()):
        client = FXClient(mock_http_client)

        with pytest.raises(ServiceUnavailableError):
            await client.fetch_rates("2025-07-01", "2025-07-03", "EUR", "USD")


@pytest.mark.asyncio
async def test_local_file_currency_mismatch():
    """Test error when local file has wrong currency pair."""
    mock_http_client = AsyncMock(spec=httpx.AsyncClient)
    mock_http_client.get.side_effect = httpx.RequestError("Network error")

    local_data = {
        "base": "EUR",
        "to": "USD",
        "rates": {"2025-07-01": 1.07}
    }

    with patch("builtins.open", mock_open(read_data=json.dumps(local_data))):
        client = FXClient(mock_http_client)

        with pytest.raises(ServiceUnavailableError):
            await client.fetch_rates("2025-07-01", "2025-07-03", "GBP", "USD")
