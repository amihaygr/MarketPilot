# ADR-006: Optional Local Elastic Observability Profile

- Status: Proposed
- Date: 2026-08-29

## Context

MarketPilot already emits structured application logs and has a lightweight
operational monitor. Centralized search and visualization would improve failure
analysis, but the local Compose stack is resource-heavy and Elasticsearch plus
Kibana must not destabilize the data paths.

## Proposed decision

- Phase 13 may add a self-managed Elasticsearch and Kibana deployment under an
  explicit Compose profile named `observability`.
- The profile is disabled by default and is not a dependency of ingestion,
  streaming, batch, storage, orchestration, API, or Web App services.
- Elasticsearch stores operational logs only. It is not a system of record for
  market bars, filings, indicators, signals, or backtests.
- Log collection must not mount the Docker socket into Airflow.
- The implementation must define retention, index lifecycle, authentication,
  healthchecks, memory limits, and a resource budget before acceptance.
- Existing structured JSON logging and the operational monitor remain valid when
  the profile is disabled.

## Decision gate

This ADR remains `Proposed` until the certified historical path is complete and an empirical Docker
resource check confirms that the optional profile can run without destabilizing
the core platform.
