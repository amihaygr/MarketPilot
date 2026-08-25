# Delivery Quality Report

## Verified on the target workstation

- `docker compose config --quiet` passes.
- Kafka, MinIO, MariaDB, Spark Master, Spark Worker, the producer, the raw sink,
  and Spark Streaming run locally and report healthy where healthchecks apply.
- Python 3.12 Ruff lint and formatting checks pass in a clean container.
- Thirteen unit and contract tests pass.
- The opt-in Docker recovery integration test passes.
- The synthetic raw path writes Kafka events to MinIO Bronze.
- Spark Structured Streaming writes provisional, lineage-bearing Gold rows to MariaDB.
- Re-delivering a business key does not create a duplicate Gold row.
- Invalid events reach the Kafka DLQ without terminating the streaming application.
- Restarting `spark-streaming` resumes from the durable checkpoint.
- Recreating both the Spark Worker and streaming driver preserves shared state and
  resumes processing without duplicate business keys.
- Source-to-Gold p95 latency was measured for the Phase 3 synthetic run.

## Deliberately deferred

- Airflow runtime and DAG import verification remain Phase 5 work.
- Bronze-to-Silver and Silver-to-Gold batch integration remain Phase 4 work.
- External Alpaca and SEC integration remain Phase 6 work.
- Backend API and Web App integration remain Phase 7 work.

The Docker-backed recovery test is opt-in because it restarts a running service:

```powershell
$env:MARKETPILOT_RUN_INTEGRATION = "1"
pytest tests/integration/test_streaming_restart.py
```
