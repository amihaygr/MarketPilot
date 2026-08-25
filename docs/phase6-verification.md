# Phase 6 External Sources Verification

Verified locally on 2026-08-26 with Docker Compose, the official Alpaca Python
SDK 0.44.0, a deterministic local SEC fixture, Airflow 3.0.3, MinIO, and MariaDB.
No request was sent to Alpaca or `sec.gov` during verification.

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
  default.
- The adapter subscribes to bars through the official SDK and converts them to the
  existing schema-versioned `MarketBarV1` contract.
- Event IDs are deterministic across reconnects for the same feed, symbol,
  interval, and market minute.
- Only regular XNYS session minutes are published.
- Disconnects use capped exponential backoff, and SIGTERM/SIGINT trigger a
  graceful stream stop and Kafka flush.
- The rebuilt producer image imports Alpaca SDK 0.44.0 successfully. Contract,
  calendar, conversion, and retry behavior are covered by unit tests.

A real websocket session was deliberately not opened because Alpaca credentials
are local operator secrets and were not supplied.

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
`external_source_gate` and `poll_sec_submissions` successfully. All production
source settings remained disabled afterward, and the temporary HTTP container was
removed.

## Safety and restart behavior

- SEC retries do not duplicate raw objects or accession rows.
- A failed raw upload prevents the MariaDB publication boundary from running.
- The producer reconnect loop reuses deterministic event IDs, while downstream
  Kafka and MariaDB business keys preserve idempotency.
- Secrets are read only from the ignored `.env`; tracked configuration contains
  placeholders.
- External activation is a separate reviewed step documented in
  `docs/runbooks/external-source-activation.md`.

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
