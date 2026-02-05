# FX Summary Service

andiron-cursor :white_check_mark:

![Tests](https://github.com/peter-iglaev/dan_brown_test/actions/workflows/test.yml/badge.svg)
![Code Quality](https://github.com/peter-iglaev/dan_brown_test/actions/workflows/quality.yml/badge.svg)
![Coverage](https://img.shields.io/badge/coverage-92%25-brightgreen)

A resilient Python + FastAPI service that provides EUR→USD exchange rate summaries with intelligent caching and automatic fallback mechanisms.

## Features

- **Real-time FX data**: Fetches current exchange rates from Frankfurter API
- **Resilience shield**: In-memory cache (60s TTL) + local file fallback
- **Daily breakdowns**: Optional per-day percentage change analysis
- **Pattern detection**: Automatic trend identification (up/down/flat)
- **Fast responses**: Cached queries return instantly

## Quick Start

Using Makefile (recommended):

```bash
# Install dependencies
make install

# Run tests
make test

# Run service
make run

# Build Docker image
make docker-build

# See all available commands
make help
```

Manual installation:

```bash
# Install dependencies
pip install -r requirements.txt
```

## Running the Service

### Method 1: Local Python

Start the server on port 8000:

```bash
# Using uvicorn directly
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Using Python module
python -m app.main
```

The service will be available at `http://localhost:8000`

### Method 2: Docker

```bash
# Build and run with Docker
docker build -t fx-service .
docker run -p 8000:8000 fx-service

# Or use docker-compose
docker-compose up
```

### Method 3: Docker Compose (Recommended for Development)

```bash
# Start the service
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the service
docker-compose down
```

## API Endpoints

### Health Check

```bash
curl http://localhost:8000/health
```

**Response:**
```json
{"status": "ok"}
```

### Summary Endpoint

Get FX rate summary for a date range:

```bash
# Basic request (totals only)
curl "http://localhost:8000/summary?start=2025-07-01&end=2025-07-03&breakdown=none"

# With daily breakdown
curl "http://localhost:8000/summary?start=2025-07-01&end=2025-07-03&breakdown=day"

# Custom currency pair
curl "http://localhost:8000/summary?start=2025-07-01&end=2025-07-03&from=EUR&to=USD&breakdown=day"
```

**Query Parameters:**
- `start` (required): Start date in YYYY-MM-DD format
- `end` (required): End date in YYYY-MM-DD format
- `breakdown` (optional): Either `none` or `day` (default: `none`)
- `from` (optional): Source currency code (default: `EUR`)
- `to` (optional): Target currency code (default: `USD`)

## madrond — Examples

### Display as Table

Use `jq` to format the response as a readable table:

```bash
curl -s "http://localhost:8000/summary?start=2025-07-01&end=2025-07-05&breakdown=day" | \
  jq -r '["Date", "Rate", "Change%"], ["----", "----", "-------"],
  (.daily[] | [.date, .rate, (.pct_change // "—")]) | @tsv' | column -t
```

**Output:**
```
Date        Rate  Change%
----        ----  -------
2025-07-01  1.07  —
2025-07-02  1.08  0.934579
2025-07-03  1.06  -1.85185
2025-07-04  1.065 0.471698
2025-07-05  1.075 0.938967
```

### ASCII Visualization

Create a simple trend visualization:

```bash
curl -s "http://localhost:8000/summary?start=2025-07-01&end=2025-07-05&breakdown=day" | \
  jq -r '.daily[] | "\(.date): " + ("█" * (.rate * 20 | floor))'
```

**Output:**
```
2025-07-01: █████████████████████
2025-07-02: █████████████████████
2025-07-03: █████████████████████
2025-07-04: █████████████████████
2025-07-05: █████████████████████
```

## Response Structure

### Successful Response

```json
{
  "meta": {
    "cache": "MISS",
    "source": "frankfurter",
    "base": "EUR",
    "quote": "USD",
    "start": "2025-07-01",
    "end": "2025-07-03",
    "breakdown": "day"
  },
  "totals": {
    "start_rate": 1.07,
    "end_rate": 1.06,
    "total_pct_change": -0.9345794392523364,
    "mean_rate": 1.07
  },
  "daily": [
    {
      "date": "2025-07-01",
      "rate": 1.07,
      "pct_change": null
    },
    {
      "date": "2025-07-02",
      "rate": 1.08,
      "pct_change": 0.9345794392523364
    },
    {
      "date": "2025-07-03",
      "rate": 1.06,
      "pct_change": -1.8518518518518516
    }
  ],
  "pattern": {
    "direction": "down",
    "min_rate": {
      "date": "2025-07-03",
      "rate": 1.06
    },
    "max_rate": {
      "date": "2025-07-02",
      "rate": 1.08
    }
  }
}
```

### Response Fields

**Meta Information:**
- `cache`: Either `HIT` (from cache) or `MISS` (fresh data)
- `source`: Either `frankfurter` (live API) or `local_file` (fallback)
- `base`, `quote`: Currency pair (EUR→USD)
- `start`, `end`: Date range from request
- `breakdown`: Breakdown type (`day` or `none`)

**Totals:**
- `start_rate`: Exchange rate on start date
- `end_rate`: Exchange rate on end date
- `total_pct_change`: Percentage change from start to end (null if start_rate = 0)
- `mean_rate`: Average rate across all dates

**Daily Breakdown** (only if `breakdown=day`):
- `date`: Date in YYYY-MM-DD format
- `rate`: Exchange rate for that day
- `pct_change`: Percentage change vs previous day (null for first day or if prev_rate = 0)

**Pattern:**
- `direction`: Overall trend (`up`, `down`, or `flat`)
- `min_rate`: Object with `date` and `rate` for lowest rate in the period
- `max_rate`: Object with `date` and `rate` for highest rate in the period

## Error Responses

| Status Code | Error Type | Description |
|-------------|------------|-------------|
| 400 | ValidationError | Invalid date format or start > end |
| 404 | NoDataFound | No rates available for the date range |
| 503 | ServiceUnavailable | Both API and fallback failed |

**Example Error:**
```json
{
  "detail": {
    "error": "ValidationError",
    "message": "Date must be in YYYY-MM-DD format, got: 2025-7-1"
  }
}
```

## Resilience Shield

The service implements a multi-layer resilience strategy:

### 1. In-Memory Cache (60-second TTL)

Identical requests within 60 seconds return instantly from cache. The `meta.cache` field indicates cache status:
- `MISS`: Fresh data fetched from API or fallback
- `HIT`: Returned from cache

**Cache Key Format:** `{from}_{to}_{start}_{end}`

### 2. Local File Fallback

When the Frankfurter API is unavailable, the service automatically falls back to `data/sample_fx.json`. The `meta.source` field indicates data origin:
- `frankfurter`: Live data from Frankfurter API
- `local_file`: Fallback data from local file

### Fallback Data Format

The `data/sample_fx.json` file contains sample exchange rates:

```json
{
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
```

The service automatically filters this data to match the requested date range.

## Division by Zero Handling

The service handles edge cases gracefully:
- If `start_rate = 0`: `total_pct_change` is `null`
- If `prev_rate = 0`: daily `pct_change` is `null`

No exceptions are raised for mathematical edge cases.

## Testing

Run the test suite:

```bash
# Run all tests
pytest tests/ -v

# Run with coverage report
pytest tests/ -v --cov=app

# Run specific test file
pytest tests/test_calculator.py -v
```

### Continuous Integration

The project uses GitHub Actions for automated testing on every commit:

**Tests Workflow** (`.github/workflows/test.yml`):
- Triggers on every push to any branch
- Triggers on all pull requests
- Runs tests on Python 3.11, 3.12, and 3.13
- Generates coverage reports
- Enforces minimum 85% code coverage
- Can be triggered manually from GitHub UI

**Code Quality Workflow** (`.github/workflows/quality.yml`):
- Runs linting with `ruff`
- Checks code formatting
- Performs static type checking with `mypy`

**Docker Build Workflow** (`.github/workflows/docker.yml`):
- Builds Docker image on main branch commits and tags
- Tests Docker image in pull requests
- Pushes to GitHub Container Registry
- Automatically tags images with version, branch, and commit SHA

All workflows run automatically on every commit, ensuring code quality and test coverage.

## Project Structure

```
dan_brown_test/
├── README.md
├── requirements.txt
├── .gitignore
├── data/
│   └── sample_fx.json       # Fallback exchange rate data
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app and endpoints
│   ├── models.py            # Pydantic data models
│   ├── config.py            # Configuration constants
│   ├── services/
│   │   ├── __init__.py
│   │   ├── cache.py         # In-memory cache (60s TTL)
│   │   ├── fx_client.py     # Frankfurter API client + fallback
│   │   └── calculator.py    # Business logic for summaries
│   └── utils/
│       ├── __init__.py
│       └── validators.py    # Date validation utilities
└── tests/
    ├── __init__.py
    ├── test_health.py       # Health endpoint tests
    ├── test_summary.py      # Integration tests
    ├── test_fx_client.py    # API client tests
    ├── test_calculator.py   # Business logic tests
    └── test_cache.py        # Cache mechanism tests
```

## Dependencies

- **fastapi**: Web framework for building APIs
- **uvicorn**: ASGI server for FastAPI
- **httpx**: Async HTTP client for API requests
- **pydantic**: Data validation and serialization
- **python-dateutil**: Date parsing and manipulation
- **pytest**: Testing framework

## License

This project is provided as-is for demonstration purposes.
