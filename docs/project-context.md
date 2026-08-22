# MarketPilot Project Context

## Purpose

MarketPilot is a solo data-engineering capstone project intended to demonstrate a complete local data platform using Kafka, Spark, Airflow, Python, MariaDB, MinIO, and Docker Compose.

The product provides market monitoring, indicators, signals, historical analysis, and SEC filing context for traders and casual investors. It is an engineering and analytics project, not an automated trading execution system.

## MVP scope

- 10 to 20 fixed US equities.
- SPY as the benchmark.
- One-minute OHLCV market bars.
- SEC EDGAR filing metadata and raw JSON.
- Near-real-time processing.
- Batch cleansing, enrichment, certification, backfill, and archive.
- Backend API and Web App over MariaDB Gold.
- Local Docker Compose deployment.

## Data sources

### Alpaca Market Data

Pull one-minute OHLCV bars for the configured equities and SPY.

Required fields:

- symbol
- event timestamp
- open
- high
- low
- close
- volume
- source
- ingestion timestamp
- schema version
- event identifier

At 20 equities plus SPY and approximately 390 regular market minutes, the upper bound is about 8,190 one-minute bar events per regular trading day. This is small enough for MariaDB serving tables, but raw event payloads still belong in object storage for replay and lineage.

### SEC EDGAR

Collect filing metadata and raw JSON from SEC submissions and XBRL APIs.

Required operational behavior:

- Declare a descriptive User-Agent with a contact address.
- Throttle below the SEC maximum rate. The project default is five requests per second.
- Poll for new filings every 15 minutes in the configured window.
- Deduplicate by accession number.
- Save raw JSON to Bronze.
- Save modeled filing metadata to Gold.

## User-facing flow

The browser never connects directly to MariaDB or MinIO.

`Browser -> Web App -> Backend API -> MariaDB Gold`

## Live data path

`Alpaca -> market-producer -> Kafka -> Spark Structured Streaming -> MariaDB Gold`

In parallel:

`Kafka -> raw-archive-sink -> MinIO Bronze`

The streaming job is a long-running service. It is not an Airflow task.

## Certified batch path

`Bronze -> Spark Batch -> Silver -> Spark Batch -> Gold`

Airflow submits and monitors both Spark Batch applications. Data-quality gates must pass before certified publication.

## Storage decisions

### MariaDB

MariaDB stores application-ready modeled data, including:

- active historical one-minute bars;
- near-real-time bars;
- indicators;
- signals;
- SEC filing metadata;
- backtest results;
- data-quality results;
- ETL watermarks;
- archive manifests.

### MinIO and future S3

MinIO stores:

- immutable Bronze events and source payloads;
- Silver Parquet datasets;
- Spark checkpoints if the connector configuration supports it reliably;
- annual Parquet archives;
- manifests and checksums.

S3 is the future cloud replacement for MinIO. Paths and code should avoid unnecessary MinIO-specific assumptions.

## Airflow responsibility

Airflow owns schedules, dependencies, retries, timeouts, pools, logs, and status for bounded work.

Airflow runs:

- SEC polling;
- Bronze to Silver Spark Batch;
- Silver to Gold Spark Batch;
- quality checks;
- daily certification;
- backfill and replay;
- weekly Parquet compaction;
- annual archive.

Airflow does not start or stop:

- Kafka;
- market-producer;
- raw-archive-sink;
- Spark Structured Streaming;
- MariaDB;
- MinIO;
- Backend API;
- Web App.

These are long-running Docker services.

## Automatic streaming lifecycle

1. Docker Compose starts the infrastructure services.
2. Healthchecks confirm Kafka, Spark, MariaDB, and MinIO readiness.
3. Docker starts the producer, raw archive consumer, and Spark Streaming application.
4. The producer connects to Alpaca and publishes market events.
5. Spark consumes micro-batches every 30 to 60 seconds.
6. Spark uses a checkpoint to preserve query progress.
7. MariaDB writes use idempotent upserts.
8. If streaming fails, Docker restarts the service and Spark resumes from its checkpoint.

## Time handling

- Store timestamps in UTC.
- Use `America/New_York` for schedules and market-session logic.
- Do not use a fixed UTC offset for US market time.
- Use a market calendar for holidays and early closes.

## Security boundaries

- Credentials are local secrets and never committed.
- Databases and data infrastructure remain on internal Docker networks.
- Only the ports needed for local development are published.
- The API uses a read-only or narrowly scoped database user.
- Ingestion and publisher identities are separated from API identities.
- Airflow metadata PostgreSQL is separate from business MariaDB.

## MVP success criteria

- A synthetic bar travels from producer to Kafka, Bronze, Spark Streaming, and MariaDB.
- The event is visible through the Backend API.
- Streaming resumes from checkpoint after restart.
- Reprocessing the same event does not create a duplicate business row.
- The daily Airflow DAG shows explicit Bronze to Silver to Gold dependencies.
- Airflow failure does not stop the live streaming path.
- SEC polling stores an accession number once.
- Annual archive verifies row count and checksum without automatically deleting MariaDB history.
