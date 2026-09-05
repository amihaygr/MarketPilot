# Historical Market Backfill Runbook

## Purpose

Load real, closed-session Alpaca bars through Kafka and the complete Medallion
certification path, then create a reproducible backtest run.

## Preconditions

1. Put real `ALPACA_API_KEY` and `ALPACA_API_SECRET` values only in the ignored `.env`.
2. Keep `ALPACA_DATA_FEED=iex` unless the account has SIP entitlement.
3. Start the platform and confirm Kafka, MinIO, raw archive, Spark, MariaDB, Airflow,
   Backend API, and Web App are healthy.
4. Confirm the requested symbols are included in `MARKET_SYMBOLS`.

Never paste credentials into Airflow parameters, logs, screenshots, or Git.

## Run

1. Open Airflow at <http://localhost:8080>.
2. Select `historical_market_backfill` and choose **Trigger DAG w/ config**.
3. Start with `AAPL`, `MSFT`, and `SPY` over two to ten closed trading sessions.
4. Keep `minimum_coverage_pct=80` for IEX. This is a minimum observed-bar gate, not
   permission to fabricate missing minutes.
5. Keep the default SMA, cost, and slippage values for the first run.
6. Trigger once and follow tasks in order: acquisition, Bronze-to-Silver, quality,
   Gold Certified, then backtest.

## Evidence to inspect

- Kafka UI: `market.bars.1m.backfill.v1` contains canonical events.
- MinIO Bronze: exact Alpaca page objects, per-offset market bars, and the completion manifest.
- Airflow: every mapped session is green; no Gold task ran before its quality gate.
- MariaDB: requested dates are `CERTIFIED`; the newest backtest run is `SUCCEEDED`.
- Backtesting Lab: select the newest run and confirm non-flat market-dependent results.

## Failure handling

- Authentication errors: correct `.env`, recreate Airflow services, and retry the same run.
- Rate limits or transient 5xx: retries use bounded exponential backoff.
- Bronze barrier timeout: inspect `raw-archive-sink` health and logs; do not bypass the barrier.
- Coverage failure: verify the feed and symbol. Lowering the gate requires a reviewed data-quality decision.
- Retry after a completed acquisition: the immutable completion manifest prevents duplicate publication.
