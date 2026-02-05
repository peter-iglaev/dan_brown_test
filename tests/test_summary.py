"""Integration tests for summary endpoint."""

import json
import pytest
from unittest.mock import AsyncMock, patch, mock_open, MagicMock
from httpx import AsyncClient, ASGITransport

from app.main import app, cache


@pytest.fixture(autouse=True)
def clear_cache():
    """Clear cache before each test."""
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def mock_api_error():
    """Mock httpx client to force fallback to local file."""
    async def mock_get(*args, **kwargs):
        raise Exception("Force fallback")

    with patch("app.main.http_client") as mock_client:
        mock_client.get = mock_get
        yield mock_client


@pytest.mark.asyncio
async def test_summary_breakdown_none(mock_api_error):
    """Test summary with breakdown=none returns empty daily array."""
    local_data = {
        "base": "EUR",
        "to": "USD",
        "rates": {
            "2025-07-01": 1.07,
            "2025-07-02": 1.08,
            "2025-07-03": 1.06
        }
    }

    with patch("builtins.open", mock_open(read_data=json.dumps(local_data))):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/summary?start=2025-07-01&end=2025-07-03&breakdown=none"
            )

    assert response.status_code == 200
    data = response.json()
    assert data["daily"] == []
    assert data["meta"]["cache"] == "MISS"
    assert len(data["totals"]) > 0


@pytest.mark.asyncio
async def test_summary_breakdown_day(mock_api_error):
    """Test summary with breakdown=day returns populated daily array."""
    local_data = {
        "base": "EUR",
        "to": "USD",
        "rates": {
            "2025-07-01": 1.07,
            "2025-07-02": 1.08,
            "2025-07-03": 1.06
        }
    }

    with patch("builtins.open", mock_open(read_data=json.dumps(local_data))):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/summary?start=2025-07-01&end=2025-07-03&breakdown=day"
            )

    assert response.status_code == 200
    data = response.json()
    assert len(data["daily"]) == 3
    assert data["daily"][0]["date"] == "2025-07-01"
    assert data["daily"][0]["pct_change"] is None  # First day
    assert data["daily"][1]["pct_change"] is not None


@pytest.mark.asyncio
async def test_summary_cache_hit(mock_api_error):
    """Test cache HIT on second identical request."""
    local_data = {
        "base": "EUR",
        "to": "USD",
        "rates": {
            "2025-07-01": 1.07,
            "2025-07-02": 1.08
        }
    }

    with patch("builtins.open", mock_open(read_data=json.dumps(local_data))):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # First request - MISS
            response1 = await client.get(
                "/summary?start=2025-07-01&end=2025-07-02&breakdown=day"
            )
            data1 = response1.json()
            assert data1["meta"]["cache"] == "MISS"

            # Second request - HIT
            response2 = await client.get(
                "/summary?start=2025-07-01&end=2025-07-02&breakdown=day"
            )
            data2 = response2.json()
            assert data2["meta"]["cache"] == "HIT"


@pytest.mark.asyncio
async def test_summary_invalid_date_format():
    """Test 400 error for invalid date format."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/summary?start=invalid-date&end=2025-07-03&breakdown=none"
        )

    assert response.status_code == 400
    data = response.json()
    assert "detail" in data


@pytest.mark.asyncio
async def test_summary_start_after_end():
    """Test 400 error when start date is after end date."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/summary?start=2025-07-03&end=2025-07-01&breakdown=none"
        )

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_summary_no_data_found(mock_api_error):
    """Test 404 when no rates are found in range."""
    local_data = {
        "base": "EUR",
        "to": "USD",
        "rates": {
            "2025-06-01": 1.07,
            "2025-06-02": 1.08
        }
    }

    with patch("builtins.open", mock_open(read_data=json.dumps(local_data))):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/summary?start=2025-07-01&end=2025-07-03&breakdown=none"
            )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_summary_with_pattern(mock_api_error):
    """Test that pattern is included in response."""
    local_data = {
        "base": "EUR",
        "to": "USD",
        "rates": {
            "2025-07-01": 1.07,
            "2025-07-02": 1.08,
            "2025-07-03": 1.09
        }
    }

    with patch("builtins.open", mock_open(read_data=json.dumps(local_data))):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/summary?start=2025-07-01&end=2025-07-03&breakdown=day"
            )

    assert response.status_code == 200
    data = response.json()
    assert "pattern" in data
    assert data["pattern"]["direction"] == "up"
    assert data["pattern"]["min_rate"]["rate"] == 1.07
    assert data["pattern"]["max_rate"]["rate"] == 1.09
