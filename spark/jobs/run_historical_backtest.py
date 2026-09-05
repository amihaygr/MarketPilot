"""Run and publish a bounded, versioned historical strategy evaluation."""

from __future__ import annotations

import argparse
import json
import logging
import math
import os
from collections import defaultdict
from datetime import timedelta, timezone
from decimal import Decimal

from pyspark.sql import DataFrame, Window
from pyspark.sql.functions import (
    abs as abs_,
)
from pyspark.sql.functions import (
    avg,
    broadcast,
    col,
    count,
    exp,
    lag,
    lit,
    log1p,
    max_by,
    row_number,
    stddev_samp,
    to_date,
    when,
)
from pyspark.sql.functions import (
    max as max_,
)
from pyspark.sql.functions import (
    min as min_,
)
from pyspark.sql.functions import (
    sum as sum_,
)

from marketpilot.backtesting.mariadb import publish_backtest
from marketpilot.backtesting.rules import (
    BACKTEST_SCHEMA_VERSION,
    PERIODS_PER_YEAR,
    STRATEGY_CODE,
    STRATEGY_VERSION,
    BacktestResult,
    EquityPoint,
    resolve_backtest_scope,
)
from marketpilot.batch.mariadb import publisher_config_from_env
from marketpilot.batch.market_calendar import xnys_session_windows
from marketpilot.batch.spark_support import build_batch_spark_session
from marketpilot.operations.archive import spark_mariadb_jdbc_url
from marketpilot.operations.object_store import (
    inventory,
    inventory_checksum,
    object_store_client,
    parse_s3_uri,
    write_json,
)

logger = logging.getLogger(__name__)
UTC = timezone.utc  # noqa: UP017 -- Spark 3.5.8 image uses Python 3.10.


