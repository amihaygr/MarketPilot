"""Calculate and atomically publish versioned indicators and explained signals."""

import argparse
import json
import logging
import math
import os
from datetime import timedelta

from pyspark.sql import DataFrame, Window
from pyspark.sql.functions import (
    abs as abs_,
)
from pyspark.sql.functions import (
    avg,
    col,
    concat,
    count,
    greatest,
    lag,
    least,
    lit,
    log,
    stddev_samp,
    to_date,
    when,
)
from pyspark.sql.functions import (
    round as round_,
)

from marketpilot.analytics.mariadb import publish_analytics_partition
from marketpilot.analytics.rules import (
    INDICATOR_SCHEMA_VERSION,
    INDICATOR_VERSION,
    SIGNAL_MODEL_VERSION,
    SIGNAL_SCHEMA_VERSION,
    resolve_analytics_scope,
)
from marketpilot.batch.mariadb import publisher_config_from_env
from marketpilot.batch.spark_support import build_batch_spark_session
from marketpilot.operations.archive import spark_mariadb_jdbc_url

logger = logging.getLogger(__name__)


def _indicator(
    frame: DataFrame,
    *,
    value_column: str,
    code: str,
    lookback: int,
    valid_column: str,
    code_version: str,
) -> DataFrame:
    return frame.filter(col(valid_column)).select(
        "symbol_id",
        "event_time_utc",
        lit(code).alias("indicator_code"),
        lit(INDICATOR_VERSION).alias("indicator_version"),
        col(value_column).cast("decimal(24,10)").alias("indicator_value"),
        lit(lookback).alias("lookback_bars"),
        "certification_status",
        lit(code_version).alias("code_version"),
        lit("market-analytics-v1").alias("data_version"),
        lit(INDICATOR_SCHEMA_VERSION).alias("schema_version"),
    )


