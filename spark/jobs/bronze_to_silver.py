"""Normalize one logical Bronze partition into canonical Silver Parquet."""

import argparse
import os

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, input_file_name, to_date


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--logical-date", required=True)
    args = parser.parse_args()
    spark = SparkSession.builder.appName("marketpilot-bronze-to-silver").getOrCreate()
    source = (
        f"{os.environ['BRONZE_URI']}/source=alpaca/event=market_bar_1m/"
        f"year={args.logical_date[:4]}/month={args.logical_date[5:7]}/"
        f"day={args.logical_date[8:10]}"
    )
    target = f"{os.environ['SILVER_URI']}/dataset=market_bars_1m/trade_date={args.logical_date}"
    frame = (
        spark.read.json(source)
        .withColumn("source_file", input_file_name())
        .withColumn("trade_date", to_date(col("event_time_utc")))
        .dropDuplicates(["symbol", "event_time_utc"])
    )
    frame.write.mode("overwrite").parquet(target)


if __name__ == "__main__":
    main()
