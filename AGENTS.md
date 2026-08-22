# MarketPilot Project Instructions

## Mission

Build MarketPilot as a local, reproducible Docker Compose data platform for market data, SEC filings, derived indicators, signals, backtests, and a web application.

The initial scope is 10 to 20 fixed US equities plus SPY as the benchmark.

## Source of truth

Before changing code, read these files:

1. `AGENTS.md`
2. `docs/project-context.md`
3. `docs/architecture/architecture.md`
4. `docs/implementation-plan.md`
5. All accepted ADRs under `docs/decisions/`

When documentation and implementation conflict, stop and report the conflict. Do not silently change the architecture.

## Mandatory architecture

- Kafka transports market events.
- `market-producer` is a long-running Docker service.
- `raw-archive-sink` is a long-running Kafka consumer.
- Spark Structured Streaming is a long-running Docker service.
- Docker Compose owns the lifecycle of long-running services.
- Airflow must not start or stop Kafka, Spark Streaming, MariaDB, MinIO, the Backend API, or the Web App.
- Airflow schedules and monitors bounded jobs only:
  - SEC polling
  - Bronze to Silver Spark Batch
  - Silver to Gold Spark Batch
  - data-quality checks
  - backfill and replay
  - Parquet compaction
  - annual archive
- Airflow submits Spark Batch applications through `SparkSubmitOperator`.
- Bronze stores immutable raw data in MinIO. S3 is the future cloud replacement.
- Silver stores cleaned and normalized Parquet data in MinIO or S3.
- Gold stores application-ready data in MariaDB.
- MariaDB contains both active historical data and near-real-time modeled data required by the application.
- Raw payloads and long-term analytical archives must not be stored only in MariaDB.
- The browser communicates only with the Backend API.
- The browser must never connect directly to MariaDB or MinIO.

## Data-flow invariants

The certified batch path is:

`Bronze -> Spark Batch -> Silver -> Spark Batch -> Gold`

The live path is:

`Alpaca -> market-producer -> Kafka -> Spark Structured Streaming -> MariaDB Gold`

The raw archive path is:

`Kafka -> raw-archive-sink -> MinIO Bronze`

Live Gold data may be provisional. The post-market batch pipeline recalculates and publishes certified data.

## Development standards

- Target Python 3.12 unless a documented dependency conflict requires another version.
- Use type hints for production Python code.
- Use structured JSON logging.
- Store event timestamps in UTC.
- Use `America/New_York` for market and Airflow schedule definitions.
- Use an exchange calendar for holidays and early-close awareness.
- Never commit passwords, API keys, access tokens, connection strings, private endpoints, or personal data.
- Put safe placeholders in `.env.example`.
- Every Docker service must have a healthcheck when technically possible.
- Use `depends_on.condition: service_healthy` for readiness-sensitive dependencies.
- Long-running services must have an appropriate restart policy.
- All persistent state must use named volumes or object storage.
- Database writes must be idempotent.
- Market bars require a unique business key based on symbol and event timestamp.
- SEC filings require a unique key based on accession number.
- Spark Structured Streaming must use durable checkpoints.
- Airflow DAGs that mutate the same partitions or tables must use `max_active_runs=1`.
- Frequent polling DAGs use `catchup=False`.
- Historical processing uses a parameterized backfill DAG, not automatic catchup.
- Do not mount the Docker socket into Airflow unless the risk is documented and explicitly approved.
- Do not introduce Celery and Redis in the MVP unless LocalExecutor is proven insufficient.

## Quality requirements

- Add unit tests for business logic.
- Add integration tests for Kafka, object storage, Spark, and MariaDB boundaries.
- Add data-quality checks for freshness, completeness, duplicates, nulls, OHLC consistency, and expected market bars.
- Every schema must have an explicit version.
- Every published dataset must have lineage to source, run, code version, and data version.
- Quarantine malformed records instead of silently dropping them.
- Do not automatically delete MariaDB history after archive export in the MVP.
- Archive purge requires a separate retention decision and a verified restore test.

## Work process

Before editing:

1. Inspect the relevant files and current Git status.
2. State the proposed scope.
3. Identify assumptions, risks, and external dependencies.
4. Confirm the task does not conflict with an accepted ADR.

During implementation:

1. Make focused changes only.
2. Preserve unrelated user changes.
3. Keep services independently testable.
4. Prefer small, reviewable commits and milestones.

After editing:

1. Run relevant unit and integration tests.
2. Run formatting and linting.
3. Run `docker compose config` whenever Compose changes.
4. Inspect service health and logs when Docker is available.
5. Report changed files, executed commands, results, and unresolved risks.

## Expected commands

- Validate Compose: `docker compose config`
- Start services: `docker compose up -d`
- Show status: `docker compose ps`
- Show logs: `docker compose logs --tail=200`
- Stop services: `docker compose down`
- Run Python tests: `pytest`
- Run linting: `ruff check .`
- Run formatting check: `ruff format --check .`

## Definition of done

A task is not complete until:

- the requested behavior is implemented;
- relevant tests pass;
- failure and restart behavior were considered;
- secrets are not exposed;
- documentation reflects material architecture or behavior changes;
- the final response states any tests that could not be run.
