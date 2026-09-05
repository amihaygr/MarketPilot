# Phase 12 Verification

- Verification date: 2026-09-05
- Airflow run: `phase12_verification_20260905`
- Scope: 2026-08-24 through 2026-08-28
- Symbols: AAPL, MSFT, SPY
- Feed: Alpaca IEX
- Minimum per-session coverage gate: 80 percent

## Result

The `historical_market_backfill` DAG completed successfully. All five mapped
acquisition tasks, five Bronze-to-Silver jobs, five blocking quality jobs, five
Silver-to-Gold Certified jobs, and the final historical backtest succeeded.

The first integration attempt exposed an Airflow 3 reserved-context collision on
the task argument name `logical_date`. The argument was renamed to `session_date`,
a regression assertion was added, and the same verification run was safely reset
before any source request or data publication from that failed attempt.

## Runtime evidence

- Kafka topic `market.bars.1m.backfill.v1` exists with three partitions.
- End offsets after verification were 1,950, 3,887, and 0: 5,837 historical events.
- MinIO Bronze contained five content-addressed Alpaca source-page objects.
- MinIO Bronze contained five successful session manifests.
- The broader August Alpaca market-bar prefix contained 8,445 immutable per-offset objects.
- The Backend API health endpoint returned `ready`.
- AAPL had 2,083 Certified Gold bars in the requested date range.
- The published backtest run ID is `5e8eed0b-c3af-5427-9601-db6afe99be54`.
- The run contained 6,232 strategy observations and 145 position changes across assets.

Published results:

| Symbol | Observations | Trades | Net return | Benchmark | Excess | Max drawdown |
|---|---:|---:|---:|---:|---:|---:|
| AAPL | 2,081 | 47 | 25.34% | 0.72% | 24.62% | -1.21% |
| MSFT | 2,070 | 59 | -15.94% | 0.72% | -16.66% | -17.99% |
| SPY | 2,081 | 39 | -54.02% | 0.72% | -54.74% | -54.31% |

These values are historical simulation output, not a performance promise or
financial advice. The IEX feed is intentionally quality-gated but is not claimed
to be a complete consolidated US-market feed.

## Automated checks

- Test suite: 84 passed, 7 optional integration tests skipped before the final
  Airflow compatibility correction; focused regression suite: 14 passed afterward.
- Ruff lint: passed.
- Ruff formatting check: 155 files formatted.
- Python compile check: passed.
- `docker compose --env-file .env config --quiet`: passed.
- Airflow DAG import errors: none.
- `alpaca_api_pool`: one slot.
- Docker health: all long-running core services healthy after the run.

## Visual verification

The local Backtesting Lab loaded the newest run automatically and visibly showed:

- two selectable published runs;
- the 2026-08-24 through 2026-08-28 period;
- 6,232 certified observations, five sessions, and 145 trades;
- non-zero KPI cards, a five-session equity chart, bias controls, and the
  cross-asset comparison table;
- `API HEALTHY` with no visible empty-state or layout failure.
