"""Measure and persist blocking quality checks for one Silver partition."""

import argparse
import json
import logging
import os
from dataclasses import asdict
from datetime import date
from uuid import UUID

from pyspark.sql.functions import (
    col,
    count,
    countDistinct,
    lit,
    struct,
    to_date,
    unix_timestamp,
    when,
)
from pyspark.sql.functions import max as spark_max
from pyspark.sql.functions import sum as spark_sum

from marketpilot.batch.mariadb import publisher_config_from_env, record_quality_gate
from marketpilot.batch.market_calendar import expected_xnys_market_minutes
from marketpilot.batch.quality import (
    QualityGateFailed,
    QualityMetrics,
    QualityPolicy,
    evaluate_quality_gate,
    quality_gate_passed,
)
from marketpilot.batch.spark_support import build_batch_spark_session

logger = logging.getLogger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--logical-date", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--expected-symbols-json")
    parser.add_argument("--expected-bars-per-symbol", type=int)
    parser.add_argument("--partition-key")
    parser.add_argument(
        "--maximum-ingestion-lag-seconds",
        type=int,
        default=int(os.environ.get("BATCH_MAX_INGESTION_LAG_SECONDS", "300")),
    )
    args = parser.parse_args()
    logical_date = date.fromisoformat(args.logical_date)
    UUID(args.run_id)
    if args.expected_symbols_json:
        raw_symbols = json.loads(args.expected_symbols_json)
    else:
        raw_symbols = os.environ["MARKET_SYMBOLS"].split(",")
    expected_symbols = tuple(
        sorted(str(symbol).strip().upper() for symbol in raw_symbols if str(symbol).strip())
    )
    expected_bars_per_symbol = args.expected_bars_per_symbol
    if expected_bars_per_symbol is None:
        expected_bars_per_symbol = expected_xnys_market_minutes(logical_date)
        if expected_bars_per_symbol == 0:
            raise ValueError(f"{logical_date} is not an XNYS trading session")

    logging.basicConfig(level=logging.INFO, format="%(message)s")
    spark = build_batch_spark_session("marketpilot-validate-silver")
    spark.sparkContext.setLogLevel(os.environ.get("SPARK_LOG_LEVEL", "WARN"))
    source = (
        f"{os.environ['SILVER_URI']}/dataset=market_bars_1m/"
        f"year={logical_date:%Y}/month={logical_date:%m}/day={logical_date:%d}"
    )
    try:
        frame = spark.read.parquet(source).filter(col("symbol").isin(*expected_symbols)).cache()
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
            "ingested_at_utc",
            "source_topic",
            "source_partition",
            "source_offset",
        ]
        any_null = col(required[0]).isNull()
        for field in required[1:]:
            any_null = any_null | col(field).isNull()
        lag_seconds = unix_timestamp("ingested_at_utc") - unix_timestamp("event_time_utc")
        aggregate = frame.agg(
            count("*").alias("total_rows"),
            countDistinct(struct("symbol", "event_time_utc", "interval")).alias(
                "distinct_business_keys"
            ),
            spark_sum(when(any_null, 1).otherwise(0)).alias("required_null_rows"),
            spark_sum(
                when(
                    (col("high") < col("open"))
                    | (col("high") < col("close"))
                    | (col("high") < col("low"))
                    | (col("low") > col("open"))
                    | (col("low") > col("close"))
                    | (col("low") > col("high")),
                    1,
                ).otherwise(0)
            ).alias("invalid_ohlc_rows"),
            spark_sum(when(to_date("event_time_utc") != lit(logical_date), 1).otherwise(0)).alias(
                "wrong_logical_date_rows"
            ),
            spark_sum(
                when(
                    (col("event_schema_version") != 1) | (col("dataset_schema_version") != 1),
                    1,
                ).otherwise(0)
            ).alias("invalid_schema_rows"),
            spark_sum(when(lag_seconds < 0, 1).otherwise(0)).alias("event_after_ingestion_rows"),
            spark_max(lag_seconds).alias("maximum_ingestion_lag_seconds"),
        ).first()
        rows_by_symbol = {
            str(row["symbol"]): int(row["count"])
            for row in frame.groupBy("symbol").count().collect()
        }
        metrics = QualityMetrics(
            total_rows=int(aggregate["total_rows"]),
            distinct_business_keys=int(aggregate["distinct_business_keys"]),
            required_null_rows=int(aggregate["required_null_rows"] or 0),
            invalid_ohlc_rows=int(aggregate["invalid_ohlc_rows"] or 0),
            wrong_logical_date_rows=int(aggregate["wrong_logical_date_rows"] or 0),
            invalid_schema_rows=int(aggregate["invalid_schema_rows"] or 0),
            event_after_ingestion_rows=int(aggregate["event_after_ingestion_rows"] or 0),
            maximum_ingestion_lag_seconds=(
                int(aggregate["maximum_ingestion_lag_seconds"])
                if aggregate["maximum_ingestion_lag_seconds"] is not None
                else None
            ),
            rows_by_symbol=rows_by_symbol,
        )
        results = evaluate_quality_gate(
            metrics,
            QualityPolicy(
                expected_symbols=expected_symbols,
                expected_bars_per_symbol=expected_bars_per_symbol,
                maximum_ingestion_lag_seconds=args.maximum_ingestion_lag_seconds,
            ),
        )
        record_quality_gate(
            publisher_config_from_env(),
            args.run_id,
            logical_date,
            results,
            partition_key=args.partition_key,
        )
        logger.info(
            json.dumps(
                {
                    "event": "silver_quality_completed",
                    "logical_date": logical_date.isoformat(),
                    "run_id": args.run_id,
                    "passed": quality_gate_passed(results),
                    "checks": [asdict(result) for result in results],
                },
                separators=(",", ":"),
            )
        )
        if not quality_gate_passed(results):
            failed = ",".join(result.check_name for result in results if result.status == "FAIL")
            raise QualityGateFailed(f"Silver quality gate failed: {failed}")
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
