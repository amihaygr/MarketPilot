# Lightweight Threat Model

| Asset | Threat | Control |
|---|---|---|
| API credentials | Commit or log leakage | `.env` exclusion, secret scanning, log redaction |
| Kafka events | Tampering or malformed payload | Versioned validation, quarantine, internal network |
| Gold database | Over-privileged access | Separate app and ingest users, least privilege grants |
| Object storage | Destructive overwrite | Immutable Bronze convention, versioning in cloud target |
| Archive evidence | Partial or tampered export | Staging, per-object SHA-256, inventory checksum, dual manifest |
| Recovery | Accidental live-database overwrite | Isolated schema and strict restore-target allowlist |
| Alerting | Credential disclosure or alert flood | Optional secret webhook, transition deduplication, redacted logs |
| Airflow | Remote command abuse | No Docker socket, bounded allow-listed applications |
| Web client | Direct data-store access | Backend-only access boundary |
| Serving query | Unbounded scan or injection | Parameterized SQL, fixed filters, bounded ranges and pagination |
| Browser content | Script or framing injection | Same-origin API proxy, restrictive CSP and response hardening headers |
| Supply chain | Compromised container or dependency | Pinned versions, CI scanning, controlled update cadence |

The local MVP uses plaintext internal Docker networking. TLS, secret management, authenticated Kafka and object-storage policies are required before any shared or internet-reachable deployment.
