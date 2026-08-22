# ADR-004: Provisional and Certified Gold Publication

- Status: Accepted
- Date: 2026-08-22

## Context

The application needs recent data before the full trading session can be reconstructed and validated. Streaming and batch can produce different results when late or corrected events arrive.

## Decision

Streaming writes idempotent Gold records marked `PROVISIONAL`. The post-market batch pipeline rebuilds the complete partition from Bronze and publishes it as `CERTIFIED` only after blocking quality checks pass. Publication state is tracked separately from row ingestion.

## Consequences

- The API must expose or apply a clear certification policy.
- Batch is authoritative for closed sessions.
- A failed batch never hides the last known certified partition.
- Reconciliation metrics between provisional and certified values are required.
