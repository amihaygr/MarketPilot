"""Long-running Structured Streaming entry point, supervised by Docker Compose."""

import os

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json
from pyspark.sql.types import (
    DecimalType,
    LongType,
    StringType,
    StructField,
    StructType,
    TimestampType,
)

SCHEMA = StructType(
    [
        StructField("event_id", StringType(), False),
        StructField("symbol", StringType(), False),
        StructField("event_time_utc", TimestampType(), False),
        StructField("open", DecimalType(19, 6), False),
        StructField("high", DecimalType(19, 6), False),
        StructField("low", DecimalType(19, 6), False),
        StructField("close", DecimalType(19, 6), False),
        StructField("volume", LongType(), False),
        StructField("schema_version", LongType(), False),
    ]
)


def main() -> None:
    spark = SparkSession.builder.appName("marketpilot-market-bars-v1").getOrCreate()
    raw = (
        spark.readStream.format("kafka")
        .option("kafka.bootstrap.servers", os.environ["KAFKA_BOOTSTRAP_SERVERS"])
        .option("subscribe", os.environ["KAFKA_MARKET_BARS_TOPIC"])
        .option("startingOffsets", "latest")
        .load()
    )
    bars = (
        raw.select(from_json(col("value").cast("string"), SCHEMA).alias("bar"))
        .select("bar.*")
        .withWatermark("event_time_utc", "10 minutes")
        .dropDuplicates(["symbol", "event_time_utc"])
    )

    query = (
        bars.writeStream.format("console")
        .outputMode("append")
        .option(
            "checkpointLocation",
            os.environ.get("SPARK_CHECKPOINT_PATH", "/checkpoints/market-bars-v1"),
        )
        .trigger(
            processingTime=(f"{os.environ.get('SPARK_STREAMING_TRIGGER_SECONDS', '60')} seconds")
        )
        .start()
    )
    query.awaitTermination()


if __name__ == "__main__":
    main()
