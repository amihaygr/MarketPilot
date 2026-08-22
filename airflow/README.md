# Airflow

Planned DAGs:

- `sec_polling_dag`
- `daily_market_close_dag`
- `weekly_compaction_dag`
- `annual_archive_dag`
- `backfill_replay_dag`

The MVP uses LocalExecutor and a separate PostgreSQL metadata database.

Airflow must not launch or supervise Spark Structured Streaming.
