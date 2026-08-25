# Database

Place versioned MariaDB migrations and safe seed data here.

Initial planned objects are documented in `docs/architecture/architecture.md`.

Requirements:

- explicit primary and unique keys;
- idempotent migrations where practical;
- separate API, streaming-ingestion, and certified-publisher identities;
- indexes driven by verified query patterns;
- no real data dumps in Git.

Phase 4 uses `stg_market_bar_1m` as a transient run-scoped boundary. The publisher
identity can mutate only the Gold publication tables, staging, DQ results, and
watermarks. A validated watermark is checked before staging and locked/rechecked
inside the certified publication transaction.

Phase 6 adds `fact_sec_filing`, keyed by SEC accession number. It retains the
Bronze object URI and SHA-256 digest together with run, code, and schema lineage.
The separate `marketpilot_sec` identity has only the read/write grants required to
resolve symbols, upsert filings, and publish its watermark.
