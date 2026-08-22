# ADR-003: Automatic Streaming Lifecycle

- Status: Accepted
- Date: 2026-08-22

## Context

The live market path must start automatically, remain active, recover after failure, and avoid duplicate business rows.

## Decision

- Docker Compose starts Spark Structured Streaming after its readiness-sensitive dependencies become healthy.
- The streaming container uses an appropriate restart policy.
- Spark uses a durable checkpoint.
- Kafka consumer offsets and Spark checkpoint state provide processing continuity.
- MariaDB writes are idempotent upserts.
- The market-bar unique key is based on symbol, event timestamp, and interval.
- Malformed events are quarantined or sent to a dead-letter topic.
- The service may remain active outside market hours and wait for events.
- The producer owns source connection logic and exchange-session awareness.

## Consequences

### Positive

- Streaming does not depend on Airflow availability.
- Container restart can recover from application failure.
- Checkpoint recovery avoids restarting from the beginning.
- Upserts protect the business layer from duplicate delivery.

### Negative

- Checkpoint storage becomes critical state.
- Incorrect checkpoint deletion can cause replay or data loss.
- Exactly-once behavior across Kafka, Spark, and MariaDB is not assumed. Business-level idempotency is mandatory.

## Operational verification

The project must test:

1. normal event processing;
2. duplicate delivery;
3. streaming restart;
4. Kafka temporary unavailability;
5. MariaDB temporary unavailability;
6. malformed event handling;
7. checkpoint preservation.
