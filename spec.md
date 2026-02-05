Below is a fully worked, implementation-ready spec (English) for the assignment you decoded. I’m writing it like something you can hand to an engineer (or to a coding agent) and expect consistent behavior.

⸻

FX Summary Service — Specification (EUR → USD)

1) Goal

Build an HTTP service that:
	•	Accepts a start date and end date.
	•	Fetches EUR→USD exchange rates from Frankfurter public FX API (no key).
	•	If the network request fails, falls back to a local JSON file (data/sample_fx.json).
	•	Returns either:
	•	Daily breakdown (per day rates + pct change), or
	•	No breakdown (totals only).
	•	Provides two endpoints: /health and /summary.
	•	Runs on port 8000.

A key requirement: “Coins alone do not tell the story; show me the pattern and the change.”
So the output must include both the rates and the change over time (daily pct_change + total pct change + mean rate).

⸻

2) Runtime & Server
	•	The service MUST listen on: 0.0.0.0:8000
	•	Any framework is acceptable (FastAPI / Flask / Express / etc.), but behavior must match this spec.
	•	Responses MUST be JSON (except optional HTML in README examples; service itself is JSON).

⸻

3) External Data Source (Primary)

Frankfurter endpoints

Primary fetch (range):
	•	GET https://api.frankfurter.dev/{start}..{end}?from=EUR&to=USD

Latest (optional, not required for summary but allowed):
	•	GET https://api.frankfurter.dev/latest?from=EUR&to=USD

Important: The range endpoint is the core requirement.

Expected response (Frankfurter-style)

Typically looks like:

{
  "amount": 1.0,
  "base": "EUR",
  "start_date": "2025-07-01",
  "end_date": "2025-07-03",
  "rates": {
    "2025-07-01": { "USD": 1.07 },
    "2025-07-02": { "USD": 1.08 },
    "2025-07-03": { "USD": 1.06 }
  }
}


⸻

4) Fallback Data Source (Secondary)

If any network failure occurs (DNS error, timeout, non-2xx response, parsing error), the service MUST attempt to load:
	•	data/sample_fx.json

Required local file format

The file MUST contain enough to compute the same output structure. Recommended canonical format:

{
  "base": "EUR",
  "to": "USD",
  "rates": {
    "2025-07-01": 1.07,
    "2025-07-02": 1.08,
    "2025-07-03": 1.06
  }
}

Notes:
	•	Local file may include a superset of dates; the service must filter to requested range.
	•	If local file is missing or invalid AND network failed, return a 503 with a clear error.

⸻

5) API Endpoints

5.1 GET /health

Purpose

Minimal health probe.

Response
	•	Status: 200 OK
	•	Body:

{
  "status": "ok"
}

No external calls are required for /health.

⸻

5.2 GET /summary

Query Parameters

Name	Type	Required	Example	Notes
start	string (YYYY-MM-DD)	yes	2025-07-01	Inclusive
end	string (YYYY-MM-DD)	yes	2025-07-03	Inclusive
breakdown	enum: day | none	no	day	Default: none
from	string	no	EUR	Default MUST be EUR; may allow only EUR for this test
to	string	no	USD	Default MUST be USD; may allow only USD for this test

Core assignment is EUR→USD. You may accept from/to params but must default to EUR/USD and still work correctly.

Validation Rules
	•	start and end must be valid dates in ISO format YYYY-MM-DD.
	•	start <= end else return 400.
	•	breakdown must be either day or none else 400.
	•	If the date range returns no data (empty intersection), return 404 or 200 with empty daily + null totals (pick one and document; recommended: 404 with message).

⸻

6) Output Data Contract

6.1 Common response structure (always returned)

{
  "meta": {
    "base": "EUR",
    "quote": "USD",
    "start": "2025-07-01",
    "end": "2025-07-03",
    "breakdown": "day",
    "source": "frankfurter" 
  },
  "totals": {
    "start_rate": 1.07,
    "end_rate": 1.06,
    "total_pct_change": -0.9346,
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
      "pct_change": 0.9346
    }
  ],
  "pattern": {
    "direction": "down",
    "min_rate": { "date": "2025-07-03", "rate": 1.06 },
    "max_rate": { "date": "2025-07-02", "rate": 1.08 }
  }
}

Field requirements
meta
	•	base: string, always "EUR" (or from query if supported)
	•	quote: string, always "USD" (or from query if supported)
	•	start, end: ISO dates
	•	breakdown: "day" or "none"
	•	source: "frankfurter" or "local_file"

totals
	•	start_rate: numeric (float), first available rate in the requested range (chronologically earliest date returned)
	•	end_rate: numeric, last available rate in range (chronologically latest date returned)
	•	total_pct_change: numeric, computed as:
	•	((end_rate - start_rate) / start_rate) * 100
	•	Rounded to a sensible precision (e.g., 4 decimals)
	•	mean_rate: arithmetic mean of daily rates in the range:
	•	sum(rates) / count(rates)

