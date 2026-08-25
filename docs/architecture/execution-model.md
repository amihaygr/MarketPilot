# Execution and Orchestration Model

## The short answer

Airflow does schedule Spark, but only bounded Spark Batch applications. Airflow does not schedule or keep Spark Structured Streaming alive.

## Ownership matrix

| Component | Started by | Trigger | Completion model | Restart owner |
|---|---|---|---|---|
| Kafka | Docker Compose | Environment start | Never under normal operation | Docker |
| Market producer | Docker Compose | Environment start | Never | Docker |
| Raw archive sink | Docker Compose | Environment start | Never | Docker |
| Spark Streaming | Docker Compose | Environment start | Never | Docker |
| Spark Batch | Airflow via `SparkSubmitOperator` | Schedule or manual run | Finite job | Airflow retry policy |
| SEC polling | Airflow | Every 15 minutes | Finite request batch | Airflow retry policy |
| MariaDB and MinIO | Docker Compose | Environment start | Never | Docker |
| Daily certification | Airflow | 16:30 New York on trading days | Finite DAG run | Airflow |

## Automatic streaming startup

`docker compose up -d` creates the infrastructure. Compose waits for Kafka and MariaDB health checks before it starts `spark-streaming`. The Spark process opens a Kafka subscription and continues until stopped or failed. A restart policy starts it again after an unexpected exit. Its durable checkpoint controls offset recovery.

This is automatic startup, but it is not time scheduling. The process is event-driven and permanent.

For the local MVP, the streaming query owns two subdirectories in the
`spark-checkpoints` named volume: one for provisional Gold and one for DLQ progress.
The Spark image embeds its Kafka connector during image build so the internal runtime
network does not need Internet access. The official Spark 3.5.8 image uses Python
3.10; this is a documented dependency exception limited to Spark applications.

## Airflow to Spark interaction

The scheduler creates a DAG run. `SparkSubmitOperator` submits a finite application to the Spark master. Airflow waits for a terminal state, records logs and duration, applies retries, and allows downstream publication only after quality gates pass.

The daily path is explicitly:

`Bronze -> Spark Batch -> Silver -> quality gate -> Spark Batch -> Gold certified -> publication watermark`

The live path is explicitly:

`Alpaca -> producer -> Kafka -> Spark Structured Streaming -> Gold provisional`

The raw recovery path is explicitly:

`Kafka -> raw archive sink -> Bronze`

## Why both Gold paths are valid

Streaming provides low latency and marks its output `PROVISIONAL`. Batch recomputes the complete trading session from immutable Bronze data, validates it, and idempotently replaces or certifies the partition. Consumers can choose whether provisional data is acceptable.

## Failure semantics

| Failure | Expected behavior |
|---|---|
| Producer disconnect | Reconnect with bounded exponential backoff; no fabricated bars |
| Kafka unavailable | Producer retries; consumer offsets remain recoverable |
| Streaming process crash | Compose restarts; Spark resumes from checkpoint |
| Malformed event | Quarantine with reason and source metadata |
| Batch transformation failure | Airflow retries; no publication watermark advances |
| Quality gate failure | Partition remains unpublished and prior certified data remains visible |
| MariaDB write ambiguity | Retry only through idempotent business-key upsert |
| Archive verification failure | Manifest remains unverified; no purge is permitted |
