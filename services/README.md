# Services

Planned Python services:

- `market_producer`: long-running Alpaca adapter and Kafka producer.
- `raw_archive_sink`: long-running Kafka consumer that writes Bronze objects.
- `sec_adapter`: bounded SEC EDGAR adapter triggered by Airflow or a safe internal interface.

Begin with a deterministic synthetic producer before implementing external sources.

## Phase 2 services

- `platform_init`: idempotently creates Kafka topics and MinIO buckets, then exits.
- `market_producer`: publishes deterministic `MarketBarV1` events once per configured interval.
- `raw_archive_sink`: validates events, archives valid payloads to Bronze, quarantines invalid
  payloads, and commits Kafka offsets only after the object upload succeeds.

The Alpaca adapter is preserved in `market_producer/alpaca.py` but is not used until Phase 6.
