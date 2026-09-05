from pathlib import Path

import pytest

from marketpilot.orchestration.backtest_scope import prepare_backtest_arguments
from marketpilot.orchestration.batch_scope import (
    configured_market_symbols,
    prepare_backfill_arguments,
    prepare_daily_scope,
)
from marketpilot.orchestration.historical_scope import prepare_historical_backfill_plan

ROOT = Path(__file__).resolve().parents[2]
CONFIGURED = ("AAPL", "MSFT", "SPY")


def test_daily_scope_uses_xnys_calendar_and_stable_retry_run_id() -> None:
    first = prepare_daily_scope("2026-08-24", "scheduled__2026-08-24")
    retry = prepare_daily_scope("2026-08-24", "scheduled__2026-08-24")

    assert first == retry
    assert first is not None
    assert first["expected_bars_per_symbol"] == 390


def test_daily_scope_short_circuits_weekend_unless_explicitly_overridden() -> None:
    assert prepare_daily_scope("2026-08-22", "manual__weekend") is None
    forced = prepare_daily_scope("2026-08-22", "manual__weekend", 171)
    assert forced is not None
    assert forced["expected_bars_per_symbol"] == 171


def test_backfill_builds_ordered_mapped_arguments_for_sessions_and_symbol_subset() -> None:
    arguments = prepare_backfill_arguments(
        start_date_value="2026-08-21",
        end_date_value="2026-08-24",
        requested_symbols=["SPY", "AAPL"],
        configured_symbols=CONFIGURED,
        airflow_run_id="manual__range",
    )

    assert len(arguments["bronze"]) == 2
    assert len(arguments["quality"]) == 2
    assert len(arguments["gold"]) == 2
    assert "2026-08-21" in arguments["bronze"][0]
    assert "2026-08-24" in arguments["bronze"][1]
    assert '["AAPL","SPY"]' in arguments["bronze"][0]
    assert "2026-08-21|symbols=AAPL,SPY" in arguments["quality"][0]


def test_backfill_rejects_unbounded_or_unknown_scope() -> None:
    with pytest.raises(ValueError, match="31 calendar days"):
        prepare_backfill_arguments(
            start_date_value="2026-01-01",
            end_date_value="2026-02-01",
            requested_symbols=["SPY"],
            configured_symbols=CONFIGURED,
            airflow_run_id="manual__too-wide",
        )
    with pytest.raises(ValueError, match="outside MARKET_SYMBOLS"):
        prepare_backfill_arguments(
            start_date_value="2026-08-24",
            end_date_value="2026-08-24",
            requested_symbols=["INVALID"],
            configured_symbols=CONFIGURED,
            airflow_run_id="manual__unknown",
        )


def test_configured_symbols_are_normalized_and_non_empty() -> None:
    assert configured_market_symbols(" spy,AAPL,spy ") == ("AAPL", "SPY")
    with pytest.raises(ValueError, match="at least one symbol"):
        configured_market_symbols(" , ")


def test_backtest_arguments_are_bounded_validated_and_retry_stable() -> None:
    values = {
        "start_date_value": "2026-08-21",
        "end_date_value": "2026-08-24",
        "requested_symbols": ["AAPL", "SPY"],
        "benchmark_symbol": "SPY",
        "short_window": 20,
        "long_window": 50,
        "initial_capital": "10000",
        "transaction_cost_bps": "1",
        "slippage_bps": "1",
        "configured_symbols_value": "AAPL,MSFT,SPY",
        "airflow_run_id": "manual__phase11",
    }
    first = prepare_backtest_arguments(**values)
    assert first == prepare_backtest_arguments(**values)
    assert "--run-id" in first
    assert "AAPL,SPY" in first

    values["requested_symbols"] = ["UNKNOWN"]
    with pytest.raises(ValueError, match="outside MARKET_SYMBOLS"):
        prepare_backtest_arguments(**values)


def test_airflow_dags_never_launch_or_reference_streaming_application() -> None:
    dag_sources = "\n".join(
        path.read_text(encoding="utf-8") for path in (ROOT / "airflow" / "dags").glob("*.py")
    )
    assert "SparkSubmitOperator" in dag_sources
    assert "stream_market_bars.py" not in dag_sources
    assert "docker compose" not in dag_sources.lower()
    assert "docker.sock" not in dag_sources.lower()


def test_sec_dag_is_bounded_and_rate_limited_by_pool() -> None:
    source = (ROOT / "airflow" / "dags" / "sec_polling.py").read_text(encoding="utf-8")
    assert 'schedule="*/15 6-22 * * 1-5"' in source
    assert "catchup=False" in source
    assert "max_active_runs=1" in source
    assert 'pool="sec_api_pool"' in source


def test_historical_plan_is_bounded_coverage_aware_and_retry_stable() -> None:
    values = {
        "start_date_value": "2026-08-21",
        "end_date_value": "2026-08-24",
        "requested_symbols": ["AAPL", "SPY"],
        "benchmark_symbol": "SPY",
        "configured_symbols": CONFIGURED,
        "airflow_run_id": "manual__historical",
        "minimum_coverage_pct": 80,
        "maximum_ingestion_lag_seconds": 60_000_000,
        "short_window": 20,
        "long_window": 50,
        "initial_capital": "10000",
        "transaction_cost_bps": "1",
        "slippage_bps": "1",
    }
    plan = prepare_historical_backfill_plan(**values)
    assert plan == prepare_historical_backfill_plan(**values)
    assert len(plan["ingestion"]) == 2
    assert plan["ingestion"][0]["session_date"] == "2026-08-21"
    assert "logical_date" not in plan["ingestion"][0]
    assert "312" in plan["quality"][0]
    assert "--maximum-ingestion-lag-seconds" in plan["quality"][0]
    assert plan["ingestion"][0]["run_id"] == plan["bronze"][0][3]

    values["benchmark_symbol"] = "MSFT"
    with pytest.raises(ValueError, match="included in symbols"):
        prepare_historical_backfill_plan(**values)


def test_historical_dag_is_manual_serial_and_uses_bronze_barrier() -> None:
    source = (ROOT / "airflow" / "dags" / "historical_market_backfill.py").read_text(
        encoding="utf-8"
    )
    assert 'dag_id="historical_market_backfill"' in source
    assert "schedule=None" in source
    assert "max_active_runs=1" in source
    assert 'pool="alpaca_api_pool"' in source
    assert "backfill_historical_session_from_env" in source
    assert "bronze_to_silver >> silver_quality_gate >> silver_to_gold >> run_backtest" in source
