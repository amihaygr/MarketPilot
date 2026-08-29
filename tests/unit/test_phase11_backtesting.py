from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

import pytest

from marketpilot.backtesting.rules import (
    PriceBar,
    daily_equity_points,
    resolve_backtest_scope,
    run_long_cash_backtest,
)


def _scope(**overrides):
    values = {
        "run_id": str(uuid4()),
        "start_date_value": "2026-08-01",
        "end_date_value": "2026-08-02",
        "symbols_value": "AAPL",
        "short_window": 2,
        "long_window": 3,
        "initial_capital": "10000",
        "transaction_cost_bps": "1",
        "slippage_bps": "1",
    }
    values.update(overrides)
    return resolve_backtest_scope(**values)


def _bars(prices: list[str]) -> list[PriceBar]:
    start = datetime(2026, 8, 1, 14, 30, tzinfo=UTC)
    return [
        PriceBar(1, "AAPL", start + timedelta(minutes=index), Decimal(price))
        for index, price in enumerate(prices)
    ]


def test_scope_rejects_unbounded_or_invalid_parameters() -> None:
    with pytest.raises(ValueError, match="must satisfy"):
        _scope(short_window=20, long_window=20)
    with pytest.raises(ValueError, match="cannot exceed"):
        _scope(end_date_value="2028-08-02")
    with pytest.raises(ValueError, match="positive"):
        _scope(initial_capital="0")


def test_signal_is_applied_only_to_the_following_bar_return() -> None:
    scope = _scope(transaction_cost_bps="0", slippage_bps="0")
    result = run_long_cash_backtest(_bars(["10", "9", "8", "12", "18"]), scope)

    crossover_point = result.curve[2]
    following_point = result.curve[3]
    assert crossover_point.desired_position == 1
    assert crossover_point.applied_position == 0
    assert crossover_point.net_return == 0
    assert following_point.applied_position == 1
    assert following_point.net_return == Decimal("0.5")


def test_costs_and_idempotent_daily_projection_are_explicit() -> None:
    scope = _scope(transaction_cost_bps="10", slippage_bps="5")
    result = run_long_cash_backtest(_bars(["10", "9", "8", "12", "18"]), scope)

    entry = result.curve[-1]
    assert entry.cost_return == Decimal("0.0015")
    assert result.trade_count == 1
    assert daily_equity_points(result.curve) == (result.curve[-1],)


def test_duplicate_timestamps_and_insufficient_history_are_rejected() -> None:
    scope = _scope()
    with pytest.raises(ValueError, match="enough bars"):
        run_long_cash_backtest(_bars(["10", "11", "12"]), scope)
    duplicated = _bars(["10", "11", "12", "13"])
    duplicated[-1] = PriceBar(1, "AAPL", duplicated[-2].event_time_utc, Decimal("13"))
    with pytest.raises(ValueError, match="duplicate"):
        run_long_cash_backtest(duplicated, scope)


def test_distributed_job_stays_on_native_spark_dataframe_execution() -> None:
    job = Path("spark/jobs/run_historical_backtest.py").read_text(encoding="utf-8")

    assert ".rdd" not in job
    assert "lag(" in job
