"""Build one finite acquisition-to-backtest plan for Phase 12."""

from __future__ import annotations

from typing import Any

from marketpilot.orchestration.backtest_scope import prepare_backtest_arguments
from marketpilot.orchestration.batch_scope import prepare_backfill_arguments


def prepare_historical_backfill_plan(
    *,
    start_date_value: str,
    end_date_value: str,
    requested_symbols: list[str],
    benchmark_symbol: str,
    configured_symbols: tuple[str, ...],
    airflow_run_id: str,
    minimum_coverage_pct: int,
    maximum_ingestion_lag_seconds: int,
    short_window: int,
    long_window: int,
    initial_capital: str,
    transaction_cost_bps: str,
    slippage_bps: str,
) -> dict[str, Any]:
    """Return retry-stable mapped tasks plus one final backtest application."""
    benchmark = benchmark_symbol.strip().upper()
    normalized = sorted({str(symbol).strip().upper() for symbol in requested_symbols})
    if benchmark not in normalized:
        raise ValueError("benchmark_symbol must be included in symbols")
    mapped = prepare_backfill_arguments(
        start_date_value=start_date_value,
        end_date_value=end_date_value,
        requested_symbols=normalized,
        configured_symbols=configured_symbols,
        airflow_run_id=airflow_run_id,
        minimum_coverage_pct=int(minimum_coverage_pct),
        maximum_ingestion_lag_seconds=int(maximum_ingestion_lag_seconds),
    )
    for bronze_args in mapped["bronze"]:
        bronze_args.extend(["--source-name", "alpaca"])
    ingestion = []
    for bronze_args in mapped["bronze"]:
        ingestion.append(
            {
                "session_date": bronze_args[1],
                "run_id": bronze_args[3],
                "symbols": normalized,
            }
        )
    backtest = prepare_backtest_arguments(
        start_date_value=start_date_value,
        end_date_value=end_date_value,
        requested_symbols=normalized,
        benchmark_symbol=benchmark,
        short_window=int(short_window),
        long_window=int(long_window),
        initial_capital=initial_capital,
        transaction_cost_bps=transaction_cost_bps,
        slippage_bps=slippage_bps,
        configured_symbols_value=",".join(configured_symbols),
        airflow_run_id=airflow_run_id,
    )
    return {**mapped, "ingestion": ingestion, "backtest": backtest}
