# MarketPilot Implementation Plan

## Delivery principle

Implement one verifiable vertical slice at a time. Each phase must have explicit acceptance criteria and a Git checkpoint. Do not connect external production-like sources before the synthetic path is reliable.

## Phase 0 - Repository and engineering baseline

### Scope

- Confirm repository structure.
- Configure Python packaging.
- Add linting and test configuration.
- Add safe environment-variable handling.
- Add logging conventions.
- Add architecture validation to the working agreement.

### Acceptance criteria

- `AGENTS.md` is loaded by Codex.
- `pytest` can run successfully even if the initial suite contains only smoke tests.
- `ruff check .` passes.
- No secrets exist in tracked files.
- Initial Git checkpoint exists.

## Phase 1 - Core Docker infrastructure

### Scope

- Kafka in KRaft mode.
- MinIO.
- MariaDB.
- Spark Master.
- One Spark Worker.
- Internal networks.
- Named volumes.
- Healthchecks.
- Safe `.env.example` integration.

### Excluded

- Airflow.
- Alpaca.
- SEC.
- API and Web App.
- Business transformations.

### Acceptance criteria

- `docker compose config` passes.
- `docker compose up -d` starts the core stack.
- All core services become healthy.
- Named volumes are visible.
- Restarting the stack preserves expected state.
- No real credentials are committed.

## Phase 2 - Synthetic raw path

### Scope

- Define the versioned market-bar event contract.
- Create a synthetic market producer.
- Publish deterministic sample bars to Kafka.
- Create the raw archive consumer.
- Write Bronze objects to MinIO.
- Add event identifiers and structured logs.

### Acceptance criteria

- A deterministic event appears in the Kafka topic.
- The same event is archived in Bronze.
- The Bronze object contains source time, ingestion time, event ID, and schema version.
- Re-running the producer does not corrupt existing objects.
- Malformed events go to quarantine or DLQ.

## Phase 3 - Live Spark Streaming to MariaDB

### Scope

- Create initial Gold DDL.
- Implement Spark Structured Streaming.
- Parse the market event schema.
- Configure event-time handling.
- Configure a durable checkpoint.
- Implement idempotent MariaDB upserts.
- Add an integration test for restart recovery.

### Acceptance criteria

- A synthetic Kafka event appears in `fact_market_bar_1m`.
- The business key prevents a duplicate row.
- Restarting streaming resumes from checkpoint.
- A malformed event does not terminate the query.
- p95 synthetic source-to-Gold latency is measured and documented.

## Phase 4 - Batch Medallion pipeline

### Scope

- Implement Bronze to Silver Spark Batch.
- Implement Silver validation and deduplication.
- Write partitioned Parquet.
- Implement Silver to Gold Spark Batch.
- Add publication status and data version.
- Add data-quality checks.

### Acceptance criteria

- Explicit Bronze to Silver to Gold data flow exists.
- Reprocessing a partition is idempotent.
- Silver files are queryable and schema-versioned.
- Certified publication is blocked by a failed quality check.
- Live provisional data can be reconciled with certified batch data.

## Phase 5 - Airflow orchestration

### Scope

- Add Airflow PostgreSQL metadata database.
- Add Scheduler, API Server or UI, and DAG Processor.
- Use LocalExecutor.
- Configure Spark connection.
- Implement `daily_market_close_dag`.
- Implement manual `backfill_replay_dag`.

### Acceptance criteria

- Airflow submits Spark Batch through `SparkSubmitOperator`.
- Airflow does not launch Spark Streaming.
- The daily DAG enforces ordered quality gates.
- `max_active_runs=1` protects conflicting writes.
- A failed Airflow scheduler does not stop live streaming.

## Phase 6 - External sources

### Alpaca scope

- Replace or complement the synthetic producer with the live adapter.
- Implement reconnect and exponential backoff.
- Use a market calendar.
- Preserve the same versioned event contract.

### SEC scope

- Implement filing discovery.
- Use a declared User-Agent.
- Throttle requests.
- Deduplicate accession numbers.
- Archive raw JSON.
- Implement `sec_polling_dag`.

### Acceptance criteria

- Live Alpaca events follow the tested synthetic contract.
- Reconnect does not create duplicate business rows.
- SEC access remains within the configured rate.
- A filing accession is modeled once.

## Phase 7 - Serving layer

### Scope

- Backend API.
- Gold read models.
- Pagination and filtering.
- Web App.
- Health and freshness endpoints.

### Acceptance criteria

- The browser communicates only with the API.
- The API identity cannot mutate Gold tables.
- Responses enforce bounded ranges and pagination.
- The UI shows data freshness and provisional or certified status.

## Phase 8 - Operations and archive

### Scope

- Weekly Parquet compaction.
- Annual archive.
- Archive manifest.
- Backup and restore procedure.
- Alerting and operational runbooks.

### Acceptance criteria

- Compaction preserves row counts and schema.
- Archive export passes row-count and checksum validation.
- A sample restore is successful.
- MariaDB history is not automatically deleted.
- Recovery steps are documented.

## Required checkpoints

Recommended Git checkpoints:

1. `bootstrap architecture and instructions`
2. `add core docker infrastructure`
3. `add synthetic kafka raw path`
4. `add spark streaming gold path`
5. `add batch medallion pipeline`
6. `add airflow orchestration`
7. `add external data sources`
8. `add api and web serving layer`
9. `add archive and operations`
