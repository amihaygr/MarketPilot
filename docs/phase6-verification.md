# Phase 6 External Sources Verification

Verified locally on 2026-08-26 with Docker Compose, the official Alpaca Python
SDK 0.44.0, a deterministic local SEC fixture, Airflow 3.0.3, MinIO, and MariaDB.
Alpaca authentication and its IEX websocket were verified with local secrets. No
request was sent to `sec.gov`; SEC verification used the local fixture only.

## Implemented boundaries

```text
Long-running live path
Alpaca WebSocket -> market-producer -> Kafka -> existing raw and streaming paths

Bounded filings path
Airflow sec_polling -> SEC submissions JSON -> immutable MinIO Bronze object
                                           \-> MariaDB fact_sec_filing
```

Docker Compose still owns the long-running producer. Airflow owns only the bounded
SEC polling run and never starts or stops Kafka, Spark Streaming, MariaDB, or
MinIO.

## Alpaca adapter

- `MARKET_DATA_SOURCE` selects `synthetic` or `alpaca`; synthetic remains the
  tracked example default, while the verified workstation now runs `alpaca`.
- The adapter subscribes to bars through the official SDK and converts them to the
  existing schema-versioned `MarketBarV1` contract.
- Event IDs are deterministic across reconnects for the same feed, symbol,
  interval, and market minute.
- Only regular XNYS session minutes are published.
- Disconnects use capped exponential backoff, and SIGTERM/SIGINT trigger a
  graceful stream stop and Kafka flush.
- The rebuilt producer image imports Alpaca SDK 0.44.0 successfully. Contract,
  calendar, conversion, and retry behavior are covered by unit tests.

The local credentials passed a read-only latest-bar request. The long-running
producer then connected to `wss://stream.data.alpaca.markets/v2/iex` and subscribed
successfully to all 11 configured symbols. No trading endpoint was called.

## SEC adapter and persistence

- The client uses `data.sec.gov/submissions/CIK##########.json`, an identifiable
  User-Agent, a configurable request timeout, retry/backoff, and a default limit
  of five requests per second.
- Raw response bytes are archived before database publication under a
  content-addressed SHA-256 Bronze key.
- `fact_sec_filing` uses accession number as its primary business key and stores
  the Bronze URI, digest, schema version, run ID, and code version.
- A separate `marketpilot_sec` MariaDB identity has minimal grants.
- `sec_polling` runs at most once concurrently, has `catchup=False`, and uses the
  single-slot `sec_api_pool`.

## Runtime evidence

### Alpaca

- A read-only IEX request returned the latest AAPL bar successfully.
- The long-running websocket authenticated, connected, and subscribed to all 11
  configured symbols.
- Because activation occurred after the regular session, a bounded smoke check
  normalized the latest external bars and published the 10 regular-session bars.
- MinIO contained 10 `source=alpaca/event=market_bar_1m` Bronze objects with zero
  quarantined records. SPY's latest bar was timestamped 20:00 UTC and was correctly
  excluded as outside the XNYS regular-session minute range.
- The historical smoke bars were older than the existing streaming watermark,
  which had already advanced on synthetic events, so Spark correctly did not add
  them to live Gold. The first new websocket bars in the next regular session are
  the remaining live Gold verification point.
- Spark Streaming was recreated independently, resumed from its durable checkpoint,
  and loaded code version `ba4cdae` for subsequent lineage.

### SEC fixture

A temporary HTTP container served the checked-in Apple submissions fixture. Two
bounded poll runs produced this result:

| Check | Result |
|---|---:|
| qualifying filings discovered per run | 2 |
| first-run inserts | 2 |
| second-run inserts | 0 |
| second-run idempotent updates | 2 |
| total filing rows | 2 |
| distinct accession numbers | 2 |
| distinct raw Bronze objects | 1 |

The stored accessions were one 10-Q and one 8-K. The watermark
`sec-filings-poll/latest` was `PUBLISHED`. The raw object existed at the expected
`source=sec/event=submissions/.../sha256=...json` key.

An Airflow `dags test` with `force=true` and the same local fixture completed both
`polling_enabled_and_in_window` and `poll_sec_submissions` successfully. Live SEC
polling remained disabled afterward, and the temporary HTTP container was removed.

## Safety and restart behavior

- SEC retries do not duplicate raw objects or accession rows.
- A failed raw upload prevents the MariaDB publication boundary from running.
- The producer reconnect loop reuses deterministic event IDs, while downstream
  Kafka and MariaDB business keys preserve idempotency.
- Secrets are read only from the ignored `.env`; tracked configuration contains
  placeholders.
- Alpaca activation followed the reviewed steps in
  `docs/runbooks/external-source-activation.md`; SEC activation remains gated on a
  real monitored contact identity.

## Quality gates

- `ruff format --check .`: 84 files formatted.
- `ruff check .`: passed.
- `pytest -q`: 39 passed, 4 opt-in Docker tests skipped.
- `scripts/validate_repository.py`: passed.
- `docker compose config --quiet`: passed.
- Airflow DAG import errors: none.
- All 15 long-running local containers reported healthy.

Docker-backed external-boundary verification is opt-in because it creates a
temporary local fixture container and writes test records to the local development
stores. The equivalent SEC boundary and Airflow DAG checks were executed directly
during this verification.
