# Phase 5 Airflow Verification

Verified locally on 2026-08-25 with Docker Compose, Airflow 3.0.3, Spark 3.5.8,
PostgreSQL 16, MinIO, and MariaDB 11.4.

## Implemented boundary

```text
Airflow LocalExecutor
    -> SparkSubmitOperator
        -> Bronze to Silver
        -> blocking Silver quality gate
        -> Silver to Gold CERTIFIED

Docker Compose
    -> Kafka, producers, raw archive, and Spark Structured Streaming
```

Airflow has no Docker socket and does not start or stop the long-running data path.
The scheduler and Spark Structured Streaming have independent lifecycles.

## Runtime services

- PostgreSQL is the Airflow metadata database.
- `airflow-scheduler`, `airflow-api-server`, and `airflow-dag-processor` run as
  separate services with health checks.
- LocalExecutor is configured without Celery or Redis.
- The persisted `spark_standalone` connection targets
  `spark://spark-master:7077` in client deploy mode.
- The `spark_batch_pool` has one slot to serialize local Spark Batch submissions.

## Daily certification evidence

The manual synthetic-fixture run
`manual__2026-08-25T20:23:54.226828+00:00_1zuD6QLt` completed successfully for
logical date `2026-08-22` in this order:

1. `exchange_session_gate`
2. `bronze_to_silver`
3. `silver_quality_gate`
4. `silver_to_gold_certified`

The synthetic fixture uses an explicit 171-bar override because its sample date is
a weekend. Normal scheduled runs derive the expected bar count from the XNYS
exchange calendar.

MariaDB verification for pipeline run
`5d81f65c-1fac-5a3c-b62f-bc5ac34e0abd` showed:

- 1,881 CERTIFIED bars across 11 symbols;
- all required data-quality checks passed;
- Silver DQ watermark `VALIDATED`;
- certified publication watermark `PUBLISHED`;
- zero rows left in staging after publication.

The first Gold attempt exposed a Python 3.12 Airflow driver versus Python 3.10
Spark worker mismatch in executor-side `foreachPartition`. The publisher now keeps
Spark transformations distributed and streams the bounded result through the
driver in batches of 1,000 rows. The Airflow retry then completed successfully.

## Scoped backfill evidence

The manual run `manual__2026-08-25T20:42:57.983831+00:00_R49cXc5b` replayed only
AAPL for `2026-08-22`. Dynamic task mapping created one mapped instance for each
Spark stage. It published under partition key `2026-08-22|symbols=AAPL` with both
`VALIDATED` and `PUBLISHED` watermarks.

After the scoped replay, every one of the 11 configured symbols still had 171
CERTIFIED bars and the full date still contained 1,881 rows. This verifies that a
partial backfill does not delete other symbols in the same date partition.

## Failure and restart behavior

- The Gold task retried without repeating successful upstream tasks.
- The Airflow scheduler was stopped and recreated while Spark Structured Streaming
  remained running and healthy.
- Airflow task and DAG-run state survived in PostgreSQL.
- Both DAGs use `max_active_runs=1`; scheduled polling uses `catchup=False`.
- Both DAGs are intentionally paused after verification. Phase 6 will connect the
  market-session-aware external source before enabling the daily schedule.

## Quality gates

- `ruff format --check .`: passed.
- `ruff check .`: passed.
- `pytest -q`: 29 passed, 3 opt-in integration tests skipped.
- `scripts/validate_repository.py`: passed.
- `docker compose config --quiet`: passed.
- DAG import errors: none.

The Docker-backed Airflow behavior covered by the opt-in integration test was also
executed directly during this verification. External-source behavior remains Phase
6 scope.
