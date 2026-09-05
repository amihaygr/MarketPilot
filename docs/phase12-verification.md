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

## Release-candidate extension

A wider release-candidate run was completed on 2026-09-05 for 20 XNYS trading
sessions from 2026-08-03 through 2026-08-28. The acquisition DAG
`phase12_month_verification_20260905` completed all 20 mapped acquisition,
Bronze-to-Silver, quality-gate, and Certified Gold tasks before publishing its
backtest.

The first monthly result exposed an important cross-run contamination risk:
old synthetic verification rows existed inside the same calendar range. The
backtest treated a synthetic Saturday as a session, and the historical
Bronze-to-Silver task could retain a synthetic row when IEX had no bar for the
same minute. The release gate therefore added two explicit protections:

- backtests join input to native Spark SQL windows derived from the XNYS
  exchange calendar and record excluded non-session rows in their manifest;
- the Phase 12 Bronze-to-Silver plan reads only `source=alpaca`, so a certified
  historical partition cannot borrow an older synthetic observation.

The focused repair run `phase12_source_isolation_20260905` rebuilt and
atomically replaced the 2026-08-25 partition. A read-only database check then
found 1,166 Certified rows for the requested symbols, all sourced from Alpaca.
After checkpointing the implementation, the scheduler loaded code version
`bed1fb7`. The final bounded Airflow run
`phase12_month_lineage_final_20260905` completed successfully and published
backtest run `48cf39e5-ccb0-5df6-9149-df5bc8741469`.

Final published results:

| Symbol | Observations | Trades | Net return | Benchmark | Excess | Max drawdown |
|---|---:|---:|---:|---:|---:|---:|
| AAPL | 7,794 | 179 | 0.19% | 2.60% | -2.41% | -5.65% |
| MSFT | 7,759 | 195 | -5.55% | 2.60% | -8.15% | -9.07% |
| SPY | 7,796 | 181 | -3.47% | 2.60% | -6.07% | -5.70% |

The final manifest points to code version `bed1fb7`, reconciled 23,349 detailed
rows and three Parquet symbol partitions, and explicitly excluded 513 old
synthetic rows dated Saturday
2026-08-22. Those audit rows remain in Gold, but none is eligible for the final
calculation. The API returned exactly 20 daily AAPL equity points, all on valid
XNYS dates.

The first corrected attempt also proved failure recovery: a Python 3.12 driver
versus Python 3.10 Spark-worker mismatch was triggered by constructing a
DataFrame from a Python collection. The implementation was changed to create
the tiny session table with native Spark SQL; Airflow retried and succeeded
without restarting the platform or modifying business data.

The Backtesting Lab was then verified visually in the in-app browser. It loaded
the newest run automatically, showed 23,349 certified observations, 20
sessions, 555 trades, non-zero KPI cards, a populated equity chart, the full
comparison table, and `API HEALTHY`. A responsive readiness-card issue found at
the narrower verification viewport was corrected before release.

The final release gate completed with 86 tests passing and seven opt-in Docker
integration suites skipped; those boundaries were exercised directly by the
successful Airflow, Spark, Kafka, MinIO, MariaDB, API, and browser run above.
Ruff lint, Ruff formatting, JavaScript syntax, Compose validation, and Airflow
DAG imports all passed. Kafka historical end offsets were 10,138 and 20,223
across the two populated partitions. August Bronze held 22 content-addressed
source pages, 26 successful session manifests, and 32,969 immutable per-offset
market-bar objects after the focused replay.

All 18 long-running Compose services reported healthy. The operational monitor
correctly retained a market-freshness warning because the stack was resumed on
a Saturday and the newest available market observation predated its 96-hour
threshold. The Alpaca producer itself was connected to IEX and subscribed to
the configured 11-symbol universe; no freshness threshold was weakened to make
the release appear green.

These results remain a short IEX historical simulation of a simple strategy.
They are evidence that the engineering workflow works, not evidence of future
performance or financial advice.
