"""Transactional publication of bounded Phase 11 Gold read models."""

from __future__ import annotations

from datetime import timezone
from typing import Any

import pymysql

from marketpilot.backtesting.rules import (
    BACKTEST_SCHEMA_VERSION,
    STRATEGY_CODE,
    STRATEGY_VERSION,
    BacktestResult,
    BacktestScope,
    daily_equity_points,
)
from marketpilot.streaming.mariadb_sink import MariaDbConfig

UTC = timezone.utc  # noqa: UP017 -- imported by Spark 3.5.8 on Python 3.10.


def publish_backtest(
    config: MariaDbConfig,
    *,
    scope: BacktestScope,
    results: list[BacktestResult],
    detailed_output_uri: str,
    code_version: str,
    data_version: str,
) -> tuple[int, int]:
    if not results:
        raise ValueError("backtest publication requires at least one result")
    if {result.symbol for result in results} != set(scope.symbols):
        raise ValueError("published backtest symbols do not match requested scope")
    daily_points = [
        (result, point) for result in results for point in daily_equity_points(result.curve)
    ]
    connection = pymysql.connect(
        host=config.host,
        port=config.port,
        database=config.database,
        user=config.user,
        password=config.password,
        charset="utf8mb4",
        autocommit=False,
    )
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM fact_backtest_run WHERE run_id=%s FOR UPDATE",
                (scope.run_id,),
            )
            existing = cursor.fetchone()
            if existing is not None:
                _validate_existing_scope(existing, scope)
            cursor.execute(
                """
                INSERT INTO fact_backtest_run (
                    run_id, strategy_code, strategy_version, start_date, end_date,
                    symbols_csv, benchmark_symbol, short_window, long_window,
                    initial_capital, transaction_cost_bps, slippage_bps, status,
                    detailed_output_uri, code_version, data_version, schema_version,
                    completed_at_utc
                ) VALUES (
                    %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
                    'PUBLISHED',%s,%s,%s,%s,UTC_TIMESTAMP(6)
                )
                ON DUPLICATE KEY UPDATE
                    status='PUBLISHED', detailed_output_uri=VALUES(detailed_output_uri),
                    error_message=NULL, code_version=VALUES(code_version),
                    data_version=VALUES(data_version), schema_version=VALUES(schema_version),
                    completed_at_utc=UTC_TIMESTAMP(6)
                """,
                (
                    scope.run_id,
                    STRATEGY_CODE,
                    STRATEGY_VERSION,
                    scope.start_date,
                    scope.end_date,
                    ",".join(scope.symbols),
                    scope.benchmark_symbol,
                    scope.short_window,
                    scope.long_window,
                    scope.initial_capital,
                    scope.transaction_cost_bps,
                    scope.slippage_bps,
                    detailed_output_uri,
                    code_version,
                    data_version,
                    BACKTEST_SCHEMA_VERSION,
                ),
            )
            cursor.execute(
                "DELETE FROM fact_backtest_equity_daily WHERE run_id=%s",
                (scope.run_id,),
            )
            cursor.execute("DELETE FROM fact_backtest_result WHERE run_id=%s", (scope.run_id,))
            cursor.executemany(
                """
                INSERT INTO fact_backtest_result (
                    run_id, symbol_id, first_event_time_utc, last_event_time_utc,
                    observation_count, trade_count, total_return_pct,
                    benchmark_return_pct, excess_return_pct, max_drawdown_pct,
                    annualized_volatility_pct, sharpe_ratio
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """,
                [
                    (
                        scope.run_id,
                        result.symbol_id,
                        _database_time(result.first_event_time_utc),
                        _database_time(result.last_event_time_utc),
                        result.observation_count,
                        result.trade_count,
                        result.total_return_pct,
                        result.benchmark_return_pct,
                        result.excess_return_pct,
                        result.max_drawdown_pct,
                        result.annualized_volatility_pct,
                        result.sharpe_ratio,
                    )
                    for result in results
                ],
            )
            cursor.executemany(
                """
                INSERT INTO fact_backtest_equity_daily (
                    run_id, symbol_id, trading_date, event_time_utc, equity,
                    benchmark_equity, drawdown_pct, applied_position
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                """,
                [
                    (
                        scope.run_id,
                        result.symbol_id,
                        point.event_time_utc.date(),
                        _database_time(point.event_time_utc),
                        point.equity,
                        point.benchmark_equity,
                        point.drawdown * 100,
                        point.applied_position,
                    )
                    for result, point in daily_points
                ],
            )
            cursor.execute(
                """
                INSERT INTO etl_watermark (
                    pipeline_name, partition_key, watermark_utc, status, run_id
                ) VALUES (
                    'historical_backtest', %s, UTC_TIMESTAMP(6), 'PUBLISHED', %s
                )
                ON DUPLICATE KEY UPDATE watermark_utc=VALUES(watermark_utc),
                    status='PUBLISHED', run_id=VALUES(run_id),
                    updated_at_utc=UTC_TIMESTAMP(6)
                """,
                (scope.run_id, scope.run_id),
            )
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
    return len(results), len(daily_points)


def _validate_existing_scope(row: Any, scope: BacktestScope) -> None:
    values = tuple(row) if not isinstance(row, dict) else ()
    if values:
        expected = (
            STRATEGY_CODE,
            STRATEGY_VERSION,
            scope.start_date,
            scope.end_date,
            ",".join(scope.symbols),
            scope.benchmark_symbol,
            scope.short_window,
            scope.long_window,
        )
        actual = (
            values[1],
            values[2],
            values[3],
            values[4],
            values[5],
            values[6],
            values[7],
            values[8],
        )
    else:
        expected = (
            STRATEGY_CODE,
            STRATEGY_VERSION,
            scope.start_date,
            scope.end_date,
            ",".join(scope.symbols),
            scope.benchmark_symbol,
            scope.short_window,
            scope.long_window,
        )
        actual = tuple(
            row[key]
            for key in (
                "strategy_code",
                "strategy_version",
                "start_date",
                "end_date",
                "symbols_csv",
                "benchmark_symbol",
                "short_window",
                "long_window",
            )
        )
    if actual != expected:
        raise ValueError("run ID already exists with different immutable backtest parameters")


def _database_time(value):  # type: ignore[no-untyped-def]
    return value.astimezone(UTC).replace(tzinfo=None)
