"""Materialize finite, retry-stable Airflow arguments for Phase 11."""

from __future__ import annotations

from uuid import NAMESPACE_URL, uuid5

from marketpilot.backtesting.rules import resolve_backtest_scope
from marketpilot.orchestration.batch_scope import configured_market_symbols


def prepare_backtest_arguments(
    *,
    start_date_value: str,
    end_date_value: str,
    requested_symbols: list[str],
    benchmark_symbol: str,
    short_window: int,
    long_window: int,
    initial_capital: str,
    transaction_cost_bps: str,
    slippage_bps: str,
    configured_symbols_value: str,
    airflow_run_id: str,
) -> list[str]:
    configured = set(configured_market_symbols(configured_symbols_value))
    normalized = sorted({str(symbol).strip().upper() for symbol in requested_symbols})
    benchmark = benchmark_symbol.strip().upper()
    unknown = (set(normalized) | {benchmark}) - configured
    if unknown:
        raise ValueError(f"backtest symbols outside MARKET_SYMBOLS: {','.join(sorted(unknown))}")
    stable_run_id = str(
        uuid5(
            NAMESPACE_URL,
            "marketpilot:backtest:"
            f"{airflow_run_id}:{start_date_value}:{end_date_value}:{','.join(normalized)}:"
            f"{benchmark}:{short_window}:{long_window}:{initial_capital}:"
            f"{transaction_cost_bps}:{slippage_bps}",
        )
    )
    scope = resolve_backtest_scope(
        run_id=stable_run_id,
        start_date_value=start_date_value,
        end_date_value=end_date_value,
        symbols_value=",".join(normalized),
        benchmark_symbol=benchmark,
        short_window=int(short_window),
        long_window=int(long_window),
        initial_capital=str(initial_capital),
        transaction_cost_bps=str(transaction_cost_bps),
        slippage_bps=str(slippage_bps),
    )
    return [
        "--run-id",
        scope.run_id,
        "--start-date",
        scope.start_date.isoformat(),
        "--end-date",
        scope.end_date.isoformat(),
        "--symbols",
        ",".join(scope.symbols),
        "--benchmark-symbol",
        scope.benchmark_symbol,
        "--short-window",
        str(scope.short_window),
        "--long-window",
        str(scope.long_window),
        "--initial-capital",
        str(scope.initial_capital),
        "--transaction-cost-bps",
        str(scope.transaction_cost_bps),
        "--slippage-bps",
        str(scope.slippage_bps),
    ]