daily
	•	Included only if breakdown=day. If breakdown=none, it MUST be an empty array [] (or omit; recommended: include as [] for consistency).
	•	For each day:
	•	date: ISO date
	•	rate: numeric
	•	pct_change: numeric percent change vs previous day:
	•	For day i>0: ((rate_i - rate_{i-1}) / rate_{i-1}) * 100
	•	For the first day: null

pattern
	•	A minimal “story” field that highlights the pattern.
	•	Must include at least:
	•	direction: "up" | "down" | "flat" (based on start_rate vs end_rate with a tiny epsilon)
	•	min_rate: date+rate
	•	max_rate: date+rate

This satisfies the “pattern and change” requirement even if the UI is simple.

⸻

7) Division-by-Zero & “Be Kind”

When computing percent changes, if the denominator is 0:
	•	If previous rate is 0:
	•	If current rate is also 0: pct_change = 0
	•	If current rate is non-zero: pct_change = null and include a warning in meta.warnings (recommended)
	•	Same logic for total_pct_change if start_rate is 0.

Recommended addition:

"meta": {
  ...
  "warnings": ["pct_change undefined because previous rate is 0 on 2025-07-02"]
}


⸻

8) Ordering & Missing Days
	•	Daily entries MUST be sorted ascending by date.
	•	Frankfurter may not return weekends/holidays depending on source behavior; you must compute based on returned dates.
	•	Do not invent missing days unless explicitly required (it is not).

⸻

9) “Simple window” presentation requirement

Service output must be JSON, but your README should show users how to view it in a “simple window”:

Choose at least one:
	•	A text table example in README.
	•	A tiny ASCII sparkline example in README.
	•	A command example using jq to print a neat table.

(Implementation itself remains JSON.)

⸻

10) Resilience “Shield” (GREENNGIVE signature)

Implement at least one of these (more is better):

Option A: Retry
	•	Retry the Frankfurter call up to 2 times (e.g., total 3 attempts) on network/timeouts/5xx
	•	Use a short backoff (e.g., 200ms → 400ms)

Option B: Rate limit
	•	Very basic in-memory: max N requests per minute per IP (optional)

Option C: Cache (recommended)
	•	In-memory cache keyed by (start, end, from, to) for e.g. 60 seconds
	•	Avoid hammering external API during tests

Minimum requirement: implement caching OR retry.

In response, include:
	•	meta.cache: "HIT" / "MISS" (optional but nice)

⸻

11) Error Handling

400 Bad Request
	•	Invalid date format
	•	start > end
	•	invalid breakdown

Body:

{ "error": "BadRequest", "message": "start must be <= end" }

502 Bad Gateway
	•	Frankfurter returns non-2xx but network still reachable
	•	(You may still fallback to local file; if fallback works, return 200 with source=local_file.)

503 Service Unavailable
	•	Network failed AND local fallback missing/invalid/unusable

Body:

{ "error": "Unavailable", "message": "Failed to fetch rates and local fallback not available." }

404 Not Found
	•	No rates found in requested range (after filtering)

⸻

12) Examples

Example 1: totals only

Request:
GET /summary?start=2025-07-01&end=2025-07-03&breakdown=none

Response:
	•	daily: []
	•	totals present
	•	pattern present

Example 2: daily breakdown

Request:
GET /summary?start=2025-07-01&end=2025-07-03&breakdown=day

Response:
	•	daily array with pct_change vs prior day
	•	totals present

⸻

13) README Requirements

Your repository README MUST include:
	1.	The literal marker line:

	•	andiron-cursor :white_check_mark:

	2.	How to run:

	•	install dependencies
	•	run on port 8000

	3.	Example calls:

	•	curl commands for /health and /summary
	•	at least one “simple window” display example (table or sparkline)

	4.	Mention fallback:

	•	explain data/sample_fx.json usage and expected format

	5.	Mention resilience shield:

	•	caching or retry description

(There was also a weird word “madrond” in the decoded text; treat it as a label and include it as a small section header or note in README, e.g., “## madrond — Examples”.)

⸻

14) Non-functional Requirements
	•	Fast response (<1s typical) when cached; otherwise depends on external API.
	•	Deterministic JSON keys (consistent ordering optional, but structure must be stable).
	•	Minimal dependencies are preferred.

⸻

15) Acceptance Checklist
	•	Service runs on :8000
	•	GET /health returns {status:"ok"}
	•	GET /summary supports start, end, breakdown
	•	Uses Frankfurter range API
	•	On network failure, reads data/sample_fx.json
	•	Computes daily pct_change and totals (start_rate, end_rate, total_pct_change, mean_rate)
	•	Guards division by zero (no crashes, “kind” behavior)
	•	Includes a “pattern” summary (direction + min/max)
	•	Has at least one resilience shield (cache or retry)
	•	README includes andiron-cursor :white_check_mark: and runnable examples

⸻

If you want, I can also produce:
	•	OpenAPI 3.1 YAML for this contract (very useful for tests),
	•	a test plan (unit + integration cases),
	•	or a ready-to-copy README skeleton that matches these requirements.