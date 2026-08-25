# Delivery Quality Report

## Verified on the target workstation

- `docker compose config --quiet` passes.
- Kafka, MinIO, MariaDB, Spark Master, Spark Worker, the producer, the raw sink,
  and Spark Streaming run locally and report healthy where healthchecks apply.
- Python 3.12 Ruff lint and formatting checks pass in a clean container.
- The Python 3.12 unit and contract suite passes; Docker-backed integration tests
  remain explicit opt-in checks.
- The opt-in Docker recovery integration test passes.
- The synthetic raw path writes Kafka events to MinIO Bronze.
- Spark Structured Streaming writes provisional, lineage-bearing Gold rows to MariaDB.
- Re-delivering a business key does not create a duplicate Gold row.
- Invalid events reach the Kafka DLQ without terminating the streaming application.
- Restarting `spark-streaming` resumes from the durable checkpoint.
- Recreating both the Spark Worker and streaming driver preserves shared state and
  resumes processing without duplicate business keys.
- Source-to-Gold p95 latency was measured for the Phase 3 synthetic run.
- Spark Batch reads immutable Bronze through S3A and writes schema-versioned,
  partitioned Snappy Parquet to MinIO Silver.
- Ten blocking Silver checks pass for the verified partition, including XNYS-aware
  expected-bar policy support.
- Reprocessing the same partition and run is idempotent: 1,881 business rows remain
  1,881 and reconciliation reports zero value changes.
- A deliberately failed completeness check exits non-zero, blocks staging and
  certified publication, and leaves the prior certified partition visible.
- Airflow imports all DAGs without errors and submits bounded Spark jobs without
  controlling long-running services.
- The Alpaca adapter preserves `MarketBarV1`, XNYS regular-session filtering,
  deterministic event IDs, and capped reconnect behavior in tests.
- A local SEC fixture was archived once in MinIO and published twice without
  duplicate accession rows; the second run inserted zero new rows.
- The SEC DAG completed successfully against the local fixture, with its production
  external-source gate disabled afterward.

## Deliberately deferred

- A real Alpaca websocket session remains an operator activation step because no
  API credentials were supplied.
- A live SEC request remains an operator activation step because a real monitored
  contact identity was not supplied.
- Backend API and Web App integration remain Phase 7 work.

The Docker-backed recovery test is opt-in because it restarts a running service:

```powershell
$env:MARKETPILOT_RUN_INTEGRATION = "1"
pytest tests/integration/test_streaming_restart.py
```

The Phase 4 Docker integration test is also opt-in because it submits multiple
bounded applications and intentionally exercises a failing gate:

```powershell
$env:MARKETPILOT_RUN_BATCH_INTEGRATION = "1"
pytest tests/integration/test_batch_medallion.py
```

The Phase 6 SEC integration check creates a temporary local HTTP fixture container
and verifies MinIO plus MariaDB boundaries:

```powershell
$env:MARKETPILOT_RUN_SEC_INTEGRATION = "1"
pytest tests/integration/test_sec_pipeline.py
```
