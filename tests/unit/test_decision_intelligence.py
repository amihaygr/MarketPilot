from datetime import UTC, datetime, timedelta
from decimal import Decimal

from marketpilot.decision_intelligence.rules import DecisionInputs, PortfolioRisk, build_decision


def inputs(**overrides):
    now = datetime(2026, 9, 13, 14, 0, tzinfo=UTC)
    values = dict(
        symbol="AAPL",
        as_of_utc=now,
        market_data_time_utc=now - timedelta(minutes=1),
        fundamentals_as_of_utc=now - timedelta(days=30),
        price=Decimal("100"),
        ema20=Decimal("100"),
        ema50=Decimal("95"),
        atr14=Decimal("2"),
        rsi14=Decimal("55"),
        macd_histogram=Decimal("1"),
        support=Decimal("99"),
        resistance_1=Decimal("104"),
        resistance_2=Decimal("108"),
        volume_ratio=Decimal("1.5"),
        relative_strength_spy=Decimal("2"),
        daily_trend=1,
        hourly_trend=1,
        revenue_growth_pct=Decimal("10"),
        eps_growth_pct=Decimal("12"),
        fcf_growth_pct=Decimal("8"),
        net_margin_pct=Decimal("20"),
        debt_to_equity=Decimal("0.5"),
        dilution_pct=Decimal("0"),
        shadow_mode=True,
    )
    values.update(overrides)
    return DecisionInputs(**values)


def test_decision_builds_reproducible_levels_and_shadow_gate():
    result = build_decision(inputs(), PortfolioRisk(equity=Decimal("10000")))
    assert result.action == "BUY ZONE"
    assert result.actionable is False
    assert result.risk_reward_1 >= 2
    assert result.position_shares > 0
    assert result.planned_risk <= Decimal("200")
    assert result.position_value <= Decimal("2000")


def test_stale_market_or_fundamentals_blocks_entry():
    now = datetime(2026, 9, 14, 14, 0, tzinfo=UTC)
    assert (
        build_decision(
            inputs(as_of_utc=now, market_data_time_utc=now - timedelta(minutes=31)),
            PortfolioRisk(equity=Decimal("10000")),
        ).action
        == "INSUFFICIENT DATA"
    )
    assert (
        build_decision(
            inputs(as_of_utc=now, fundamentals_as_of_utc=now - timedelta(days=151)),
            PortfolioRisk(equity=Decimal("10000")),
        ).action
        == "INSUFFICIENT DATA"
    )


def test_open_risk_and_exposure_limit_position_size():
    portfolio = PortfolioRisk(
        equity=Decimal("10000"),
        current_symbol_exposure=Decimal("1950"),
        current_open_risk=Decimal("590"),
    )
    result = build_decision(inputs(), portfolio)
    assert result.position_value <= Decimal("50")
    assert result.planned_risk <= Decimal("10")


def test_old_bar_does_not_expire_certified_research_while_market_is_closed():
    sunday = datetime(2026, 9, 13, 14, 0, tzinfo=UTC)
    result = build_decision(
        inputs(as_of_utc=sunday, market_data_time_utc=sunday - timedelta(days=2)),
        PortfolioRisk(equity=Decimal("10000")),
    )
    assert result.action != "INSUFFICIENT DATA"
