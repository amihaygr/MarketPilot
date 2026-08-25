"""Stage and atomically publish one validated Silver partition as Gold CERTIFIED."""

import argparse
import json
import logging
import os
from datetime import date
from functools import partial
from uuid import UUID

from pyspark.sql.functions import lit

from marketpilot.batch.mariadb import (
    assert_quality_gate_validated,
    clear_staging_run,
    publish_certified_partition,
    publisher_config_from_env,
    stage_market_bar_partition,
)
from marketpilot.batch.quality import QUALITY_CHECK_NAMES
from marketpilot.batch.spark_support import build_batch_spark_session

logger = logging.getLogger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--logical-date", required=True)
    parser.add_argument("--run-id", required=True)
    args = parser.parse_args()
    logical_date = date.fromisoformat(args.logical_date)
    UUID(args.run_id)

    logging.basicConfig(level=logging.INFO, format="%(message)s")
    spark = build_batch_spark_session("marketpilot-silver-to-gold")
    spark.sparkContext.setLogLevel(os.environ.get("SPARK_LOG_LEVEL", "WARN"))
    source = (
        f"{os.environ['SILVER_URI']}/dataset=market_bars_1m/"
        f"year={logical_date:%Y}/month={logical_date:%m}/day={logical_date:%d}"
    )
    database = publisher_config_from_env()
    try:
        assert_quality_gate_validated(
            database,
            args.run_id,
            logical_date,
            QUALITY_CHECK_NAMES,
        )
        frame = (
            spark.read.parquet(source)
            .withColumn("pipeline_run_id", lit(args.run_id))
            .withColumn("logical_date", lit(logical_date.isoformat()))
            .withColumn(
                "code_version",
                lit(os.environ.get("MARKETPILOT_CODE_VERSION", "development")),
            )
            .withColumn("data_version", lit("market-bars-certified-v1"))
        )
        clear_staging_run(database, args.run_id)
        frame.foreachPartition(partial(stage_market_bar_partition, config=database))
        summary = publish_certified_partition(
            database,
            args.run_id,
            logical_date,
            QUALITY_CHECK_NAMES,
        )
        logger.info(
            json.dumps(
                {
                    "event": "certified_partition_published",
                    "logical_date": logical_date.isoformat(),
                    "run_id": args.run_id,
                    "staged_rows": summary.staged_rows,
                    "previous_partition_rows": summary.previous_partition_rows,
                    "matched_business_keys": summary.matched_business_keys,
                    "changed_business_keys": summary.changed_business_keys,
                },
                separators=(",", ":"),
            )
        )
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
