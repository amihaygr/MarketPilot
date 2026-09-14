# Phase 14 verification — Decision Intelligence

Verification date: 2026-09-14

## Release state

The software delivery is complete and running locally. The model remains deliberately locked in
`COLLECTING` Shadow Mode at **1 of 20** distinct certified market sessions. This is the expected
state: twenty real sessions must elapse before a human review may approve Decision Support.

## Verified behavior

- Docker Compose configuration validates and all core services report healthy.
- A certified bounded calculation published three watchlist snapshots.
- A provisional calculation published one AAPL snapshot and remained non-actionable.
- The Opportunity API returned four ranked symbols; two were in a mathematical `BUY ZONE`.
- The Shadow status API returned `completed_sessions=1`, `required_sessions=20` and
  `promotion_status=COLLECTING`.
- The official Alpaca Corporate Actions adapter archived one exact page and normalized nine
  actions idempotently.
- Airflow loaded `corporate_actions` and `daily_market_close` with no import errors.
- The outcome evaluator completed successfully and published zero rows because no requested
  2/5/10/20-session horizon had elapsed yet. It did not invent future results.
- Spark Structured Streaming restarted healthy with its durable checkpoint and both Gold/DLQ
  queries active.
- The Opportunity Center was visually inspected at desktop and mobile widths. Ranked selection,
  AAPL/MSFT detail changes, position sizing, bilingual explanations, chart legend, journal and
  Shadow Mode progress rendered correctly.
- Historical evidence was expanded to 41 certified XNYS sessions for AAPL, MSFT and SPY. The
  combined 2026-07-06 through 2026-08-28 backtest published 46,749 observations and 1,059
  position changes under run `2bf99281-ec93-5fec-9ce2-d72539021bea`.
- Historical evidence remains separate from the live gate; Shadow Mode is still 1 of 20.
- The orphaned scheduled run from 2026-08-25 was preserved and closed as `failed`; the
  `daily_market_close` DAG was unpaused for the next real XNYS close.
- A terminal `verify_shadow_mode_progress` task now fails the daily run unless its certified
  recommendation date, Shadow latest date and capped session counter agree.

## Quality gates

```text
ruff format --check .  -> passed (175 files)
ruff check .           -> passed
pytest -q              -> 99 passed, 7 integration suites opt-in skipped
docker compose config  -> passed
Airflow DAG imports    -> no errors
```

The skipped suites require their documented environment flags and live boundary setup; the same
runtime boundaries were exercised directly during this verification.

## Honest limitations

- Alpaca IEX is a partial market feed and therefore lowers confidence.
- Shadow Mode cannot finish before 20 real certified sessions exist.
- Cash dividends are retained as Corporate Actions but are not credited in the current
  price-signal backtest; split adjustment is active.
- No recommendation guarantees return, reads a brokerage balance or places an order.
