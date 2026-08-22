# Expert Engineering Review Checklist

## Architecture

- [ ] Long-running service lifecycle is separate from bounded workflow orchestration.
- [ ] Every arrow in the diagrams has an implementation owner and a data contract.
- [ ] Bronze, Silver and Gold responsibilities are non-overlapping.
- [ ] Provisional and certified publication semantics are visible to consumers.
- [ ] Replay, late data and correction behavior are documented.

## Reliability

- [ ] Kafka keys preserve per-symbol ordering requirements.
- [ ] Consumer offsets are committed only after durable Bronze writes.
- [ ] Streaming checkpoints are durable and uniquely owned.
- [ ] Database writes are idempotent by business key.
- [ ] Failed quality gates cannot advance publication watermarks.
- [ ] Recovery runbooks have been exercised, not only written.

## Data quality

- [ ] Required-field, type, uniqueness and OHLC checks exist.
- [ ] Market-session completeness uses an exchange calendar.
- [ ] Source, Bronze, Silver and Gold counts reconcile.
- [ ] Late and quarantined event metrics are retained.
- [ ] Provisional-to-certified differences are measured.

## Security

- [ ] Secrets are injected at runtime and absent from Git history.
- [ ] API, ingestion and orchestration identities use least privilege.
- [ ] The browser cannot reach MariaDB or MinIO directly.
- [ ] Only necessary development ports are exposed.
- [ ] Images are pinned and vulnerability-scanned before release.

## Operability

- [ ] Health checks test readiness rather than process existence alone.
- [ ] Structured logs include run ID, event ID, symbol and partition.
- [ ] Alerts cover freshness, lag, failures, storage and resource saturation.
- [ ] Backup restore and archive restore have evidence.
- [ ] Capacity limits were measured on the target workstation.
