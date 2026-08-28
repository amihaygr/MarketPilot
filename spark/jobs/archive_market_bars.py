"""Export one versioned market-bar year to verified Parquet and register its manifest."""

from __future__ import annotations

import argparse
import json
import logging
import os
from datetime import datetime, timezone

from pyspark.sql.functions import lit
from pyspark.sql.functions import max as max_
from pyspark.sql.functions import min as min_

from marketpilot.batch.spark_support import build_batch_spark_session
from marketpilot.operations.archive import (
    ARCHIVE_SCHEMA_VERSION,
    ArchiveManifest,
    resolve_archive_scope,
    spark_mariadb_jdbc_url,
)
from marketpilot.operations.mariadb import (
    OperationsDbConfig,
    archive_manifest_exists,
    register_archive_manifest,
)
from marketpilot.operations.object_store import (
    copy_prefix,
    delete_prefix,
    inventory,
    inventory_checksum,
    list_objects,
    object_store_client,
    parse_s3_uri,
    read_json,
    write_json,
)

logger = logging.getLogger(__name__)
SPARK_UTC = timezone.utc  # noqa: UP017 -- Spark 3.5.8 image uses Python 3.10.


def _schema_signature(frame) -> tuple[tuple[str, str], ...]:  # type: ignore[no-untyped-def]
    return tuple(
        sorted((field.name, field.dataType.simpleString()) for field in frame.schema.fields)
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive-year", type=int, required=True)
    parser.add_argument("--archive-version", type=int, default=1)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--validation-snapshot", action="store_true")
    args = parser.parse_args()
    scope = resolve_archive_scope(
        archive_year=args.archive_year,
        archive_version=args.archive_version,
        run_id=args.run_id,
        validation_snapshot=args.validation_snapshot,
    )
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    archive_uri = os.environ.get("ARCHIVE_URI", "s3a://marketpilot-archive").rstrip("/")
    archive = parse_s3_uri(archive_uri)
    base_prefix = (
        f"dataset={scope.dataset_name}/archive_year={scope.archive_year}"
        f"/version={scope.archive_version}"
    )
    data_prefix = f"{base_prefix}/data"
    manifest_key = f"{base_prefix}/manifest.json"
    manifest_uri = f"{archive_uri}/{manifest_key}"
    object_uri = f"{archive_uri}/{data_prefix}"
    client = object_store_client()
    database = OperationsDbConfig.from_env()

    existing = list_objects(client, archive.bucket, manifest_key)
    if existing:
        manifest = ArchiveManifest.from_dict(read_json(client, archive.bucket, manifest_key))
        actual_inventory = inventory(client, archive.bucket, data_prefix)
        manifest.validate_inventory()
        if actual_inventory != manifest.objects:
            raise RuntimeError("registered archive inventory differs from stored objects")
        if not archive_manifest_exists(
            database,
            manifest.dataset_name,
            manifest.archive_year,
            manifest.archive_version,
        ):
            register_archive_manifest(database, manifest)
        logger.info(
            json.dumps(
                {"event": "annual_archive_already_verified", "manifest": manifest.to_dict()},
                separators=(",", ":"),
            )
        )
        return

    start = f"{scope.archive_year:04d}-01-01 00:00:00"
    end = f"{scope.archive_year + 1:04d}-01-01 00:00:00"
    query = f"""(
        SELECT d.symbol, f.event_time_utc, f.bar_interval,
               f.open_price, f.high_price, f.low_price, f.close_price, f.volume,
               f.certification_status, f.source_event_id, f.source_name,
               f.ingested_at_utc, f.pipeline_run_id, f.code_version,
               f.data_version, f.schema_version
        FROM fact_market_bar_1m f
        JOIN dim_symbol d ON d.symbol_id = f.symbol_id
        WHERE f.event_time_utc >= '{start}' AND f.event_time_utc < '{end}'
    ) archive_source"""
    spark = build_batch_spark_session("marketpilot-annual-market-bar-archive")
    spark.sparkContext.setLogLevel(os.environ.get("SPARK_LOG_LEVEL", "WARN"))
    staging_prefix = f"_staging/archive/run_id={scope.run_id}"
    staging_uri = f"{archive_uri}/{staging_prefix}"
    try:
        frame = (
            spark.read.format("jdbc")
            .option("url", spark_mariadb_jdbc_url(os.environ["MARIADB_JDBC_URL"]))
            .option("dbtable", query)
            .option("user", os.environ["MARIADB_PUBLISH_USER"])
            .option("password", os.environ["MARIADB_PUBLISH_PASSWORD"])
            .option("driver", "org.mariadb.jdbc.Driver")
            .option("fetchsize", "1000")
            .load()
            .withColumn("archive_schema_version", lit(ARCHIVE_SCHEMA_VERSION))
            .withColumn("archive_run_id", lit(scope.run_id))
            .withColumn(
                "archive_code_version",
                lit(os.environ.get("MARKETPILOT_CODE_VERSION", "development")),
            )
            .cache()
        )
        row_count = frame.count()
        if row_count < 1:
            raise RuntimeError("annual archive source contains no rows")
        bounds = frame.agg(
            min_("event_time_utc").alias("minimum"), max_("event_time_utc").alias("maximum")
        ).first()
        source_schema = _schema_signature(frame)
        delete_prefix(client, archive.bucket, staging_prefix)
        (
            frame.repartition("symbol")
            .write.mode("overwrite")
            .option("compression", "snappy")
            .partitionBy("symbol")
            .parquet(staging_uri)
        )
        frame.unpersist()
        staged = spark.read.parquet(staging_uri)
        if staged.count() != row_count or _schema_signature(staged) != source_schema:
            raise RuntimeError("archive staging validation changed row count or schema")

        delete_prefix(client, archive.bucket, data_prefix)
        copy_prefix(
            client,
            source_bucket=archive.bucket,
            source_prefix=staging_prefix,
            target_bucket=archive.bucket,
            target_prefix=data_prefix,
        )
        final_frame = spark.read.parquet(object_uri)
        if final_frame.count() != row_count or _schema_signature(final_frame) != source_schema:
            raise RuntimeError("final archive validation changed row count or schema")
        objects = inventory(client, archive.bucket, data_prefix)
        verified_at = datetime.now(SPARK_UTC).isoformat()
        manifest = ArchiveManifest(
            dataset_name=scope.dataset_name,
            archive_year=scope.archive_year,
            archive_version=scope.archive_version,
            run_id=scope.run_id,
            object_uri=object_uri,
            manifest_uri=manifest_uri,
            row_count=row_count,
            object_count=len(objects),
            checksum_sha256=inventory_checksum(objects),
            schema_version=ARCHIVE_SCHEMA_VERSION,
            code_version=os.environ.get("MARKETPILOT_CODE_VERSION", "development"),
            min_event_time_utc=bounds["minimum"].replace(tzinfo=SPARK_UTC).isoformat(),
            max_event_time_utc=bounds["maximum"].replace(tzinfo=SPARK_UTC).isoformat(),
            period_closed=scope.period_closed,
            verified_at_utc=verified_at,
            objects=objects,
        )
        manifest.validate_inventory()
        write_json(client, archive.bucket, manifest_key, manifest.to_dict())
        register_archive_manifest(database, manifest)
        logger.info(
            json.dumps(
                {"event": "annual_archive_verified", "manifest": manifest.to_dict()},
                separators=(",", ":"),
            )
        )
    finally:
        delete_prefix(client, archive.bucket, staging_prefix)
        spark.stop()


if __name__ == "__main__":
    main()
