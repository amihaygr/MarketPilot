"""Versioned, explainable swing-trade decision-support calculations.

These rules produce research scenarios, never orders or promised returns.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from decimal import ROUND_FLOOR, Decimal
from typing import Literal
from zoneinfo import ZoneInfo

COMPAT_UTC = timezone.utc  # noqa: UP017 -- also imported by Spark's Python 3.10 runtime.

Action = Literal["BUY ZONE", "WAIT", "WATCH BREAKOUT", "AVOID", "INSUFFICIENT DATA"]
MODEL_VERSION = "decision-intelligence-v1"


@dataclass(frozen=True, slots=True)
class PortfolioRisk:
    equity: Decimal
    current_symbol_exposure: Decimal = Decimal("0")
    current_open_risk: Decimal = Decimal("0")
    risk_per_trade_pct: Decimal = Decimal("2")
    max_symbol_exposure_pct: Decimal = Decimal("20")
    max_open_risk_pct: Decimal = Decimal("6")


@dataclass(frozen=True, slots=True)
class DecisionInputs:
    symbol: str
    as_of_utc: datetime
    market_data_time_utc: datetime
    fundamentals_as_of_utc: datetime | None
    price: Decimal
    ema20: Decimal
    ema50: Decimal
    atr14: Decimal
    rsi14: Decimal
    macd_histogram: Decimal
    support: Decimal
    resistance_1: Decimal
    resistance_2: Decimal
    volume_ratio: Decimal
    relative_strength_spy: Decimal
    daily_trend: int
    hourly_trend: int
    revenue_growth_pct: Decimal | None
    eps_growth_pct: Decimal | None
    fcf_growth_pct: Decimal | None
    net_margin_pct: Decimal | None
    debt_to_equity: Decimal | None
    dilution_pct: Decimal | None
    feed: str = "iex"
    certification_status: Literal["PROVISIONAL", "CERTIFIED"] = "PROVISIONAL"
    shadow_mode: bool = True
    five_minute_trend: int = 0


@dataclass(frozen=True, slots=True)
class DecisionOutput:
    action: Action
    actionable: bool
    technical_score: Decimal
    fundamental_score: Decimal
    opportunity_score: Decimal
    confidence: Decimal
    buy_zone_low: Decimal
    buy_zone_high: Decimal
    stop_price: Decimal
    target_1: Decimal
    target_2: Decimal
    risk_reward_1: Decimal
    risk_reward_2: Decimal
    potential_profit_1_pct: Decimal
    potential_profit_2_pct: Decimal
    position_shares: int
    position_value: Decimal
    planned_risk: Decimal
    valid_until_utc: datetime
    model_version: str
    explanation_he: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


def _clamp(value: Decimal, low: Decimal = Decimal("0"), high: Decimal = Decimal("100")) -> Decimal:
    return min(high, max(low, value))


def _q(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"))


def _market_is_open(moment_utc: datetime) -> bool:
    local = moment_utc.astimezone(ZoneInfo("America/New_York"))
    minutes = local.hour * 60 + local.minute
    return local.weekday() < 5 and 9 * 60 + 30 <= minutes < 16 * 60


def _technical_score(data: DecisionInputs) -> Decimal:
    score = Decimal("50")
    score += Decimal(data.daily_trend) * Decimal("12")
    score += Decimal(data.hourly_trend) * Decimal("8")
    score += Decimal(data.five_minute_trend) * Decimal("3")
    score += Decimal("8") if data.ema20 > data.ema50 else Decimal("-8")
    score += Decimal("5") if data.macd_histogram > 0 else Decimal("-5")
    score += Decimal("5") if Decimal("40") <= data.rsi14 <= Decimal("65") else Decimal("-4")
    score += _clamp((data.volume_ratio - 1) * 5, Decimal("-5"), Decimal("5"))
    score += _clamp(data.relative_strength_spy * 2, Decimal("-5"), Decimal("5"))
    return _q(_clamp(score))


def _fundamental_score(data: DecisionInputs) -> Decimal | None:
    values = (data.revenue_growth_pct, data.eps_growth_pct, data.fcf_growth_pct)
    if any(value is None for value in values) or data.net_margin_pct is None:
        return None
    score = Decimal("50")
    score += _clamp(data.revenue_growth_pct or Decimal(), Decimal("-20"), Decimal("20")) * Decimal(
        "0.5"
    )
    score += _clamp(data.eps_growth_pct or Decimal(), Decimal("-25"), Decimal("25")) * Decimal(
        "0.4"
    )
    score += _clamp(data.fcf_growth_pct or Decimal(), Decimal("-20"), Decimal("20")) * Decimal(
        "0.3"
    )
    score += _clamp(data.net_margin_pct or Decimal(), Decimal("-10"), Decimal("25")) * Decimal(
        "0.4"
    )
    score -= _clamp((data.debt_to_equity or Decimal()) - 1, Decimal("0"), Decimal("3")) * 5
    score -= _clamp(data.dilution_pct or Decimal(), Decimal("0"), Decimal("20")) * Decimal("0.5")
    return _q(_clamp(score))


def build_decision(data: DecisionInputs, portfolio: PortfolioRisk) -> DecisionOutput:
    """Calculate a transparent scenario and enforce freshness/risk gates."""
    if data.as_of_utc.tzinfo is None or data.market_data_time_utc.tzinfo is None:
        raise ValueError("timestamps must be timezone-aware")
    if min(data.price, data.ema20, data.ema50, data.atr14, data.support) <= 0:
        raise ValueError("price inputs must be positive")

    technical = _technical_score(data)
    fundamental = _fundamental_score(data)
    fundamentals_stale = (
        data.fundamentals_as_of_utc is None
        or data.fundamentals_as_of_utc.tzinfo is None
        or data.as_of_utc - data.fundamentals_as_of_utc > timedelta(days=150)
    )
    market_stale = _market_is_open(data.as_of_utc) and (
        data.as_of_utc - data.market_data_time_utc > timedelta(minutes=30)
    )
    complete = fundamental is not None and not fundamentals_stale
    combined = _q((technical + (fundamental or Decimal())) / 2) if complete else technical

    zone_anchor = max(data.support, min(data.ema20, data.price))
    zone_low = _q(max(Decimal("0.01"), zone_anchor - data.atr14 * Decimal("0.35")))
    zone_high = _q(zone_anchor + data.atr14 * Decimal("0.25"))
    entry = (zone_low + zone_high) / 2
    stop = _q(min(data.support - data.atr14 * Decimal("0.25"), entry - data.atr14 * Decimal("1.5")))
    per_share_risk = max(Decimal("0.01"), entry - stop)
    target_1 = _q(max(data.resistance_1, entry + per_share_risk * 2))
    target_2 = _q(max(data.resistance_2, entry + per_share_risk * 3))
    rr1 = _q((target_1 - entry) / per_share_risk)
    rr2 = _q((target_2 - entry) / per_share_risk)

    feed_factor = Decimal("0.85") if data.feed.lower() == "iex" else Decimal("1")
    certification_factor = (
        Decimal("0.9") if data.certification_status == "PROVISIONAL" else Decimal("1")
    )
    confidence = _q(_clamp(combined * feed_factor * certification_factor))

    risk_budget = portfolio.equity * portfolio.risk_per_trade_pct / 100
    exposure_budget = max(
        Decimal("0"),
        portfolio.equity * portfolio.max_symbol_exposure_pct / 100
        - portfolio.current_symbol_exposure,
    )
    open_risk_budget = max(
        Decimal("0"),
        portfolio.equity * portfolio.max_open_risk_pct / 100 - portfolio.current_open_risk,
    )
    allowed_risk = min(risk_budget, open_risk_budget)
    shares_by_risk = int((allowed_risk / per_share_risk).to_integral_value(rounding=ROUND_FLOOR))
    shares_by_exposure = int((exposure_budget / entry).to_integral_value(rounding=ROUND_FLOOR))
    shares = max(0, min(shares_by_risk, shares_by_exposure))

    in_zone = zone_low <= data.price <= zone_high
    if market_stale or not complete:
        action: Action = "INSUFFICIENT DATA"
    elif combined < 45 or technical < 40:
        action = "AVOID"
    elif rr1 < 2 or confidence < 55 or shares == 0:
        action = "WAIT"
    elif data.price > zone_high:
        action = "WATCH BREAKOUT"
    elif in_zone:
        action = "BUY ZONE"
    else:
        action = "WAIT"

    actionable = action == "BUY ZONE" and not data.shadow_mode
    explanations = [
        f"הציון הטכני הוא {technical}/100 והציון המשולב הוא {combined}/100.",
        f"טווח הכניסה נגזר מתמיכה, EMA 20 ו-ATR 14; יחס הסיכון/סיכוי ליעד הראשון הוא {rr1}.",
        "מקור IEX הוא חלקי ולכן מפחית את רמת הביטחון."
        if data.feed.lower() == "iex"
        else "מקור השוק הוא SIP מלא.",
    ]
    if market_stale:
        explanations.append("נתוני המחיר ישנים מ-30 דקות ולכן ההמלצה חסומה.")
    if fundamentals_stale or fundamental is None:
        explanations.append("הנתונים הפונדמנטליים חסרים או ישנים מ-150 ימים.")
    if data.shadow_mode:
        explanations.append("המערכת ב-Shadow Mode: הפלט מיועד להערכה ואינו actionable.")

    return DecisionOutput(
        action=action,
        actionable=actionable,
        technical_score=technical,
        fundamental_score=fundamental or Decimal("0"),
        opportunity_score=combined,
        confidence=confidence,
        buy_zone_low=zone_low,
        buy_zone_high=zone_high,
        stop_price=stop,
        target_1=target_1,
        target_2=target_2,
        risk_reward_1=rr1,
        risk_reward_2=rr2,
        potential_profit_1_pct=_q((target_1 / entry - 1) * 100),
        potential_profit_2_pct=_q((target_2 / entry - 1) * 100),
        position_shares=shares,
        position_value=_q(entry * shares),
        planned_risk=_q(per_share_risk * shares),
        valid_until_utc=(
            data.market_data_time_utc.astimezone(COMPAT_UTC) + timedelta(minutes=30)
            if _market_is_open(data.as_of_utc)
            else data.as_of_utc.astimezone(COMPAT_UTC) + timedelta(days=1)
        ),
        model_version=MODEL_VERSION,
        explanation_he=tuple(explanations),
    )
