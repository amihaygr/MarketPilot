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

Status: completed and locally verified on 2026-08-25. See
`docs/phase3-verification.md` for runtime evidence.

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

Status: completed and locally verified on 2026-08-25. See
`docs/phase4-verification.md` for runtime evidence.

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

Status: completed and locally verified on 2026-08-25. See
`docs/phase5-verification.md` for runtime evidence.

### Scope

- Add Airflow PostgreSQL metadata database.
- Add Scheduler, API Server or UI, and DAG Processor.
- Use LocalExecutor.
- Configure Spark connection.
- Implement `daily_market_close`.
- Implement manual `backfill_replay`.

### Acceptance criteria

- Airflow submits Spark Batch through `SparkSubmitOperator`.
- Airflow does not launch Spark Streaming.
- The daily DAG enforces ordered quality gates.
- `max_active_runs=1` protects conflicting writes.
- A failed Airflow scheduler does not stop live streaming.

## Phase 6 - External sources

Status: completed and locally verified on 2026-08-26. See
`docs/phase6-verification.md` for runtime evidence. Alpaca authentication and the
IEX websocket were activated locally on 2026-08-26. Live SEC polling was then
verified for idempotency and enabled with an identifiable local User-Agent.

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

Status: completed and locally verified on 2026-08-26. See
`docs/phase7-verification.md` for API, UI, privilege, and restart evidence.

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

Status: completed and locally verified on 2026-08-28. See
`docs/phase8-verification.md` for compaction, archive, backup, restore, monitoring,
and failure-recovery evidence.

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

## Phase 9 - Explainable market analytics

Status: completed and locally verified on 2026-08-28. See
`docs/phase9-verification.md` for Spark, MariaDB, API, privilege, Dashboard, and
idempotency evidence.

### Scope

- Versioned SMA, RSI, realized-volatility, and volume-ratio indicators.
- Explainable threshold-crossing and volume observations.
- Atomic, idempotent Gold publication after the certified daily path.
- Blocking analytics quality rules and publication watermark.
- Bounded read-only Indicator and Signal APIs.
- Dashboard indicators, SMA overlay, and recent explained Signals.

### Acceptance criteria

- Indicator and Signal business keys remain unique after reprocessing.
- RSI and Signal strength ranges are enforced before publication.
- A static partition produces identical row counts across repeated runs.
- The application identity can read analytics but cannot mutate them.
- Browser analytics requests pass only through the Backend API.
- Every row carries model/schema, run, code, data, and certification lineage.

## Phase 10 - Final showcase and delivery

Status: implemented and locally verified on 2026-08-28. The Project Story is
the presentation artifact for this phase. See `docs/phase10-verification.md`
for release evidence and the remaining manual visual-review note.

### Scope

- A dedicated Project Story served by the existing Nginx Web App.
- A clear end-to-end demo route across application and engineering interfaces.
- A final presentation package for academic review and interviews.
- Review-ready README, architecture narrative, evidence and delivery notes.
- A final release gate covering tests, formatting, service health, logs and secrets.

### Architecture boundary

- The Project Story may read only existing bounded Backend API endpoints.
- It must not connect directly to MariaDB, MinIO, Kafka or Airflow.
- Dated verification evidence must not be presented as live production state.
- The analytical Dashboard remains a decision surface, not a presentation page.

### Acceptance criteria

- A reviewer can understand the problem, architecture and key decisions before a live demo.
- The demo guide traverses source, transport, storage, compute, orchestration and serving.
- Every quantitative claim is either live through the API or tied to a dated verification file.
- The Project Story is responsive, keyboard accessible and contains no credentials.
- All final release gates pass and the delivery has a Git checkpoint.

## Phase 11 - Historical backtesting

Status: implemented and locally verified on 2026-08-29. See ADR-005 and
`docs/phase11-verification.md`. Final visual acceptance remains manual because the
local browser connector rejected its Trusted Path before navigation.

### Scope

- Versioned, long-or-cash SMA crossover strategy.
- Parameterized Spark Batch backtest over certified one-minute Gold bars.
- Next-bar position application, transaction costs, slippage, and SPY comparison.
- Full-resolution Parquet output in MinIO and bounded Gold read models in MariaDB.
- Blocking quality checks, idempotent publication, and complete run lineage.
- Manual Airflow DAG submitted through `SparkSubmitOperator`.
- Read-only Backend API and interactive Backtesting dashboard.

### Acceptance criteria

- Repeating the same run ID and parameters does not create duplicate business rows.
- No bar can influence a position applied to that same bar's return.
- Runs with non-certified, missing, duplicated, or invalid OHLC input are rejected.
- Costs and slippage are explicit and included in net performance.
- Summary metrics and the daily equity curve reconcile with detailed Parquet output.
- The browser reads results only through the Backend API.
- Every run carries strategy, schema, run, code, and data lineage.
- Unit, integration, lint, formatting, Compose, restart, and visual checks pass.

### Checkpoints

1. `add versioned historical backtesting engine`
2. `add backtest orchestration and serving`
3. `add interactive backtesting experience`

## Phase 12 - Alpaca historical acquisition and certified backfill

Status: implemented and release-candidate verified on 2026-09-05 across 20
XNYS trading sessions. Runtime evidence is recorded in
`docs/phase12-verification.md`. The design is accepted in ADR-007.

### Scope

- Manual, parameterized Airflow DAG for at most 31 calendar days.
- Multi-symbol Alpaca historical IEX acquisition with retry, rate limiting, and pagination.
- Exact, content-addressed source-page archive in MinIO Bronze.
- Dedicated Kafka topic for historical events, isolated from live Structured Streaming.
- A Bronze barrier that proves every produced Kafka offset was archived before Spark starts.
- Existing Bronze-to-Silver, blocking quality, and Silver-to-Gold Certified jobs.
- Alpaca source-partition isolation during the historical Bronze-to-Silver step.
- Automatic Phase 11 backtest after every requested market session is certified.
- Native Spark SQL filtering against XNYS regular-session windows before backtesting.
- Retry-stable run identities and completion manifests.

### Acceptance criteria

- Historical data never bypasses Kafka or the immutable Bronze layer.
- Airflow runs only bounded work and does not own any long-running service lifecycle.
- API credentials remain in the ignored `.env` and never enter manifests or logs.
- Pagination is complete and upstream source payloads are retained by SHA-256.
- Publication is blocked when the minimum per-symbol IEX coverage is not met.
- Repeating an Airflow run reuses completed session manifests without duplicating Gold rows.
- The final backtest reads Certified Gold only.
- Non-session rows are excluded explicitly and counted in the immutable run manifest.

## Phase 13 - Optional local observability

Status: proposed. Implementation remains gated by ADR-006 and a local resource measurement.

Candidate scope remains an optional Elasticsearch and Kibana Compose profile for
operational logs only, with bounded retention and no dependency from the core platform.

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
10. `add explainable market analytics`
11. `add final showcase and delivery package`
12. `add versioned historical backtesting engine`
13. `add backtest orchestration and serving`
14. `add interactive backtesting experience`
15. `add certified alpaca historical backfill`