def main() -> None:
    args = _arguments()
    scope = resolve_backtest_scope(
        run_id=args.run_id,
        start_date_value=args.start_date,
        end_date_value=args.end_date,
        symbols_value=args.symbols,
        benchmark_symbol=args.benchmark_symbol,
        short_window=args.short_window,
        long_window=args.long_window,
        initial_capital=args.initial_capital,
        transaction_cost_bps=args.transaction_cost_bps,
        slippage_bps=args.slippage_bps,
    )
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    symbols = tuple(dict.fromkeys((*scope.symbols, scope.benchmark_symbol)))
    quoted_symbols = ",".join(f"'{symbol}'" for symbol in symbols)
    end_exclusive = scope.end_date + timedelta(days=1)
    query = f"""(
        SELECT f.symbol_id, d.symbol, f.event_time_utc, f.close_price,
               f.certification_status
        FROM fact_market_bar_1m f
        JOIN dim_symbol d ON d.symbol_id = f.symbol_id
        WHERE f.event_time_utc >= '{scope.start_date.isoformat()} 00:00:00'
          AND f.event_time_utc < '{end_exclusive.isoformat()} 00:00:00'
          AND d.symbol IN ({quoted_symbols})
    ) backtest_source"""
    spark = build_batch_spark_session("marketpilot-historical-backtest")
    spark.sparkContext.setLogLevel(os.environ.get("SPARK_LOG_LEVEL", "WARN"))
    output_root = os.environ.get(
        "BACKTEST_OUTPUT_URI", "s3a://marketpilot-analytics/backtests"
    ).rstrip("/")
    detailed_uri = f"{output_root}/run_id={scope.run_id}/detail"
    location = parse_s3_uri(output_root)
    code_version = os.environ.get("MARKETPILOT_CODE_VERSION", "development")
    data_version = "certified-gold-bars-v1"
    try:
        raw_source = _read_source(spark, query).cache()
        raw_source_count = raw_source.count()
        source = _filter_xnys_regular_sessions(
            spark, raw_source, scope.start_date, scope.end_date
        ).cache()
        source_count = source.count()
        excluded_non_session_rows = raw_source_count - source_count
        logger.info(
            json.dumps(
                {
                    "event": "backtest_source_session_filter",
                    "run_id": scope.run_id,
                    "raw_rows": raw_source_count,
                    "eligible_rows": source_count,
                    "excluded_non_session_rows": excluded_non_session_rows,
                },
                separators=(",", ":"),
            )
        )
        _validate_source(source, symbols, scope.long_window)
        curve = _calculate_curve(source, scope).cache()
        detail_count = curve.count()
        if detail_count < len(scope.symbols):
            raise RuntimeError("backtest detailed output is unexpectedly empty")
        detailed = (
            curve.withColumn("run_id", lit(scope.run_id))
            .withColumn("strategy_code", lit(STRATEGY_CODE))
            .withColumn("strategy_version", lit(STRATEGY_VERSION))
            .withColumn("schema_version", lit(BACKTEST_SCHEMA_VERSION))
            .withColumn("code_version", lit(code_version))
            .withColumn("data_version", lit(data_version))
        )
        (
            detailed.repartition("symbol")
            .write.mode("overwrite")
            .option("compression", "snappy")
            .partitionBy("symbol")
            .parquet(detailed_uri)
        )
        if spark.read.parquet(detailed_uri).count() != detail_count:
            raise RuntimeError("backtest Parquet row-count reconciliation failed")

        publishable = _collect_publishable_results(curve, scope.initial_capital)
        if {result.symbol for result in publishable} != set(scope.symbols):
            raise RuntimeError("backtest summary symbols differ from requested symbols")
        objects = inventory(
            object_store_client(),
            location.bucket,
            _detail_prefix(location.prefix, scope.run_id),
        )
        manifest = {
            "run_id": scope.run_id,
            "strategy_code": STRATEGY_CODE,
            "strategy_version": STRATEGY_VERSION,
            "schema_version": BACKTEST_SCHEMA_VERSION,
            "code_version": code_version,
            "data_version": data_version,
            "symbols": list(scope.symbols),
            "benchmark_symbol": scope.benchmark_symbol,
            "start_date": scope.start_date.isoformat(),
            "end_date": scope.end_date.isoformat(),
            "detail_row_count": detail_count,
            "source_row_count": raw_source_count,
            "excluded_non_session_rows": excluded_non_session_rows,
            "object_count": len(objects),
            "inventory_checksum_sha256": inventory_checksum(objects),
            "detailed_output_uri": detailed_uri,
        }
        write_json(
            object_store_client(),
            location.bucket,
            f"{location.prefix}/run_id={scope.run_id}/manifest.json".strip("/"),
            manifest,
        )
        published_results, published_days = publish_backtest(
            publisher_config_from_env(),
            scope=scope,
            results=publishable,
            detailed_output_uri=detailed_uri,
            code_version=code_version,
            data_version=data_version,
        )
        logger.info(
            json.dumps(
                {
                    "event": "historical_backtest_published",
                    "run_id": scope.run_id,
                    "result_rows": published_results,
                    "daily_equity_rows": published_days,
                    "detail_rows": detail_count,
                },
                separators=(",", ":"),
            )
        )
        curve.unpersist()
        source.unpersist()
        raw_source.unpersist()
    finally:
        spark.stop()


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--start-date", required=True)
    parser.add_argument("--end-date", required=True)
    parser.add_argument("--symbols", required=True)
    parser.add_argument("--benchmark-symbol", default="SPY")
    parser.add_argument("--short-window", type=int, default=20)
    parser.add_argument("--long-window", type=int, default=50)
    parser.add_argument("--initial-capital", default="10000")
    parser.add_argument("--transaction-cost-bps", default="1")
    parser.add_argument("--slippage-bps", default="1")
    return parser.parse_args()


def _read_source(spark, query: str) -> DataFrame:  # type: ignore[no-untyped-def]
    return (
        spark.read.format("jdbc")
        .option("url", spark_mariadb_jdbc_url(os.environ["MARIADB_JDBC_URL"]))
        .option("dbtable", query)
        .option("user", os.environ["MARIADB_PUBLISH_USER"])
        .option("password", os.environ["MARIADB_PUBLISH_PASSWORD"])
        .option("driver", "org.mariadb.jdbc.Driver")
        .option("fetchsize", "2000")
        .load()
    )


