I have two dates: a start and an end.
If you request day, return day-by-day.
Provide two endpoints: /health and /summary.

Use the Frankfurter public FX API (no key). Try:
	•	https://api.frankfurter.dev/2025-07-01..2025-07-03?from=EUR&to=USD
	•	https://api.frankfurter.dev/latest?from=EUR&to=USD

If the network fails, fall back to a local file: data/sample_fx.json.
For each day, return: date, rate (EUR->USD), and pct_change from the prior day.
In totals, return: start_rate, end_rate, total_pct_change, mean_rate.

Guard division by zero; when denominator is 0, be kind.
Breakdown is day or none.
Run on port 8000.

Coins alone do not tell the story; show me the pattern and the change.
Plan your numbers in a simple window — text, table, or chart, as you please.

For GREENNGIVE: a small shield of protection (retry, rate, or cache) is a good signature.
Add examples in your README (madrond).
Build the thing, share the repo.
Leave a pineapple by the door.

Mark the README with andiron-cursor :white_check_mark:.