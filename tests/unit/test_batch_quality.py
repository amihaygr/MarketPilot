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
            maximum_ingestion_lag_seconds=maximum_lag,
        )
