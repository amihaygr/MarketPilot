# Spark Applications

Planned Spark applications:

- `streaming/market_bars_to_gold`: long-running Structured Streaming application.
- `batch/bronze_to_silver`: bounded cleansing and normalization job.
- `batch/silver_to_gold`: bounded enrichment and certified publication job.
- `batch/compact_parquet`: bounded small-file compaction job.

Airflow submits only the bounded applications. Docker Compose owns the streaming application lifecycle.
