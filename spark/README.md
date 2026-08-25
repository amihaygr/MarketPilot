# Spark Applications

Implemented:

- `jobs/stream_market_bars.py`: long-running Kafka to MariaDB Structured Streaming
  application. Valid records are written as provisional Gold through idempotent
  partition transactions. Invalid records are published to the configured Kafka DLQ.

Planned bounded applications:

- `jobs/bronze_to_silver.py`: cleansing and normalization.
- `jobs/silver_to_gold.py`: enrichment and certified publication.
- `jobs/backfill_replay.py`: parameterized historical replay.

Docker Compose owns the streaming application lifecycle and its durable named-volume
checkpoints. Airflow submits only bounded applications.
