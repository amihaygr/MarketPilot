# Phase 4 Verification

- Verification date: 2026-08-25
- Runtime: Spark 3.5.8 standalone, Hadoop S3A 3.3.4, MinIO, MariaDB 11.4
- Source partition: synthetic `2026-08-22`
- Successful run ID: `0222c48c-0a3e-44f0-bb60-399d8b8f106a`
- Deliberately failed run ID: `88f1d3b7-3d7f-4a13-90bb-9528e1a6aa04`

## Acceptance evidence

| Criterion | Evidence |
|---|---|
| Explicit Bronze to Silver to Gold path | Three finite Spark applications completed against the standalone cluster |
| Queryable, schema-versioned Silver | The DQ job read the Parquet partition and passed event and dataset schema checks |
| Partitioned Parquet | 11 Snappy Parquet objects, exactly one per configured symbol |
| Idempotent reprocessing | First and second runs both produced 1,881 rows; second reconciliation matched 1,881 keys and changed zero |
| Blocking quality gate | Expected 172 bars with 171 observed failed and both jobs exited non-zero |
| Prior certified data survives a failure | Gold remained at 1,881 certified rows after the failed run |
| Atomic staging boundary | Failed run left zero staging rows and no publication watermark |
| Provisional/certified reconciliation | Reconciliation result records matched, staged, and changed business-key counts |
| Exchange-calendar awareness | XNYS regular, early-close, and weekend behavior is covered by unit tests |

## Successful partition

Bronze contained 1,881 immutable JSON objects: 171 bars for each of 11 symbols.
Bronze-to-Silver wrote 1,881 canonical rows. All ten blocking checks passed:

- non-empty partition;
- exact configured symbol set;
- expected bars per symbol;
- required fields;
- business-key duplicates;
- OHLC consistency;
- logical date;
- event and dataset schema versions;
- source-to-ingestion freshness;
- event timestamp not later than ingestion.

Gold then contained 1,881 `CERTIFIED` rows and 1,881 distinct business keys. The
successful `market-bars-certified-publication` watermark is `PUBLISHED`.

## Idempotency and failure semantics

Re-running all three jobs with the same partition and run ID overwrote only that
Silver partition, upserted DQ results, restaged deterministically, and atomically
republished the same 1,881 keys. No values changed.

The negative test increased expected bars from 171 to 172. The quality job persisted
`expected_market_bars=FAIL` and exited non-zero. The publisher rejected the failed
watermark before staging. The earlier certified partition and its publication
watermark remained unchanged. The successful DQ run was then replayed so the final
operational DQ watermark is `VALIDATED`.

The synthetic verification date is a Saturday because Phase 2 intentionally emits
without market-session awareness. The test therefore used an explicit expected-bar
override. Without that override, the job uses the XNYS calendar and rejects the date
as a non-session. Live scheduling and source session controls remain Phase 5 and
Phase 6 responsibilities.
