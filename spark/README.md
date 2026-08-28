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
- `jobs/compact_silver.py`: bounded, recoverable Silver compaction with exact
  row/key/hash/schema validation and original-object backup.
- `jobs/archive_market_bars.py`: closed-year Gold export to verified, versioned
  Parquet plus matching MinIO and MariaDB manifests.
- `jobs/restore_archive_sample.py`: complete object checksum verification followed
  by a bounded restore into an isolated schema.
- `jobs/calculate_market_analytics.py`: bounded native Spark windows for versioned
  Indicators and explained Signals, followed by atomic daily Gold publication.

Planned bounded application:

- `jobs/backfill_replay.py`: parameterized historical replay.

Docker Compose owns the streaming application lifecycle and its durable named-volume
checkpoints. Airflow submits only bounded applications.

The shared Spark image embeds Kafka and Hadoop S3A dependencies. Batch drivers run
as ephemeral `spark-batch` Compose containers and submit finite applications to the
existing standalone cluster. Phase 5 will submit the same files with
`SparkSubmitOperator` rather than changing their lifecycle.
