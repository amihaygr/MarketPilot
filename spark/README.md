# Spark Applications

Implemented:

- `jobs/stream_market_bars.py`: long-running Kafka to MariaDB Structured Streaming
  application. Valid records are written as provisional Gold through idempotent
  partition transactions. Invalid records are published to the configured Kafka DLQ.
- `jobs/bronze_to_silver.py`: explicit-schema Bronze validation, deterministic
  deduplication, quarantine on rejection, and partitioned Snappy Parquet output.
- `jobs/validate_silver.py`: blocking completeness, freshness, duplicate, null,
  OHLC, date, schema, and expected-session checks persisted to MariaDB.
- `jobs/silver_to_gold.py`: least-privilege staging followed by an atomic,
  quality-gated certified partition replacement and publication watermark.

Planned bounded application:

- `jobs/backfill_replay.py`: parameterized historical replay.

Docker Compose owns the streaming application lifecycle and its durable named-volume
checkpoints. Airflow submits only bounded applications.

The shared Spark image embeds Kafka and Hadoop S3A dependencies. Batch drivers run
as ephemeral `spark-batch` Compose containers and submit finite applications to the
existing standalone cluster. Phase 5 will submit the same files with
`SparkSubmitOperator` rather than changing their lifecycle.
