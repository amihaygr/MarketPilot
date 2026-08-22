# ADR-001: MariaDB and Object Storage Responsibilities

- Status: Accepted
- Date: 2026-08-22

## Context

The application needs SQL access to both near-real-time and historical modeled data. The platform also needs immutable raw history, replay, Parquet analytics, and long-term archive.

Storing every raw payload and archive copy in MariaDB would simplify the number of technologies but would weaken replay, compression, partitioned analytics, and long-term storage efficiency.

## Decision

- MariaDB is the Gold serving database.
- MariaDB stores near-real-time modeled data and active historical data required by the application.
- MinIO stores immutable Bronze data and Silver Parquet data.
- S3 is the future cloud replacement for MinIO.
- Annual archive exports closed MariaDB periods to Parquet and records a verified manifest.
- The MVP does not automatically purge MariaDB after archive export.

## Consequences

### Positive

- The API has a predictable SQL serving layer.
- Raw data remains replayable.
- Parquet enables compression and analytical scans.
- Cloud migration can replace MinIO with S3 without changing the logical architecture.

### Negative

- Two storage systems must be operated.
- Data lineage and reconciliation are required between object storage and MariaDB.
- Archive restore must be tested.

## Rejected alternative

Store all raw, modeled, and archived data only in MariaDB.

This was rejected because it couples replay and archive to the serving database and creates unnecessary operational and storage pressure as the project grows.
