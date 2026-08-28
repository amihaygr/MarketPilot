# Phase 9 Verification

Verified locally on 2026-08-28 against the running Docker Compose platform.

## Delivered analytics

- `SMA_20`: rolling 20-bar simple moving average.
- `RSI_14`: rolling 14-change relative strength index, bounded to 0–100.
- `REALIZED_VOLATILITY_20`: annualized 20-return log volatility in percent.
- `VOLUME_RATIO_20`: current volume divided by the prior 20-bar mean.
- Explained observations for price/SMA crossings, RSI threshold crossings, and
  two-times-volume crossings.

These observations are research context, not financial advice or order-execution
instructions. Phase 9 publishes bounded snapshots. Near-real-time stateful
Indicator calculation inside Structured Streaming remains a future enhancement.

## Runtime evidence

Spark run `775e34b8-5aab-4d93-85a2-042d3803f688` published the live 2026-08-28
snapshot with 4,636 Indicator rows and 273 Signal rows at its source cutoff. All
Indicator and Signal business keys were distinct. RSI ranged from 0.2409 to 100;
Signal strength ranged from 0.000095 to 1 and was constrained by the database and
publisher to 0–1. Four persisted analytics DQ checks passed and the partition
watermark was `PUBLISHED`.

Static-partition runs `a01bcc84-8d34-49b9-9843-c23b28c8338b` and
`ca0e8cdd-0c00-4365-829d-41eb56695b4f` both produced exactly 10,868 Indicator
rows and zero threshold-crossing Signals for 2026-08-25. The second atomic
replacement preserved those counts and created no duplicate business keys.

## Serving and orchestration evidence

- The API returned 408 AAPL Indicators and 28 AAPL Signals for the tested current
  range; the Nginx `/api/` proxy returned the same Indicator total.
- The `marketpilot_app` identity read the new tables and received MariaDB error
  1142 for an `UPDATE` probe.
- Airflow imported without errors. `daily_market_close` now orders
  `silver_to_gold_certified` before `calculate_market_analytics` and remains
  `max_active_runs=1` and paused by default.
- The API and Web App rebuilt cleanly and reported healthy.

## Quality and recovery behavior

Publication validates non-empty Indicators, unique keys, RSI bounds, and Signal
strength bounds before opening its transaction. It replaces only one UTC logical
date, publishes Indicators, Signals, DQ evidence, and the watermark in a single
transaction, and rolls back on any error. Source market bars are read-only.

The automatic in-app visual inspection could not connect because the local browser
connector rejected its Trusted Path before page access. HTTP, proxy, JavaScript
syntax, DOM identifiers, API contracts, and container health were verified; a
manual refresh of `http://localhost:3000` is the remaining visual confirmation.
