# ADR-007: Certified Historical Market-Data Acquisition

- Status: Accepted
- Date: 2026-09-05

## Context

The Phase 11 engine needs realistic certified price history. Writing downloaded
bars directly to MariaDB would bypass Kafka, immutable Bronze evidence, quality
gates, and lineage. Sending a historical burst to the live topic would also make
the continuously running Structured Streaming service process backfill traffic.

## Decision

- Airflow owns a manual, bounded acquisition workflow of at most 31 calendar days.
- Alpaca's multi-symbol stock-bars endpoint is paginated completely, rate limited,
  retried, and restricted to closed XNYS regular sessions.
- Exact upstream response pages are stored in MinIO Bronze under content-addressed
  SHA-256 keys before canonical publication.
- Canonical `MarketBarV1` events use `market.bars.1m.backfill.v1`. The live Spark
  application continues to consume only `market.bars.1m.v1`.
- The long-running raw sink consumes both topics and preserves topic, partition,
  and offset in every Bronze key.
- A bounded acquisition task waits until every produced Kafka position exists in
  Bronze. Spark certification cannot begin before that barrier succeeds.
- The existing Bronze-to-Silver, quality, and Silver-to-Gold jobs remain the only
  historical publication route. A backtest runs only after all mapped Gold tasks succeed.
- IEX coverage is explicit and configurable because IEX represents one exchange;
  missing minutes are not synthesized. The default blocking minimum is 80 percent.
- Completion manifests and deterministic run IDs make Airflow retries idempotent.

## Consequences

The workflow is slower than a direct database load and creates immutable raw
storage, but it provides reproducibility, replay evidence, and a single certified
publication model. SIP can be selected only when the account is entitled to it.
Elastic observability remains optional and is deferred to Phase 13 under ADR-006.
