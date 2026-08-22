"""Publish a validated Silver partition to a Gold JDBC staging boundary."""

import argparse
import os

from pyspark.sql import SparkSession
from pyspark.sql.functions import lit


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--logical-date", required=True)
    parser.add_argument("--certification-status", choices=["CERTIFIED"], required=True)
    args = parser.parse_args()
    spark = SparkSession.builder.appName("marketpilot-silver-to-gold").getOrCreate()
    source = f"{os.environ['SILVER_URI']}/dataset=market_bars_1m/trade_date={args.logical_date}"
    frame = spark.read.parquet(source).withColumn(
        "certification_status", lit(args.certification_status)
    )
    (
        frame.write.format("jdbc")
        .option("url", os.environ["MARIADB_JDBC_URL"])
        .option("dbtable", "stg_market_bar_1m")
        .option("user", os.environ["MARIADB_INGEST_USER"])
        .option("password", os.environ["MARIADB_INGEST_PASSWORD"])
        .mode("overwrite")
        .save()
    )


if __name__ == "__main__":
    main()
