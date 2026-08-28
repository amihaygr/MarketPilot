# Archive and Recovery Runbook

## Safety rules

- Annual production archives cover only a closed calendar year.
- A current-year export is allowed only as an explicitly named validation snapshot.
- Archive publication is complete only after Parquet objects, checksums, row counts,
  time bounds, and the MariaDB manifest agree.
- Compaction backs up the original Silver objects before replacement and restores
  them if validation fails.
- MariaDB history is never purged automatically.
- Restore drills use an isolated schema; never target the live `marketpilot` schema.

## Weekly Silver compaction

Airflow schedules `weekly_compaction` at 06:00 Saturday in
`America/New_York`. It submits the bounded Spark application and does not control
any long-running service.

Manual example:

```powershell
$runId = [guid]::NewGuid().ToString()
docker compose run --rm --no-deps spark-batch /opt/spark/bin/spark-submit `
  --master spark://spark-master:7077 `
  /opt/marketpilot/spark/jobs/compact_silver.py `
  --start-date 2026-08-25 --end-date 2026-08-25 --run-id $runId
```

Success requires equal input/output row counts, distinct business-key counts,
logical row hashes, and compatible schemas. Inspect the JSON manifest under
`marketpilot-archive/compaction/` before treating the run as verified.

## Annual archive

The `annual_archive` DAG runs on January 10 and exports the previous year. Its
Spark job writes a versioned Parquet archive, hashes every object, validates the
full row count and event-time bounds, and then registers the same manifest in
MinIO and MariaDB.

Do not use the validation-snapshot option as a substitute for the annual archive.
It exists only to test the complete mechanism before the first closed year exists.

## Sample restore

Select a verified manifest and restore a small sample into the isolated
`marketpilot_restore.restore_market_bar_1m` table:

```powershell
docker compose run --rm --no-deps spark-batch /opt/spark/bin/spark-submit `
  --master spark://spark-master:7077 `
  /opt/marketpilot/spark/jobs/restore_archive_sample.py `
  --dataset fact_market_bar_1m_validation_snapshot `
  --year 2026 --version 1 --sample-size 25
```

The job re-hashes every archive object before reading it. Confirm a `PASS` row in
`marketpilot.archive_restore_result` and verify that the live Gold row count did
not change.

## Full MariaDB backup and isolated restore

Create a compressed backup and upload it with a SHA-256 sidecar:

```powershell
.\scripts\backup_mariadb.ps1
```

Restore only to an allowed isolated database name:

```powershell
.\scripts\restore_mariadb_backup.ps1 `
  -BackupPath .\tmp\backups\marketpilot-YYYYMMDDTHHMMSSZ.sql.gz `
  -TargetDatabase marketpilot_restore_drill
```

The restore script rejects live or unexpected target names and verifies the
checksum before recreating the isolated target.

## Failure response

1. Record the run ID and preserve the logs.
2. Do not delete staging, backup, or manifest objects until the cause is known.
3. Confirm that no verified manifest was registered for a partial archive.
4. For compaction, verify that the original Silver partition was restored.
5. Correct the cause and rerun with a new run ID; archive versions remain
   immutable and must not be overwritten silently.
6. Escalate any request to purge Gold history into a separate retention decision
   with a completed restore test.
