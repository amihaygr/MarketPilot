"""Compact closed Silver date partitions with validation and recoverable replacement."""

from __future__ import annotations

import argparse
import json
import logging
import os
from datetime import date, datetime, timezone

from pyspark.sql import DataFrame
from pyspark.sql.functions import col, count, countDistinct, expr, lit, pmod, struct, xxhash64
from pyspark.sql.functions import sum as sum_

from marketpilot.batch.spark_support import build_batch_spark_session
from marketpilot.operations.compaction import DatasetMetrics, compaction_dates, validate_compaction
from marketpilot.operations.object_store import (
    copy_key,
    copy_prefix,
    delete_keys,
    delete_prefix,
    list_objects,
    object_store_client,
    parse_s3_uri,
    write_json,
)

logger = logging.getLogger(__name__)
DATASET_PREFIX = "dataset=market_bars_1m"
SPARK_UTC = timezone.utc  # noqa: UP017 -- Spark 3.5.8 image uses Python 3.10.


def measure(frame: DataFrame) -> DatasetMetrics:
    columns = sorted(frame.columns)
    hashed = frame.withColumn("_operation_row_hash", xxhash64(*[col(name) for name in columns]))
    aggregate = hashed.agg(
        count("*").alias("row_count"),
        countDistinct(struct("symbol", "event_time_utc", "interval")).alias(
            "distinct_business_keys"
        ),
        expr("bit_xor(_operation_row_hash)").alias("logical_hash_xor"),
        sum_(pmod(col("_operation_row_hash"), lit(1_000_000_007))).alias("logical_hash_sum"),
    ).first()
    schema_fields = tuple(
        sorted(
            (field.name, field.dataType.simpleString(), bool(field.nullable))
            for field in frame.schema.fields
        )
    )
    return DatasetMetrics(
        row_count=int(aggregate["row_count"]),
        distinct_business_keys=int(aggregate["distinct_business_keys"]),
        logical_hash_xor=int(aggregate["logical_hash_xor"] or 0),
        logical_hash_sum=int(aggregate["logical_hash_sum"] or 0),
        schema_fields=schema_fields,
    )


def compact_partition(spark, logical_date: date, run_id: str) -> dict[str, object]:  # type: ignore[no-untyped-def]
    silver_uri = os.environ["SILVER_URI"].rstrip("/")
    silver = parse_s3_uri(silver_uri)
    archive_bucket = os.environ.get("MINIO_ARCHIVE_BUCKET", "marketpilot-archive")
    canonical_prefix = (
        f"{DATASET_PREFIX}/year={logical_date:%Y}/month={logical_date:%m}/day={logical_date:%d}"
    )
    staging_prefix = (
        f"_operations/compaction/run_id={run_id}/logical_date={logical_date.isoformat()}"
    )
    backup_prefix = (
        f"operations/compaction-backups/{DATASET_PREFIX}/logical_date={logical_date.isoformat()}"
        f"/run_id={run_id}"
    )
    manifest_key = (
        f"operations/compaction-manifests/{DATASET_PREFIX}/logical_date={logical_date.isoformat()}"
        f"/run_id={run_id}.json"
    )
    client = object_store_client()
    source_objects = [
        item
        for item in list_objects(client, silver.bucket, canonical_prefix + "/")
        if str(item["Key"]).endswith(".parquet") or str(item["Key"]).endswith("_SUCCESS")
    ]
    source_files = [item for item in source_objects if str(item["Key"]).endswith(".parquet")]
    if not source_files:
        return {"logical_date": logical_date.isoformat(), "status": "SKIPPED_NO_DATA"}

    source_uri = f"{silver_uri}/{canonical_prefix}"
    staging_uri = f"{silver_uri}/{staging_prefix}"
    source = spark.read.parquet(source_uri).cache()
    before = measure(source)
    if "symbol" not in source.columns:
        raise RuntimeError("Silver partition is missing symbol partition metadata")
    delete_prefix(client, silver.bucket, staging_prefix)
    (
        source.repartition("symbol")
        .write.mode("overwrite")
        .option("compression", "snappy")
        .partitionBy("symbol")
        .parquet(staging_uri)
    )
    source.unpersist()
    staged = spark.read.parquet(staging_uri).cache()
    after_staging = measure(staged)
    staged.unpersist()
    validate_compaction(before, after_staging)

    delete_prefix(client, archive_bucket, backup_prefix)
    for item in source_objects:
        source_key = str(item["Key"])
        relative = source_key.removeprefix(canonical_prefix + "/")
        copy_key(
            client,
            source_bucket=silver.bucket,
            source_key=source_key,
            target_bucket=archive_bucket,
            target_key=f"{backup_prefix}/{relative}",
        )
    backup_count = len(list_objects(client, archive_bucket, backup_prefix + "/"))
    if backup_count != len(source_objects):
        raise RuntimeError("compaction backup object count does not match source")

    source_keys = [str(item["Key"]) for item in source_objects]
    try:
        delete_keys(client, silver.bucket, source_keys)
        copied = copy_prefix(
            client,
            source_bucket=silver.bucket,
            source_prefix=staging_prefix,
            target_bucket=silver.bucket,
            target_prefix=canonical_prefix,
        )
        spark.catalog.clearCache()
        after_live = measure(spark.read.parquet(source_uri))
        validate_compaction(before, after_live)
    except Exception:
        current_keys = [
            str(item["Key"])
            for item in list_objects(client, silver.bucket, canonical_prefix + "/")
            if str(item["Key"]).endswith(".parquet") or str(item["Key"]).endswith("_SUCCESS")
        ]
        delete_keys(client, silver.bucket, current_keys)
        copy_prefix(
            client,
            source_bucket=archive_bucket,
            source_prefix=backup_prefix,
            target_bucket=silver.bucket,
            target_prefix=canonical_prefix,
        )
        spark.catalog.clearCache()
        validate_compaction(before, measure(spark.read.parquet(source_uri)))
        raise
    finally:
        delete_prefix(client, silver.bucket, staging_prefix)

    output_files = sum(key.endswith(".parquet") for key in copied)
    manifest = {
        "manifest_schema_version": 1,
        "dataset_name": "market_bars_1m_silver",
        "logical_date": logical_date.isoformat(),
        "run_id": run_id,
        "input_file_count": len(source_files),
        "output_file_count": output_files,
        "input_metrics": before.to_dict(),
        "output_metrics": after_live.to_dict(),
        "backup_uri": f"s3a://{archive_bucket}/{backup_prefix}",
        "verified_at_utc": datetime.now(SPARK_UTC).isoformat(),
    }
    write_json(client, archive_bucket, manifest_key, manifest)
    return {"logical_date": logical_date.isoformat(), "status": "COMPACTED", **manifest}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--through-date", required=True)
    parser.add_argument("--lookback-days", type=int, default=7)
    parser.add_argument("--run-id", required=True)
    args = parser.parse_args()
    through_date = date.fromisoformat(args.through_date)
    if through_date > datetime.now(SPARK_UTC).date():
        raise ValueError("compaction through-date cannot be in the future")
    dates = compaction_dates(through_date, args.lookback_days, args.run_id)
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    spark = build_batch_spark_session("marketpilot-weekly-silver-compaction")
    spark.sparkContext.setLogLevel(os.environ.get("SPARK_LOG_LEVEL", "WARN"))
    try:
        results = [compact_partition(spark, logical_date, args.run_id) for logical_date in dates]
        logger.info(
            json.dumps(
                {"event": "silver_compaction_completed", "run_id": args.run_id, "results": results},
                separators=(",", ":"),
            )
        )
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
