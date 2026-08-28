# Phase 8 Verification

Verified locally on 2026-08-28 against the running Docker Compose platform.

## Delivered controls

- Weekly bounded Silver compaction submitted by Airflow.
- Annual closed-year MariaDB-to-Parquet archive with per-object SHA-256 hashes.
- Matching manifests in MinIO and MariaDB.
- Isolated sample restore with a persisted PASS/FAIL result.
- Compressed MariaDB backup, checksum sidecar, MinIO upload, and isolated restore.
- Docker-owned operational monitor for API, Kafka, MinIO, MariaDB, market
  freshness, and SEC freshness.
- Recovery procedures that explicitly prohibit automatic Gold-history purge.

## Runtime evidence

### Silver compaction

Run `fdb82a3d-60fc-422d-b5da-868044086e89` compacted the 2026-08-25 partition.
Input and output both contained 1,936 rows, 1,936 distinct business keys, the same
schema, logical XOR hash `-1189678442897487788`, and logical sum hash
`953792387827`. The existing 11 files were backed up before replacement. This
partition was already well-sized, so the validated output also contained 11 files.

### Archive and restore

Because 2026 is not a closed year, the runtime drill used the explicitly separate
`fact_market_bar_1m_validation_snapshot` dataset. Run
`41bb255d-0b34-433b-a3b7-d3de95f7db05` exported 5,106 rows to 11 Parquet objects.
The combined inventory checksum was
`85f089d57d2554a5db79c96898b77f4f43ec7f938e74fe85001262a03fc2f700`.
Its event-time range was 2026-08-22 14:40 UTC through 2026-08-28 14:38 UTC, and
the manifest records `period_closed=false`.

Restore run `996c5da0-e0fb-405d-bffe-4c78d98cb9b2` re-hashed all 11 objects,
confirmed all 5,106 archive rows, restored 25 rows into the isolated restore
schema, and persisted `PASS`. The live Gold schema was not changed.

### Full database recovery drill

A compressed backup containing 5,126 market bars and 932 SEC filings was created,
hashed as `eca9abcc8a233f64c48f405e6994e858d6c823e2ecc823ba1b2c671c3f320f25`,
uploaded under the archive bucket, and restored into
`marketpilot_restore_drill`. The restored counts matched the backup-time counts;
the live database remained online and untouched.

### Monitoring and orchestration

All 18 Compose services were healthy, including `operational-monitor`. Its first
full probe reached the API, all three Kafka topics, all three MinIO data buckets,
MariaDB, and both freshness checks. The two Phase 8 DAGs imported without errors,
use `max_active_runs=1`, and remain paused by default for operator-controlled
activation.

## Failure and restart behavior

Pre-publication drills exposed and safely rejected three issues: Python runtime
compatibility, JDBC dialect selection, and Parquet nullability metadata. None
registered a verified manifest or modified Gold history. The corrected jobs then
completed successfully. Compaction replacement includes automatic restoration
from its run-specific backup when validation or replacement fails.

## Boundary confirmation

- Compose continues to own every long-running service.
- Airflow submits only bounded Spark jobs.
- The application still reads only through the Backend API.
- No secrets, database dumps, or personal data were added to Git.
- No MariaDB history was deleted.