def _filter_xnys_regular_sessions(
    spark,
    source: DataFrame,
    start_date,
    end_date,  # type: ignore[no-untyped-def]
) -> DataFrame:
    windows = xnys_session_windows(start_date, end_date)
    if not windows:
        raise RuntimeError("backtest range contains no XNYS trading sessions")
    values = ",".join(
        "("
        f"DATE '{session_date.isoformat()}',"
        f"TIMESTAMP '{session_open.replace(tzinfo=None).isoformat(sep=' ')}',"
        f"TIMESTAMP '{session_close.replace(tzinfo=None).isoformat(sep=' ')}'"
        ")"
        for session_date, session_open, session_close in windows
    )
    session_frame = spark.sql(
        "SELECT * FROM VALUES "
        f"{values} AS session_windows("
        "xnys_session_date, session_open_utc, session_close_utc)"
    )
    return (
        source.withColumn("source_session_date", to_date("event_time_utc"))
        .join(
            broadcast(session_frame),
            col("source_session_date") == col("xnys_session_date"),
            "inner",
        )
        .filter(
            (col("event_time_utc") >= col("session_open_utc"))
            & (col("event_time_utc") < col("session_close_utc"))
        )
        .drop(
            "source_session_date",
            "xnys_session_date",
            "session_open_utc",
            "session_close_utc",
        )
    )


def _validate_source(source: DataFrame, symbols: tuple[str, ...], long_window: int) -> None:
    if source.limit(1).count() == 0:
        raise RuntimeError("backtest source contains no market bars")
    if source.filter(col("certification_status") != "CERTIFIED").limit(1).count():
        raise RuntimeError("backtest source contains non-certified market bars")
    if source.filter(col("close_price") <= 0).limit(1).count():
        raise RuntimeError("backtest source contains non-positive close prices")
    if (
        source.groupBy("symbol_id", "event_time_utc")
        .count()
        .filter(col("count") > 1)
        .limit(1)
        .count()
    ):
        raise RuntimeError("backtest source contains duplicate business keys")
    counts = {
        row["symbol"]: int(row["count"]) for row in source.groupBy("symbol").count().collect()
    }
    missing = sorted(set(symbols) - set(counts))
    if missing:
        raise RuntimeError(f"backtest source is missing symbols: {','.join(missing)}")
    insufficient = sorted(symbol for symbol in symbols if counts[symbol] <= long_window)
    if insufficient:
        raise RuntimeError(f"backtest source has insufficient history: {','.join(insufficient)}")


def _calculate_curve(source: DataFrame, scope) -> DataFrame:  # type: ignore[no-untyped-def]
    benchmark = source.filter(col("symbol") == scope.benchmark_symbol).select(
        "event_time_utc", col("close_price").alias("benchmark_close")
    )
    requested = source.filter(col("symbol").isin(list(scope.symbols))).join(
        benchmark, "event_time_utc", "inner"
    )
    ordered = Window.partitionBy("symbol_id").orderBy("event_time_utc")
    cumulative = ordered.rowsBetween(Window.unboundedPreceding, Window.currentRow)
    short_window = ordered.rowsBetween(-scope.short_window + 1, 0)
    long_window = ordered.rowsBetween(-scope.long_window + 1, 0)
    total_cost = float(scope.transaction_cost_bps + scope.slippage_bps) / 10000.0
    frame = (
        requested.withColumn("short_sma", avg("close_price").over(short_window))
        .withColumn("long_sma", avg("close_price").over(long_window))
        .withColumn("short_count", count("close_price").over(short_window))
        .withColumn("long_count", count("close_price").over(long_window))
        .withColumn(
            "desired_position",
            when(
                (col("short_count") == scope.short_window)
                & (col("long_count") == scope.long_window)
                & (col("short_sma") > col("long_sma")),
                lit(1),
            ).otherwise(lit(0)),
        )
    )
    frame = (
        frame.withColumn("previous_close", lag("close_price").over(ordered))
        .withColumn("previous_benchmark", lag("benchmark_close").over(ordered))
        .withColumn("applied_position", lag("desired_position", 1, 0).over(ordered))
    )
    frame = frame.withColumn(
        "previous_position", lag("applied_position", 1, 0).over(ordered)
    ).filter(col("previous_close").isNotNull())
    frame = (
        frame.withColumn("market_return", col("close_price") / col("previous_close") - lit(1.0))
        .withColumn(
            "benchmark_return", col("benchmark_close") / col("previous_benchmark") - lit(1.0)
        )
        .withColumn("turnover", abs_(col("applied_position") - col("previous_position")))
        .withColumn("gross_return", col("applied_position") * col("market_return"))
        .withColumn("cost_return", col("turnover") * lit(total_cost))
        .withColumn("net_return", col("gross_return") - col("cost_return"))
    )
    if frame.filter(col("net_return") <= -1).limit(1).count():
        raise RuntimeError("backtest net return would make equity non-positive")
    frame = frame.withColumn(
        "equity",
        lit(float(scope.initial_capital)) * exp(sum_(log1p("net_return")).over(cumulative)),
    ).withColumn(
        "benchmark_equity",
        lit(float(scope.initial_capital)) * exp(sum_(log1p("benchmark_return")).over(cumulative)),
    )
    return frame.withColumn("running_peak", max_("equity").over(cumulative)).withColumn(
        "drawdown", col("equity") / col("running_peak") - lit(1.0)
    )


