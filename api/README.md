# Backend API

The Phase 7 Backend API is a FastAPI service at <http://localhost:8000>. It is the
only application-facing access path to MariaDB Gold and publishes OpenAPI
documentation at <http://localhost:8000/docs>.

## Version 1 endpoints

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/health/live` | Process liveness without a database query |
| `GET` | `/health/ready` | MariaDB readiness using the application identity |
| `GET` | `/api/v1/symbols` | Active symbols, row counts, latest time and state |
| `GET` | `/api/v1/market-bars` | Filtered, bounded and paginated one-minute OHLCV |
| `GET` | `/api/v1/sec-filings` | Filtered and paginated SEC filing metadata |
| `GET` | `/api/v1/freshness` | Market, SEC, per-symbol and pipeline freshness |

Market bars require `symbol`, default to a seven-day UTC window, and reject
ranges longer than 31 days. Filing queries default to one year. Both collections
limit pages to 1 through 1,000 and page size to 1 through 200.

The `marketpilot_app` MariaDB identity receives `SELECT` only on `dim_symbol`,
`fact_market_bar_1m`, `fact_sec_filing`, and `etl_watermark`. The API container
receives only this identity, bounded-query configuration and code-version metadata;
it does not receive root, MinIO, Alpaca, ingestion, publisher, SEC, or Airflow
credentials.

Response models intentionally omit internal Bronze URIs, Kafka positions, pipeline
run IDs, and database identifiers. SEC source URLs remain available for direct
links to the public filing source.
