"""Long-running Kafka to MariaDB Gold Structured Streaming application."""

import json
import logging
import os
from functools import partial
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.functions import (
    col,
    concat_ws,
    current_timestamp,
    from_json,
    greatest,
    least,
    lit,
    struct,
    to_json,
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

from marketpilot.streaming.mariadb_sink import MariaDbConfig, upsert_market_bar_partition

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


def parse_and_classify(raw: DataFrame) -> DataFrame:
    """Parse Kafka values and attach one explicit validation failure reason."""
    parsed = raw.select(
        col("topic").alias("kafka_topic"),
        col("partition").alias("kafka_partition"),
        col("offset").alias("kafka_offset"),
        col("timestamp").alias("kafka_timestamp_utc"),
        col("value").cast("string").alias("raw_value"),
        from_json(col("value").cast("string"), MARKET_BAR_SCHEMA).alias("bar"),
    )

    required = [
        "event_id",
        "symbol",
        "event_time_utc",
        "interval",
        "open",
        "high",
        "low",
        "close",
        "volume",
        "source",
        "schema_version",
        "ingested_at_utc",
    ]
    missing_required = col(f"bar.{required[0]}").isNull()
    for field in required[1:]:
        missing_required = missing_required | col(f"bar.{field}").isNull()

    return parsed.withColumn(
        "invalid_reason",
        when(col("bar").isNull(), lit("malformed_json"))
        .when(missing_required, lit("missing_required_field"))
        .when(col("bar.schema_version") != 1, lit("unsupported_schema_version"))
        .when(
            ~col("bar.event_id").rlike(
                "^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-"
                "[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$"
            ),
            lit("invalid_event_id"),
        )
        .when(~col("bar.symbol").rlike("^[A-Z][A-Z0-9.-]{0,15}$"), lit("invalid_symbol"))
        .when(col("bar.interval") != "1Min", lit("unsupported_interval"))
        .when(col("bar.volume") < 0, lit("negative_volume"))
        .when(
            col("bar.high") < greatest(col("bar.open"), col("bar.close"), col("bar.low")),
            lit("invalid_high"),
        )
        .when(
            col("bar.low") > least(col("bar.open"), col("bar.close"), col("bar.high")),
            lit("invalid_low"),
        ),
    )


def valid_market_bars(classified: DataFrame) -> DataFrame:
    return (
        classified.filter(col("invalid_reason").isNull())
        .select("bar.*", "kafka_topic", "kafka_partition", "kafka_offset")
        .withWatermark("event_time_utc", "10 minutes")
        .dropDuplicates(["symbol", "event_time_utc", "interval"])
    )


def invalid_market_bars(classified: DataFrame) -> DataFrame:
    return classified.filter(col("invalid_reason").isNotNull()).select(
        concat_ws(
            ":",
            col("kafka_topic"),
            col("kafka_partition").cast("string"),
            col("kafka_offset").cast("string"),
        ).alias("key"),
        to_json(
            struct(
                col("invalid_reason").alias("reason"),
                col("kafka_topic").alias("source_topic"),
                col("kafka_partition").alias("source_partition"),
                col("kafka_offset").alias("source_offset"),
                col("kafka_timestamp_utc"),
                col("raw_value"),
                current_timestamp().alias("failed_at_utc"),
            )
        ).alias("value"),
    )


def write_gold_batch(
    batch: DataFrame,
    batch_id: int,
    *,
    database: MariaDbConfig,
    code_version: str,
) -> None:
    run_id = str(uuid5(NAMESPACE_URL, f"marketpilot:streaming:{batch_id}"))
    enriched = (
        batch.withColumn("pipeline_run_id", lit(run_id))
        .withColumn("code_version", lit(code_version))
        .withColumn("data_version", lit("market-bar-v1"))
    )
    if enriched.isEmpty():
        return
    enriched.foreachPartition(partial(upsert_market_bar_partition, config=database))
    logger.info(
        json.dumps(
            {"event": "gold_batch_committed", "batch_id": batch_id, "run_id": run_id},
            separators=(",", ":"),
        )
    )


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    spark = (
        SparkSession.builder.appName("marketpilot-market-bars-v1")
        .config("spark.sql.session.timeZone", "UTC")
        .config("spark.sql.shuffle.partitions", "3")
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel(os.environ.get("SPARK_LOG_LEVEL", "WARN"))

    database = MariaDbConfig(
        host=os.environ["MARIADB_HOST"],
        port=int(os.environ.get("MARIADB_PORT", "3306")),
        database=os.environ["MARIADB_DATABASE"],
        user=os.environ["MARIADB_INGEST_USER"],
        password=os.environ["MARIADB_INGEST_PASSWORD"],
    )
    checkpoint_root = os.environ.get("SPARK_CHECKPOINT_PATH", "/checkpoints/market-bars-v1")
    trigger = f"{os.environ.get('SPARK_STREAMING_TRIGGER_SECONDS', '60')} seconds"

    raw = (
        spark.readStream.format("kafka")
        .option("kafka.bootstrap.servers", os.environ["KAFKA_BOOTSTRAP_SERVERS"])
        .option("subscribe", os.environ["KAFKA_MARKET_BARS_TOPIC"])
        .option("startingOffsets", "latest")
        .load()
    )
    classified = parse_and_classify(raw)

    gold_query = (
        valid_market_bars(classified)
        .writeStream.queryName("marketpilot-gold-provisional-v1")
        .foreachBatch(
            partial(
                write_gold_batch,
                database=database,
                code_version=os.environ.get("MARKETPILOT_CODE_VERSION", "development"),
            )
        )
        .outputMode("append")
        .option("checkpointLocation", f"{checkpoint_root}/gold")
        .trigger(processingTime=trigger)
        .start()
    )
    dlq_query = (
        invalid_market_bars(classified)
        .writeStream.queryName("marketpilot-market-bars-dlq-v1")
        .format("kafka")
        .option("kafka.bootstrap.servers", os.environ["KAFKA_BOOTSTRAP_SERVERS"])
        .option("topic", os.environ["KAFKA_DEAD_LETTER_TOPIC"])
        .option("checkpointLocation", f"{checkpoint_root}/dlq")
        .outputMode("append")
        .trigger(processingTime=trigger)
        .start()
    )

    ready_file = Path(os.environ.get("SPARK_STREAMING_READY_FILE", "/tmp/streaming-ready"))
    ready_file.touch()
    logger.info(
        json.dumps(
            {
                "event": "streaming_started",
                "queries": [gold_query.name, dlq_query.name],
                "checkpoint_root": checkpoint_root,
            },
            separators=(",", ":"),
        )
    )
    try:
        spark.streams.awaitAnyTermination()
        failures = [query.exception() for query in (gold_query, dlq_query)]
        failed = next((failure for failure in failures if failure is not None), None)
        if failed is not None:
            raise RuntimeError(f"streaming query terminated: {failed}")
    finally:
        ready_file.unlink(missing_ok=True)
        for query in (gold_query, dlq_query):
            if query.isActive:
                query.stop()
        spark.stop()


if __name__ == "__main__":
    main()
