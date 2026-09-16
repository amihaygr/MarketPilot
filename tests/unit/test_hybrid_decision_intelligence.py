from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from marketpilot.decision_intelligence.hybrid import (
    PriceBar,
    ValidationMetrics,
    evaluate_promotion,
    expected_r,
    hybrid_action,
    label_recommendation_path,
)


def bar(minute: int, *, high: str, low: str, close: str) -> PriceBar:
    return PriceBar(
        datetime(2026, 1, 2, 14, 30, tzinfo=UTC) + timedelta(minutes=minute),
        Decimal(high),
        Decimal(low),
        Decimal(close),
    )


def test_label_requires_entry_and_is_conservative_when_stop_and_target_share_bar():
    no_entry = label_recommendation_path(
        zone_low=Decimal("99"),
        zone_high=Decimal("100"),
        stop=Decimal("97"),
        target_1=Decimal("106"),
        target_2=Decimal("109"),
        entry_window_bars=[bar(0, high="102", low="101", close="101.5")],
        outcome_bars=[],
    )
    assert no_entry.outcome == "NO_ENTRY"
    assert no_entry.target_before_stop is None

    result = label_recommendation_path(
        zone_low=Decimal("99"),
        zone_high=Decimal("100"),
        stop=Decimal("97"),
        target_1=Decimal("106"),
        target_2=Decimal("109"),
        entry_window_bars=[bar(0, high="100.2", low="99.5", close="100")],
        outcome_bars=[bar(1, high="106.5", low="96.5", close="102")],
    )
    assert result.outcome == "STOP"
    assert result.target_before_stop == 0


@pytest.mark.parametrize(
    ("outcome_bars", "expected_outcome", "expected_label"),
    [
        ([bar(1, high="106.5", low="98", close="106")], "TARGET_1", 1),
        ([bar(1, high="102", low="96.5", close="97")], "STOP", 0),
        ([bar(1, high="102", low="98", close="101")], "EXPIRED", 0),
    ],
)
def test_label_distinguishes_target_stop_and_expiry(
    outcome_bars: list[PriceBar], expected_outcome: str, expected_label: int
):
    result = label_recommendation_path(
        zone_low=Decimal("99"),
        zone_high=Decimal("100"),
        stop=Decimal("97"),
        target_1=Decimal("106"),
        target_2=Decimal("109"),
        entry_window_bars=[bar(0, high="100.2", low="99.5", close="100")],
        outcome_bars=outcome_bars,
    )
    assert result.outcome == expected_outcome
    assert result.target_before_stop == expected_label


def test_expected_r_and_preview_preserve_rules():
    assert expected_r(Decimal("0.60")) == Decimal("0.8000")
    assert (
        hybrid_action(
            rules_action="BUY ZONE",
            model_status="PREVIEW",
            success_probability=Decimal("0.1"),
            activation_threshold=Decimal("0.6"),
            price=Decimal("100"),
            zone_low=Decimal("99"),
            zone_high=Decimal("101"),
        )
        == "BUY ZONE"
    )
    assert (
        hybrid_action(
            rules_action="BUY ZONE",
            model_status="ACTIVE",
            success_probability=Decimal("0.59"),
            activation_threshold=Decimal("0.6"),
            price=Decimal("100"),
            zone_low=Decimal("99"),
            zone_high=Decimal("101"),
        )
        == "WAIT"
    )


def test_promotion_gate_reports_every_failed_requirement():
    decision = evaluate_promotion(
        ValidationMetrics(
            entered_samples=10,
            positive_samples=2,
            symbol_count=2,
            quarter_count=1,
            brier_score=Decimal("0.30"),
            baseline_brier_score=Decimal("0.25"),
            pr_auc=Decimal("0.1"),
            positive_rate=Decimal("0.2"),
            expected_calibration_error=Decimal("0.2"),
            mean_realized_r=Decimal("-0.1"),
            largest_symbol_profit_share=Decimal("0.8"),
            worst_fold_mean_r=Decimal("-0.5"),
        )
    )
    assert decision.eligible is False
    assert len(decision.reasons) == 10
