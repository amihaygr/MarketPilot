# Services

Python services:

- `market_producer`: long-running Alpaca adapter and Kafka producer.
- `raw_archive_sink`: long-running Kafka consumer that writes Bronze objects.
- `sec_adapter`: bounded SEC EDGAR adapter triggered by Airflow or a safe internal interface.
- `backend_api`: long-running, read-only FastAPI service for application-facing Gold data.

The deterministic synthetic producer remains the safe default for local work.

## Phase 2 services

- `platform_init`: idempotently creates Kafka topics and MinIO buckets, then exits.
- `market_producer`: publishes deterministic `MarketBarV1` events once per configured interval.
- `raw_archive_sink`: validates events, archives valid payloads to Bronze, quarantines invalid
  payloads from both live and historical topics, and commits Kafka offsets only after
  the object upload succeeds.

## Phase 6 external adapters

- `market_producer` selects `synthetic` or `alpaca` through
  `MARKET_DATA_SOURCE`. The Alpaca implementation uses the same `MarketBarV1`
  contract, XNYS regular-session filtering, graceful shutdown, and capped
  exponential reconnect backoff.
- `sec_adapter` is a bounded job, not a long-running service. It archives the SEC
  submissions response in Bronze before idempotently publishing filing metadata
  to MariaDB. Airflow normally invokes the same Python boundary.

External sources are disabled by default. Activation requires local credentials or
contact identity and the review steps in `docs/runbooks/external-source-activation.md`.

The Phase 12 historical adapter is a bounded Airflow task. It paginates Alpaca's
multi-symbol bars endpoint, archives exact source pages by SHA-256, publishes
`MarketBarV1` events to `market.bars.1m.backfill.v1`, and waits until the
long-running raw sink has persisted every Kafka position in Bronze.

## Phase 7 serving service

`backend_api` provides bounded symbol, market-bar, SEC-filing, freshness, and
historical-backtest reads, plus health reads. Docker Compose owns its lifecycle.
It receives only the MariaDB application identity and never receives infrastructure
or source credentials.