def _collect_publishable_results(
    curve: DataFrame, initial_capital: Decimal
) -> list[BacktestResult]:
    summary = (
        curve.groupBy("symbol_id", "symbol")
        .agg(
            min_("event_time_utc").alias("first_event_time_utc"),
            max_("event_time_utc").alias("last_event_time_utc"),
            count("event_time_utc").alias("observation_count"),
            sum_("turnover").alias("trade_count"),
            max_by("equity", "event_time_utc").alias("final_equity"),
            max_by("benchmark_equity", "event_time_utc").alias("final_benchmark_equity"),
            min_("drawdown").alias("max_drawdown"),
            avg("net_return").alias("average_return"),
            stddev_samp("net_return").alias("return_volatility"),
        )
        .collect()
    )
    daily_window = Window.partitionBy("symbol_id", to_date("event_time_utc")).orderBy(
        col("event_time_utc").desc()
    )
    daily_rows = (
        curve.withColumn("daily_rank", row_number().over(daily_window))
        .filter(col("daily_rank") == 1)
        .orderBy("symbol", "event_time_utc")
        .collect()
    )
    daily: dict[str, list[EquityPoint]] = defaultdict(list)
    for row in daily_rows:
        daily[row["symbol"]].append(_equity_point(row))
    results = []
    for row in summary:
        volatility = float(row["return_volatility"] or 0.0)
        final_equity = Decimal(str(row["final_equity"]))
        final_benchmark = Decimal(str(row["final_benchmark_equity"]))
        total_return = (final_equity / initial_capital - 1) * 100
        benchmark_return = (final_benchmark / initial_capital - 1) * 100
        sharpe = None
        if volatility > 0:
            sharpe = Decimal(
                str(float(row["average_return"]) / volatility * math.sqrt(PERIODS_PER_YEAR))
            )
        results.append(
            BacktestResult(
                symbol_id=int(row["symbol_id"]),
                symbol=row["symbol"],
                first_event_time_utc=_aware_utc(row["first_event_time_utc"]),
                last_event_time_utc=_aware_utc(row["last_event_time_utc"]),
                observation_count=int(row["observation_count"]),
                trade_count=int(row["trade_count"]),
                total_return_pct=total_return,
                benchmark_return_pct=benchmark_return,
                excess_return_pct=total_return - benchmark_return,
                max_drawdown_pct=Decimal(str(row["max_drawdown"])) * 100,
                annualized_volatility_pct=Decimal(
                    str(volatility * math.sqrt(PERIODS_PER_YEAR) * 100)
                ),
                sharpe_ratio=sharpe,
                curve=tuple(daily[row["symbol"]]),
            )
        )
    return results


def _equity_point(row) -> EquityPoint:  # type: ignore[no-untyped-def]
    return EquityPoint(
        symbol_id=int(row["symbol_id"]),
        symbol=row["symbol"],
        event_time_utc=_aware_utc(row["event_time_utc"]),
        close=Decimal(str(row["close_price"])),
        short_sma=Decimal(str(row["short_sma"])) if row["short_sma"] is not None else None,
        long_sma=Decimal(str(row["long_sma"])) if row["long_sma"] is not None else None,
        desired_position=int(row["desired_position"]),
        applied_position=int(row["applied_position"]),
        gross_return=Decimal(str(row["gross_return"])),
        cost_return=Decimal(str(row["cost_return"])),
        net_return=Decimal(str(row["net_return"])),
        equity=Decimal(str(row["equity"])),
        benchmark_equity=Decimal(str(row["benchmark_equity"])),
        drawdown=Decimal(str(row["drawdown"])),
    )


def _aware_utc(value):  # type: ignore[no-untyped-def]
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


def _detail_prefix(root_prefix: str, run_id: str) -> str:
    return f"{root_prefix}/run_id={run_id}/detail".strip("/")


if __name__ == "__main__":
    main()