def _signal(
    frame: DataFrame,
    *,
    condition,  # type: ignore[no-untyped-def]
    code: str,
    direction: str,
    strength,  # type: ignore[no-untyped-def]
    explanation,  # type: ignore[no-untyped-def]
    code_version: str,
) -> DataFrame:
    return frame.filter(condition).select(
        "symbol_id",
        col("event_time_utc").alias("signal_time_utc"),
        lit(code).alias("signal_code"),
        lit(SIGNAL_MODEL_VERSION).alias("model_version"),
        lit(direction).alias("direction"),
        strength.cast("decimal(8,6)").alias("strength"),
        explanation.alias("explanation"),
        "certification_status",
        lit(code_version).alias("code_version"),
        lit("market-signals-v1").alias("data_version"),
        lit(SIGNAL_SCHEMA_VERSION).alias("schema_version"),
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--logical-date", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--lookback-days", type=int, default=10)
    args = parser.parse_args()
    scope = resolve_analytics_scope(args.logical_date, args.run_id, args.lookback_days)
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    start = scope.logical_date - timedelta(days=scope.lookback_days)
    end = scope.logical_date + timedelta(days=1)
    query = f"""(
        SELECT f.symbol_id, d.symbol, f.event_time_utc, f.close_price, f.volume,
               f.certification_status
        FROM fact_market_bar_1m f
        JOIN dim_symbol d ON d.symbol_id = f.symbol_id
        WHERE f.event_time_utc >= '{start.isoformat()} 00:00:00'
          AND f.event_time_utc < '{end.isoformat()} 00:00:00'
    ) analytics_source"""
    spark = build_batch_spark_session("marketpilot-market-analytics")
    spark.sparkContext.setLogLevel(os.environ.get("SPARK_LOG_LEVEL", "WARN"))
    code_version = os.environ.get("MARKETPILOT_CODE_VERSION", "development")
    try:
        source = (
            spark.read.format("jdbc")
            .option("url", spark_mariadb_jdbc_url(os.environ["MARIADB_JDBC_URL"]))
            .option("dbtable", query)
            .option("user", os.environ["MARIADB_PUBLISH_USER"])
            .option("password", os.environ["MARIADB_PUBLISH_PASSWORD"])
            .option("driver", "org.mariadb.jdbc.Driver")
            .option("fetchsize", "1000")
            .load()
        )
        if source.limit(1).count() == 0:
            raise RuntimeError("analytics source contains no market bars")

        ordered = Window.partitionBy("symbol_id").orderBy("event_time_utc")
        last_20 = ordered.rowsBetween(-19, 0)
        previous_20 = ordered.rowsBetween(-20, -1)
        last_14_changes = ordered.rowsBetween(-13, 0)
        metrics = (
            source.withColumn("previous_close", lag("close_price").over(ordered))
            .withColumn("price_change", col("close_price") - col("previous_close"))
            .withColumn("gain", greatest(col("price_change"), lit(0.0)))
            .withColumn("loss", greatest(-col("price_change"), lit(0.0)))
            .withColumn("log_return", log(col("close_price") / col("previous_close")))
            .withColumn("sma_20", avg("close_price").over(last_20))
            .withColumn("sma_count", count("close_price").over(last_20))
            .withColumn("average_gain_14", avg("gain").over(last_14_changes))
            .withColumn("average_loss_14", avg("loss").over(last_14_changes))
            .withColumn("rsi_count", count("price_change").over(last_14_changes))
            .withColumn("return_volatility_20", stddev_samp("log_return").over(last_20))
            .withColumn("return_count", count("log_return").over(last_20))
            .withColumn("average_prior_volume_20", avg("volume").over(previous_20))
            .withColumn("prior_volume_count", count("volume").over(previous_20))
            .withColumn(
                "rsi_14",
                when(
                    (col("average_gain_14") == 0) & (col("average_loss_14") == 0),
                    lit(50.0),
                )
                .when(col("average_loss_14") == 0, lit(100.0))
                .otherwise(
                    lit(100.0)
                    - lit(100.0) / (lit(1.0) + col("average_gain_14") / col("average_loss_14"))
                ),
            )
            .withColumn(
                "realized_volatility_20",
                col("return_volatility_20") * lit(math.sqrt(390.0) * 100.0),
            )
            .withColumn(
                "volume_ratio_20",
                col("volume") / col("average_prior_volume_20"),
            )
        )
        metrics = (
            metrics.withColumn("previous_sma_20", lag("sma_20").over(ordered))
            .withColumn("previous_rsi_14", lag("rsi_14").over(ordered))
            .withColumn("previous_volume_ratio_20", lag("volume_ratio_20").over(ordered))
            .filter(to_date("event_time_utc") == lit(scope.logical_date.isoformat()))
            .cache()
        )
        metrics = (
            metrics.withColumn("sma_valid", col("sma_count") == 20)
            .withColumn("rsi_valid", col("rsi_count") == 14)
            .withColumn("volatility_valid", col("return_count") == 20)
            .withColumn(
                "volume_ratio_valid",
                (col("prior_volume_count") == 20) & (col("average_prior_volume_20") > 0),
            )
        )
        indicators = _indicator(
            metrics,
            value_column="sma_20",
            code="SMA_20",
            lookback=20,
            valid_column="sma_valid",
            code_version=code_version,
        )
        indicators = (
            indicators.unionByName(
                _indicator(
                    metrics,
                    value_column="rsi_14",
                    code="RSI_14",
                    lookback=14,
                    valid_column="rsi_valid",
                    code_version=code_version,
                )
            )
            .unionByName(
                _indicator(
                    metrics,
                    value_column="realized_volatility_20",
                    code="REALIZED_VOLATILITY_20",
                    lookback=20,
                    valid_column="volatility_valid",
                    code_version=code_version,
                )
            )
            .unionByName(
                _indicator(
                    metrics,
                    value_column="volume_ratio_20",
                    code="VOLUME_RATIO_20",
                    lookback=20,
                    valid_column="volume_ratio_valid",
                    code_version=code_version,
                )
            )
            .cache()
        )

        cross_distance = least(
            lit(1.0), abs_(col("close_price") / col("sma_20") - lit(1.0)) / lit(0.02)
        )
        signals = _signal(
            metrics,
            condition=(
                col("sma_valid")
                & (col("previous_close") <= col("previous_sma_20"))
                & (col("close_price") > col("sma_20"))
            ),
            code="PRICE_CROSS_ABOVE_SMA20",
            direction="BULLISH",
            strength=cross_distance,
            explanation=concat(
                lit("Close crossed above SMA20; close="),
                round_(col("close_price"), 4),
                lit(", SMA20="),
                round_(col("sma_20"), 4),
            ),
            code_version=code_version,
        ).unionByName(
            _signal(
                metrics,
                condition=(
                    col("sma_valid")
                    & (col("previous_close") >= col("previous_sma_20"))
                    & (col("close_price") < col("sma_20"))
                ),
                code="PRICE_CROSS_BELOW_SMA20",
                direction="BEARISH",
                strength=cross_distance,
                explanation=concat(
                    lit("Close crossed below SMA20; close="),
                    round_(col("close_price"), 4),
                    lit(", SMA20="),
                    round_(col("sma_20"), 4),
                ),
                code_version=code_version,
            )
        )
        oversold_strength = least(
            lit(1.0), greatest(lit(0.0), (lit(30.0) - col("rsi_14")) / lit(30.0))
        )
        overbought_strength = least(
            lit(1.0), greatest(lit(0.0), (col("rsi_14") - lit(70.0)) / lit(30.0))
        )
        signals = signals.unionByName(
            _signal(
                metrics,
                condition=(
                    col("rsi_valid") & (col("previous_rsi_14") > 30) & (col("rsi_14") <= 30)
                ),
                code="RSI_CROSS_OVERSOLD",
                direction="BULLISH",
                strength=oversold_strength,
                explanation=concat(
                    lit("RSI14 crossed into oversold zone; RSI="), round_(col("rsi_14"), 2)
                ),
                code_version=code_version,
            )
        ).unionByName(
            _signal(
                metrics,
                condition=(
                    col("rsi_valid") & (col("previous_rsi_14") < 70) & (col("rsi_14") >= 70)
                ),
                code="RSI_CROSS_OVERBOUGHT",
                direction="BEARISH",
                strength=overbought_strength,
                explanation=concat(
                    lit("RSI14 crossed into overbought zone; RSI="), round_(col("rsi_14"), 2)
                ),
                code_version=code_version,
            )
        )
        volume_strength = least(
            lit(1.0), greatest(lit(0.0), (col("volume_ratio_20") - lit(2.0)) / lit(3.0))
        )
        signals = signals.unionByName(
            _signal(
                metrics,
                condition=(
                    col("volume_ratio_valid")
                    & (col("volume_ratio_20") >= 2)
                    & (
                        (col("previous_volume_ratio_20") < 2)
                        | col("previous_volume_ratio_20").isNull()
                    )
                ),
                code="VOLUME_SPIKE",
                direction="WATCH",
                strength=volume_strength,
                explanation=concat(
                    lit("Volume is at least 2x its prior 20-bar mean; ratio="),
                    round_(col("volume_ratio_20"), 2),
                ),
                code_version=code_version,
            )
        ).cache()

        indicator_count = indicators.count()
        invalid_rsi = indicators.filter(
            (col("indicator_code") == "RSI_14")
            & ((col("indicator_value") < 0) | (col("indicator_value") > 100))
        ).count()
        indicator_duplicates = (
            indicators.groupBy("symbol_id", "event_time_utc", "indicator_code", "indicator_version")
            .count()
            .filter(col("count") > 1)
            .count()
        )
        if indicator_count == 0 or invalid_rsi or indicator_duplicates:
            raise RuntimeError("analytics data-quality gate failed")

        published_indicators, published_signals = publish_analytics_partition(
            publisher_config_from_env(),
            logical_date=scope.logical_date,
            run_id=scope.run_id,
            indicators=indicators.toLocalIterator(),
            signals=signals.toLocalIterator(),
        )
        logger.info(
            json.dumps(
                {
                    "event": "market_analytics_published",
                    "logical_date": scope.logical_date.isoformat(),
                    "run_id": scope.run_id,
                    "indicator_rows": published_indicators,
                    "signal_rows": published_signals,
                    "indicator_schema_version": INDICATOR_SCHEMA_VERSION,
                    "signal_schema_version": SIGNAL_SCHEMA_VERSION,
                },
                separators=(",", ":"),
            )
        )
        indicators.unpersist()
        signals.unpersist()
        metrics.unpersist()
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
