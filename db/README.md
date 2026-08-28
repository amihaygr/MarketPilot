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

Phase 7 adds `marketpilot_app` through the idempotent `008_app_grants.sh`
migration. It can `SELECT` only the four Gold tables required by the serving API
and has no mutation, grant, object-storage, staging, DQ, or archive privileges.

Phase 8 extends `archive_manifest`, adds `archive_restore_result`, and creates the
isolated `marketpilot_restore.restore_market_bar_1m` target. The publisher identity
can register archive and restore evidence but cannot purge Gold history. Full dump
restore scripts accept only isolated database names matching their strict allowlist.
