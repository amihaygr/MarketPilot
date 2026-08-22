# Streaming Recovery Runbook

## Detection

- Alert on source-to-Gold freshness, consumer lag, restart count and checkpoint age.
- Confirm whether the failure is source, Kafka, Spark, checkpoint or MariaDB related.

## Safe response

1. Freeze configuration changes and record the incident start time.
2. Inspect `spark-streaming`, Kafka and MariaDB health and logs.
3. Verify that the checkpoint path exists and is not concurrently used by another query identity.
4. Restore the failed dependency before restarting the consumer.
5. Restart only the streaming service.
6. Confirm offset progress and idempotent Gold writes.
7. Run the bounded backfill DAG for any proven gap.
8. Allow the next daily certification DAG to replace provisional results.

## Prohibited shortcuts

- Do not delete a checkpoint without a reviewed replay plan.
- Do not reset Kafka offsets without recording the old and new positions.
- Do not mark a partition certified from the streaming path.
- Do not purge Bronze objects while investigating.
