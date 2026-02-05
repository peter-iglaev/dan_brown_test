"""FastAPI application for FX Summary Service."""

from contextlib import asynccontextmanager
from typing import Annotated

import httpx
from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import JSONResponse

from app.config import CACHE_TTL_SECONDS, SERVER_PORT
from app.models import SummaryQueryParams, SummaryResponse, MetaInfo
from app.services.cache import InMemoryCache
from app.services.fx_client import FXClient, ServiceUnavailableError
from app.services.calculator import Calculator


# Global cache instance
cache = InMemoryCache(ttl_seconds=CACHE_TTL_SECONDS)

# Global HTTP client
http_client: httpx.AsyncClient = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan."""
    global http_client
    http_client = httpx.AsyncClient()
    yield
    await http_client.aclose()


app = FastAPI(
    title="FX Summary Service",
    description="EUR→USD exchange rate summary with caching and fallback",
    version="1.0.0",
    lifespan=lifespan
)


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok"}


@app.get("/summary", response_model=SummaryResponse)
async def summary(
    start: Annotated[str, Query(description="Start date (YYYY-MM-DD)")],
    end: Annotated[str, Query(description="End date (YYYY-MM-DD)")],
    breakdown: Annotated[str, Query(description="Breakdown type")] = "none",
    from_currency: Annotated[str, Query(alias="from", description="Source currency")] = "EUR",
    to: Annotated[str, Query(description="Target currency")] = "USD"
):
    """
    Get FX rate summary for date range.

    Args:
        start: Start date in YYYY-MM-DD format
        end: End date in YYYY-MM-DD format
        breakdown: Either "none" or "day"
        from_currency: Source currency code (default: EUR)
        to: Target currency code (default: USD)

    Returns:
        Summary response with totals, daily breakdown (if requested), and pattern

    Raises:
        HTTPException: 400 for invalid parameters, 404 for no data, 503 for service unavailable
    """
    # Validate query parameters
    try:
        params = SummaryQueryParams(
            start=start,
            end=end,
            breakdown=breakdown,
            **{"from": from_currency},
            to=to
        )
        params.validate_date_range()
    except ValueError as e:
        raise HTTPException(status_code=400, detail={
            "error": "ValidationError",
            "message": str(e)
        })

    # Check cache
    cache_key = InMemoryCache.make_key(from_currency, to, start, end)
    cached = cache.get(cache_key)

    if cached is not None:
        # Return cached response with HIT status
        result = cached.copy()
        result["meta"]["cache"] = "HIT"
        # Adjust daily based on breakdown parameter
        if breakdown == "none":
            result["daily"] = []
        return result

    # Fetch rates
    fx_client = FXClient(http_client)
    try:
        rates, source = await fx_client.fetch_rates(start, end, from_currency, to)
    except ServiceUnavailableError:
        raise HTTPException(status_code=503, detail={
            "error": "ServiceUnavailable",
            "message": "Both API and local fallback failed"
        })

    # Check if we have data
    if not rates:
        raise HTTPException(status_code=404, detail={
            "error": "NoDataFound",
            "message": f"No exchange rates found for {from_currency}→{to} between {start} and {end}"
        })

    # Compute summary
    totals, daily, pattern = Calculator.compute_summary(rates, breakdown)

    # Build response
    meta = MetaInfo(
        cache="MISS",
        source=source,
        base=from_currency,
        quote=to,
        start=start,
        end=end,
        breakdown=breakdown
    )

    response = SummaryResponse(
        meta=meta,
        totals=totals,
        daily=daily,
        pattern=pattern
    )

    # Cache the response (always with full daily breakdown for reuse)
    cache_data = response.model_dump()
    cache.set(cache_key, cache_data)

    # Adjust daily based on breakdown parameter for this response
    if breakdown == "none":
        response.daily = []

    return response


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=SERVER_PORT)
