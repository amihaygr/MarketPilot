from decimal import Decimal

from marketpilot.decision_intelligence.evaluation import evaluate_path


def test_evaluation_uses_conservative_intrabar_outcome() -> None:
    result = evaluate_path(
        entry=Decimal("100"),
        target_1=Decimal("110"),
        target_2=Decimal("120"),
        stop=Decimal("95"),
        bars=[{"high_price": 112, "low_price": 94, "close_price": 108}],
    )

    assert result.target_1_hit is True
    assert result.stop_hit is True
    assert result.outcome == "STOP"
    assert result.realized_return_pct == Decimal("8.00")


def test_evaluation_reports_target_two_and_excursions() -> None:
    result = evaluate_path(
        entry=Decimal("100"),
        target_1=Decimal("110"),
        target_2=Decimal("120"),
        stop=Decimal("90"),
        bars=[
            {"high_price": 111, "low_price": 98, "close_price": 109},
            {"high_price": 122, "low_price": 105, "close_price": 121},
        ],
    )

    assert result.outcome == "TARGET_2"
    assert result.max_favorable_excursion_pct == Decimal("22.00")
    assert result.max_adverse_excursion_pct == Decimal("-2.00")
