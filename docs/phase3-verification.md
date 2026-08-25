# Phase 3 Verification

- Verification date: 2026-08-25
- Environment: Windows, Docker Desktop, Spark 3.5.8, MariaDB 11.4, Kafka 3.9.0
- Data source: deterministic synthetic one-minute bars for 11 configured symbols

## Acceptance evidence

| Criterion | Result |
|---|---|
| Synthetic event reaches `fact_market_bar_1m` | Passed; first micro-batch inserted 11 rows |
| Business key prevents duplicates | Passed; duplicate AAPL delivery retained one row |
| Streaming resumes from checkpoint | Passed; Gold offset files advanced from batch 3 to batch 5 after restart |
| Malformed event does not terminate query | Passed; event reached DLQ with `missing_required_field` |
| p95 source-to-Gold latency | 19.311 seconds for the measured synthetic sample |
| Provisional publication policy | Passed; all streaming rows were `PROVISIONAL` |
| Lineage | Passed; source event, Kafka position, run, code, data, and schema versions persisted |

## Recovery observations

Before restart, Gold contained 33 rows and 33 distinct business keys. After restarting
only `spark-streaming`, the application became healthy, resumed from the named-volume
checkpoint, advanced its Kafka position, and Gold contained 55 rows and 55 distinct
business keys.

The measured latency is bounded primarily by the configured 60-second processing
trigger and the producer schedule. It is evidence for the local synthetic run, not a
production service-level objective.

## Checkpoint storage correction

The first recovery pass showed that a local stateful operator also writes state-store
files from the executor. Mounting the checkpoint volume only on the driver was not
sufficient when the Worker container was recreated. The final Compose configuration
mounts the same named volume on both `spark-streaming` and `spark-worker`. The original
`market-bars-v1` checkpoint was preserved for diagnosis, and verification continued
with the new `market-bars-v2` checkpoint rather than deleting state.

The final recovery test force-recreated the Worker and then the streaming driver.
Both services returned to `healthy`, the query resumed at batches 2 through 4 without
a missing-state error, and the same state files were visible from both containers.
Gold then contained 154 rows and 154 distinct business keys, with Kafka offset 1241
as the highest persisted source position.

The automated opt-in restart test passed afterward. The next committed micro-batch
advanced Gold to 198 rows and 198 distinct business keys, with Kafka offset 1265,
confirming that processing continued from the recovered checkpoint.
