"""Normalize one immutable Bronze date partition into canonical Silver Parquet."""

import argparse
import json
import logging
import os
from datetime import date
from uuid import UUID

from pyspark.sql import DataFrame
from pyspark.sql.functions import (
    col,
    from_json,
    lit,
    regexp_extract,
    row_number,
    to_date,
    when,
)
from pyspark.sql.types import (
    DecimalType,
    LongType,
    StringType,
    StructField,
    StructType,
    TimestampType,
)
from pyspark.sql.window import Window

from marketpilot.batch.spark_support import build_batch_spark_session

logger = logging.getLogger(__name__)

MARKET_BAR_SCHEMA = StructType(
    [
        StructField("event_id", StringType(), True),
        StructField("symbol", StringType(), True),
        StructField("event_time_utc", TimestampType(), True),
        StructField("interval", StringType(), True),
        StructField("open", DecimalType(19, 6), True),
        StructField("high", DecimalType(19, 6), True),
        StructField("low", DecimalType(19, 6), True),
        StructField("close", DecimalType(19, 6), True),
        StructField("volume", LongType(), True),
        StructField("source", StringType(), True),
        StructField("schema_version", LongType(), True),
        StructField("ingested_at_utc", TimestampType(), True),
    ]
)


def classify_bronze(frame: DataFrame, logical_date: date) -> DataFrame:
    parsed = frame.select(
        col("path").alias("source_file"),
        col("content").cast("string").alias("raw_value"),
        from_json(col("content").cast("string"), MARKET_BAR_SCHEMA).alias("bar"),
    )
    required_fields = [field.name for field in MARKET_BAR_SCHEMA.fields]
    missing_required = col(f"bar.{required_fields[0]}").isNull()
    for field in required_fields[1:]:
        missing_required = missing_required | col(f"bar.{field}").isNull()

    return parsed.withColumn(
        "invalid_reason",
        when(col("bar").isNull(), lit("malformed_json"))
        .when(missing_required, lit("missing_required_field"))
        .when(col("bar.schema_version") != 1, lit("unsupported_schema_version"))
        .when(~col("bar.symbol").rlike("^[A-Z][A-Z0-9.-]{0,15}$"), lit("invalid_symbol"))
        .when(col("bar.interval") != "1Min", lit("unsupported_interval"))
        .when(col("bar.volume") < 0, lit("negative_volume"))
        .when(col("bar.high") < col("bar.open"), lit("invalid_high"))
        .when(col("bar.high") < col("bar.close"), lit("invalid_high"))
        .when(col("bar.high") < col("bar.low"), lit("invalid_high"))
        .when(col("bar.low") > col("bar.open"), lit("invalid_low"))
        .when(col("bar.low") > col("bar.close"), lit("invalid_low"))
        .when(col("bar.low") > col("bar.high"), lit("invalid_low"))
        .when(to_date(col("bar.event_time_utc")) != lit(logical_date), lit("wrong_logical_date")),
    )


def canonical_silver(classified: DataFrame, run_id: str, code_version: str) -> DataFrame:
    valid = classified.filter(col("invalid_reason").isNull()).select(
        "bar.*",
        "source_file",
        regexp_extract(col("source_file"), r"/topic=([^/]+)/", 1).alias("source_topic"),
        regexp_extract(col("source_file"), r"/partition=([0-9]+)/", 1)
        .cast("int")
        .alias("source_partition"),
        regexp_extract(col("source_file"), r"/offset=([0-9]+)\.json$", 1)
        .cast("long")
        .alias("source_offset"),
    )
    window = Window.partitionBy("symbol", "event_time_utc", "interval").orderBy(
        col("ingested_at_utc").desc(), col("source_offset").desc()
    )
    return (
        valid.withColumn("dedup_rank", row_number().over(window))
        .filter(col("dedup_rank") == 1)
        .drop("dedup_rank")
        .withColumnRenamed("schema_version", "event_schema_version")
        .withColumn("dataset_schema_version", lit(1))
        .withColumn("pipeline_run_id", lit(run_id))
        .withColumn("code_version", lit(code_version))
        .withColumn("data_version", lit("market-bars-silver-v1"))
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--logical-date", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--symbols-json")
    args = parser.parse_args()
    logical_date = date.fromisoformat(args.logical_date)
    UUID(args.run_id)
    selected_symbols = None
    if args.symbols_json:
        selected_symbols = tuple(
            sorted(
                {
                    str(symbol).strip().upper()
                    for symbol in json.loads(args.symbols_json)
                    if str(symbol).strip()
                }
            )
        )
        if not selected_symbols:
            raise ValueError("symbols-json must contain at least one symbol")

    logging.basicConfig(level=logging.INFO, format="%(message)s")
    spark = build_batch_spark_session("marketpilot-bronze-to-silver")
    spark.sparkContext.setLogLevel(os.environ.get("SPARK_LOG_LEVEL", "WARN"))
    source = (
        f"{os.environ['BRONZE_URI']}/source=*/event=market_bar_1m/"
        f"year={logical_date:%Y}/month={logical_date:%m}/day={logical_date:%d}"
    )
    target = (
        f"{os.environ['SILVER_URI']}/dataset=market_bars_1m/"
        f"year={logical_date:%Y}/month={logical_date:%m}/day={logical_date:%d}"
    )
    quarantine = (
        f"{os.environ['SILVER_URI']}/quarantine/dataset=market_bars_1m/"
        f"logical_date={logical_date.isoformat()}/run_id={args.run_id}"
    )
    try:
        raw = (
            spark.read.format("binaryFile")
            .option("recursiveFileLookup", "true")
            .option("pathGlobFilter", "*.json")
            .load(source)
        )
        classified = classify_bronze(raw, logical_date)
        if selected_symbols is not None:
            classified = classified.filter(col("bar.symbol").isin(*selected_symbols))
        classified = classified.cache()
        invalid = classified.filter(col("invalid_reason").isNotNull())
        invalid_count = invalid.count()
        if invalid_count:
            invalid.select("invalid_reason", "source_file", "raw_value").write.mode(
                "overwrite"
            ).json(quarantine)
            raise RuntimeError(
                f"Bronze validation failed for {invalid_count} records; see {quarantine}"
            )

        input_count = classified.count()
        silver = canonical_silver(
            classified,
            args.run_id,
            os.environ.get("MARKETPILOT_CODE_VERSION", "development"),
        ).cache()
        output_count = silver.count()
        if output_count == 0:
            raise RuntimeError("Bronze partition contains no valid market bars")
        if selected_symbols is None:
            (
                silver.repartition("symbol")
                .write.mode("overwrite")
                .option("compression", "snappy")
                .partitionBy("symbol")
                .parquet(target)
            )
        else:
            for symbol in selected_symbols:
                (
                    silver.filter(col("symbol") == symbol)
                    .drop("symbol")
                    .coalesce(1)
                    .write.mode("overwrite")
                    .option("compression", "snappy")
                    .parquet(f"{target}/symbol={symbol}")
                )
        logger.info(
            json.dumps(
                {
                    "event": "bronze_to_silver_completed",
                    "logical_date": logical_date.isoformat(),
                    "run_id": args.run_id,
                    "input_rows": input_count,
                    "output_rows": output_count,
                    "duplicates_removed": input_count - output_count,
                    "symbols": selected_symbols or "configured-universe",
                    "target": target,
                },
                separators=(",", ":"),
            )
        )
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
