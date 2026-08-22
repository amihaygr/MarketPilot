# ADR-002: Airflow Owns Bounded Work Only

- Status: Accepted
- Date: 2026-08-22

## Context

The platform includes both workflows that start and finish and services that must remain active continuously. Airflow is effective for dependency-driven bounded workflows but is not a service supervisor.

Running Spark Structured Streaming as an Airflow task would create an indefinitely active task, confusing retry behavior, and the risk of multiple concurrent streaming consumers.

## Decision

Airflow owns:

- SEC polling;
- Bronze to Silver Spark Batch;
- Silver to Gold Spark Batch;
- data-quality gates;
- backfill and replay;
- Parquet compaction;
- annual archive.

Airflow submits Spark Batch work through `SparkSubmitOperator`.

Airflow does not own the lifecycle of:

- Kafka;
- market-producer;
- raw-archive-sink;
- Spark Structured Streaming;
- MariaDB;
- MinIO;
- Backend API;
- Web App.

Docker Compose owns these long-running services in the local MVP.

## Consequences

### Positive

- The streaming path remains available if Airflow is unavailable.
- Airflow task state represents bounded work accurately.
- Docker restart policies and healthchecks manage service recovery.
- Spark Batch monitoring remains visible in Airflow.

### Negative

- Service health monitoring is separate from Airflow DAG state.
- The platform needs freshness and heartbeat monitoring for long-running services.

## Rejected alternative

Start Spark Streaming each morning from Airflow and stop it after market close.

This was rejected because missed or duplicated DAG runs could interrupt real-time processing or create multiple streaming applications.
