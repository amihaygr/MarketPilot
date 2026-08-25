# Services

Python services:

- `market_producer`: long-running Alpaca adapter and Kafka producer.
- `raw_archive_sink`: long-running Kafka consumer that writes Bronze objects.
- `sec_adapter`: bounded SEC EDGAR adapter triggered by Airflow or a safe internal interface.

The deterministic synthetic producer remains the safe default for local work.

## Phase 2 services

- `platform_init`: idempotently creates Kafka topics and MinIO buckets, then exits.
- `market_producer`: publishes deterministic `MarketBarV1` events once per configured interval.
- `raw_archive_sink`: validates events, archives valid payloads to Bronze, quarantines invalid
  payloads, and commits Kafka offsets only after the object upload succeeds.

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
