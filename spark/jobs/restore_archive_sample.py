"""Verify an archive and restore a bounded sample into the isolated restore schema."""

from __future__ import annotations

import argparse
import json
import logging
import os
from uuid import UUID

from marketpilot.batch.spark_support import build_batch_spark_session
from marketpilot.operations.archive import ANNUAL_DATASET, VALIDATION_DATASET, ArchiveManifest
from marketpilot.operations.mariadb import OperationsDbConfig, restore_market_bar_sample
from marketpilot.operations.object_store import (
    inventory,
    object_store_client,
    parse_s3_uri,
    read_json,
)

logger = logging.getLogger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dataset-name",
        choices=(ANNUAL_DATASET, VALIDATION_DATASET),
        required=True,
    )
    parser.add_argument("--archive-year", type=int, required=True)
    parser.add_argument("--archive-version", type=int, default=1)
    parser.add_argument("--restore-run-id", required=True)
    parser.add_argument("--sample-size", type=int, default=100)
    args = parser.parse_args()
    UUID(args.restore_run_id)
    if args.sample_size < 1 or args.sample_size > 1_000:
        raise ValueError("restore sample size must be between 1 and 1000")
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    archive_uri = os.environ.get("ARCHIVE_URI", "s3a://marketpilot-archive").rstrip("/")
    archive = parse_s3_uri(archive_uri)
    base_prefix = (
        f"dataset={args.dataset_name}/archive_year={args.archive_year}"
        f"/version={args.archive_version}"
    )
    data_prefix = f"{base_prefix}/data"
    manifest = ArchiveManifest.from_dict(
        read_json(object_store_client(), archive.bucket, f"{base_prefix}/manifest.json")
    )
    manifest.validate_inventory()
    actual_inventory = inventory(object_store_client(), archive.bucket, data_prefix)
    if actual_inventory != manifest.objects:
        raise RuntimeError("archive object checksum verification failed before restore")

    spark = build_batch_spark_session("marketpilot-archive-sample-restore")
    spark.sparkContext.setLogLevel(os.environ.get("SPARK_LOG_LEVEL", "WARN"))
    try:
        frame = spark.read.parquet(f"{archive_uri}/{data_prefix}").cache()
        if frame.count() != manifest.row_count:
            raise RuntimeError("archive row count verification failed before restore")
        rows = frame.orderBy("symbol", "event_time_utc").limit(args.sample_size).collect()
        sample = [row.asDict(recursive=True) for row in rows]
        restored = restore_market_bar_sample(
            OperationsDbConfig.from_env(),
            restore_run_id=args.restore_run_id,
            dataset_name=manifest.dataset_name,
            archive_year=manifest.archive_year,
            archive_version=manifest.archive_version,
            rows=sample,
        )
        logger.info(
            json.dumps(
                {
                    "event": "archive_sample_restore_verified",
                    "restore_run_id": args.restore_run_id,
                    "dataset_name": manifest.dataset_name,
                    "archive_year": manifest.archive_year,
                    "archive_version": manifest.archive_version,
                    "archive_rows": manifest.row_count,
                    "restored_sample_rows": restored,
                },
                separators=(",", ":"),
            )
        )
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
