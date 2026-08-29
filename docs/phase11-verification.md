# Phase 11 Verification

- Verification date: 2026-08-29
- Scope: local historical backtesting, orchestration, MinIO, MariaDB, API, and Web
- Verified run ID: `c42d4851-0587-56ac-91e8-9ac7009f9e87`
- Input: certified 2026-08-22 one-minute bars for AAPL, MSFT, and SPY
- Strategy: `SMA_CROSS_LONG_CASH` version 1, windows 20/50
- Assumptions: 10,000 initial capital, 1 bps transaction cost, 1 bps slippage

## Verified evidence

- Native Spark DataFrame execution completed on the standalone cluster.
- The signal derived from bar `t` is shifted before it becomes the applied position.
- The first run published 510 full-resolution curve rows, 3 summary rows, and 3
  bounded daily-equity rows.
- Repeating the same run ID produced the same counts: 1 run, 3 results, and 3
  daily-equity rows.
- MinIO contains 3 Parquet objects and a manifest with a 64-character SHA-256
  inventory checksum.
- MariaDB publication is transactional and the existing application identity has
  `SELECT` but receives error 1142 for an attempted no-op `UPDATE`.
- The list, detail, and daily-equity API endpoints returned HTTP 200 and did not
  expose `detailed_output_uri` or an `s3a://` path.
- `historical_backtest` is parsed and listed by Airflow as a manual DAG.
- Compose validation passed and all 18 long-running project services were healthy.
- Ruff check, Ruff formatting check, JavaScript syntax checks, and 77 unit/contract
  tests passed.

## Failure and recovery evidence

The first distributed implementation used a Python RDD and failed because the
Airflow driver uses Python 3.12 while the Spark worker image uses Python 3.10.
The implementation was corrected to use native Spark SQL/DataFrame windows for
distributed work; only bounded summary rows are collected by the driver.

The next run reached Gold publication and exposed a missing required `run_id` in
the `etl_watermark` insert. MariaDB rolled the transaction back, the statement was
fixed, and both the successful run and same-run retry were verified.

## Visual review

The in-app browser automation connector was blocked before navigation by its local
Trusted Path restriction. HTTP delivery, asset versioning, JavaScript syntax,
responsive CSS rules, real API responses, empty-state behavior, and single-point
chart rendering were verified. A final human visual review of
`http://localhost:3000/backtesting.html` remains the only manual acceptance item.

## Phase 12 resource gate

The healthy core stack used approximately 4.45 GiB of the 7.6 GiB Docker memory
allocation before a Spark Batch peak. Elasticsearch and Kibana are therefore a
No-Go under the current resource budget. ADR-006 remains Proposed and its profile
was not implemented or started.
