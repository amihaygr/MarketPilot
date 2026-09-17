import pytest

from marketpilot.batch.quality import (
    QUALITY_CHECK_NAMES,
    QualityMetrics,
    QualityPolicy,
    evaluate_quality_gate,
    quality_gate_passed,
)


def healthy_metrics() -> QualityMetrics:
    return QualityMetrics(
        total_rows=6,
        distinct_business_keys=6,
        required_null_rows=0,
        invalid_ohlc_rows=0,
        wrong_logical_date_rows=0,
        invalid_schema_rows=0,
        event_after_ingestion_rows=0,
        maximum_ingestion_lag_seconds=2,
        rows_by_symbol={"AAPL": 3, "SPY": 3},
    )


def test_all_quality_checks_pass_for_complete_canonical_partition() -> None:
    results = evaluate_quality_gate(
        healthy_metrics(),
        QualityPolicy(
            expected_symbols=("AAPL", "SPY"),
            expected_bars_per_symbol=3,
            expected_total_bars=6,
            maximum_ingestion_lag_seconds=5,
        ),
    )

    assert tuple(result.check_name for result in results) == QUALITY_CHECK_NAMES
    assert quality_gate_passed(results)
    assert {result.status for result in results} == {"PASS"}


def test_quality_gate_reports_every_blocking_failure() -> None:
    metrics = QualityMetrics(
        total_rows=2,
        distinct_business_keys=1,
        required_null_rows=1,
        invalid_ohlc_rows=1,
        wrong_logical_date_rows=1,
        invalid_schema_rows=1,
        event_after_ingestion_rows=1,
        maximum_ingestion_lag_seconds=90,
        rows_by_symbol={"AAPL": 2},
    )
    results = evaluate_quality_gate(
        metrics,
        QualityPolicy(
            expected_symbols=("AAPL", "SPY"),
            expected_bars_per_symbol=3,
            expected_total_bars=6,
            maximum_ingestion_lag_seconds=5,
        ),
    )

    failed = {result.check_name for result in results if result.status == "FAIL"}
    assert failed == set(QUALITY_CHECK_NAMES) - {"non_empty"}
    assert not quality_gate_passed(results)


@pytest.mark.parametrize(
    ("expected_bars", "maximum_lag"),
    [(0, 5), (1, -1)],
)
def test_quality_policy_rejects_invalid_thresholds(
    expected_bars: int,
    maximum_lag: int,
) -> None:
    with pytest.raises(ValueError):
        QualityPolicy(
            expected_symbols=("AAPL",),
            expected_bars_per_symbol=expected_bars,
            expected_total_bars=1,
            maximum_ingestion_lag_seconds=maximum_lag,
        )


def test_quality_gate_blocks_weak_aggregate_coverage_even_when_each_symbol_floor_passes() -> None:
    metrics = healthy_metrics()
    results = evaluate_quality_gate(
        metrics,
        QualityPolicy(
            expected_symbols=("AAPL", "SPY"),
            expected_bars_per_symbol=2,
            expected_total_bars=7,
            maximum_ingestion_lag_seconds=5,
        ),
    )

    status = {result.check_name: result.status for result in results}
    assert status["expected_market_bars"] == "PASS"
    assert status["aggregate_market_bars"] == "FAIL"
    assert not quality_gate_passed(results)


def test_feed_aware_iex_policy_accepts_sparse_symbol_with_strong_universe_coverage() -> None:
    rows_by_symbol = {
        "AAPL": 388,
        "AMZN": 389,
        "GOOGL": 360,
        "JPM": 339,
        "META": 327,
        "MSFT": 356,
        "NVDA": 390,
        "SPY": 380,
        "TSLA": 384,
        "UNH": 177,
        "XOM": 343,
    }
    total_rows = sum(rows_by_symbol.values())
    metrics = QualityMetrics(
        total_rows=total_rows,
        distinct_business_keys=total_rows,
        required_null_rows=0,
        invalid_ohlc_rows=0,
        wrong_logical_date_rows=0,
        invalid_schema_rows=0,
        event_after_ingestion_rows=0,
        maximum_ingestion_lag_seconds=1,
        rows_by_symbol=rows_by_symbol,
    )

    results = evaluate_quality_gate(
        metrics,
        QualityPolicy(
            expected_symbols=tuple(sorted(rows_by_symbol)),
            expected_bars_per_symbol=137,
            expected_total_bars=3432,
            maximum_ingestion_lag_seconds=5,
        ),
    )

    assert quality_gate_passed(results)
