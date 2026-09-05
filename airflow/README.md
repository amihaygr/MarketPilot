# Airflow orchestration

Phase 5 runs Airflow 3 with `LocalExecutor`, a dedicated PostgreSQL metadata
database, Scheduler, API Server and DAG Processor. The UI is exposed locally at
`http://localhost:8080`; credentials come from the ignored `.env` file.

## Implemented DAGs

- `daily_market_close`: weekdays at 16:30 `America/New_York`. The first task checks
  the XNYS calendar and short-circuits holidays and weekends. A successful session
  runs Bronze to Silver, blocking Silver quality checks, then atomic Gold Certified
  publication.
- `backfill_replay`: manual only. It validates a maximum 31-calendar-day range and a
  subset of `MARKET_SYMBOLS`, skips closed sessions, and dynamically maps the same
  three bounded Spark jobs for each eligible date.
- `sec_polling`: every 15 minutes on weekdays within the configured
  06:00-22:00 `America/New_York` window. A gate skips the bounded poll while
  `SEC_POLL_ENABLED=false`; `force=true` exists only for reviewed manual runs.
- `historical_backtest`: manual only. It validates a bounded certified-data scope,
  creates a stable run identity, and submits the versioned historical backtest to
  Spark. Full curves are stored as Parquet in MinIO while bounded summaries and
  daily equity points are published transactionally to MariaDB Gold.
- `historical_market_backfill`: manual only. It acquires at most 31 calendar days
  from Alpaca, archives source pages, sends canonical events through a dedicated
  Kafka topic, waits for exact Bronze offsets, maps the existing certification
  chain by session, and finally runs the historical backtest.

`spark_batch_pool`, `sec_api_pool`, and `alpaca_api_pool` each have one slot. All mutating DAGs use
`max_active_runs=1`; SEC polling also uses `catchup=False`. This serializes local
publication work and prevents overlapping SEC requests.

## Synthetic weekend verification

The Phase 2 fixture is dated Saturday 2026-08-22. A manual verification may set
`expected_bars_override=171`; routine schedules leave the value empty and always
use the exchange calendar.

Airflow has no Docker socket and no DAG references the Structured Streaming
application. Docker Compose remains the only lifecycle owner for long-running
services.
