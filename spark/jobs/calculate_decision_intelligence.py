"""Bounded Spark-submit driver that publishes auditable Phase 14 shadow snapshots."""

from __future__ import annotations

import argparse
import json
import os
from datetime import UTC, datetime
from decimal import Decimal
from uuid import NAMESPACE_URL, uuid5

import pymysql
from pymysql.cursors import DictCursor

from marketpilot.decision_intelligence.rules import DecisionInputs, PortfolioRisk, build_decision


def _ema(values: list[Decimal], period: int) -> Decimal:
    alpha = Decimal(2) / Decimal(period + 1)
    result = values[0]
    for value in values[1:]:
        result = value * alpha + result * (1 - alpha)
    return result


def _rsi(values: list[Decimal], period: int = 14) -> Decimal:
    changes = [
        right - left for left, right in zip(values[-period - 1 : -1], values[-period:], strict=True)
    ]
    gains = sum((max(change, Decimal()) for change in changes), Decimal()) / period
    losses = sum((max(-change, Decimal()) for change in changes), Decimal()) / period
    return Decimal(100) if losses == 0 else Decimal(100) - Decimal(100) / (1 + gains / losses)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--as-of-utc")
    args = parser.parse_args()
    as_of = (
        datetime.fromisoformat(args.as_of_utc).astimezone(UTC)
        if args.as_of_utc
        else datetime.now(UTC)
    )
    connection = pymysql.connect(
        host=os.environ["MARIADB_HOST"],
        port=int(os.environ.get("MARIADB_PORT", "3306")),
        database=os.environ["MARIADB_DATABASE"],
        user=os.environ["MARIADB_PUBLISH_USER"],
        password=os.environ["MARIADB_PUBLISH_PASSWORD"],
        charset="utf8mb4",
        autocommit=False,
        cursorclass=DictCursor,
    )
    published = 0
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT portfolio_id, equity, risk_per_trade_pct,
                       max_symbol_exposure_pct, max_open_risk_pct
                FROM user_portfolio WHERE portfolio_key='local-default'
                """
            )
            portfolio_row = cursor.fetchone()
            if not portfolio_row:
                raise RuntimeError("local-default portfolio is missing")
            cursor.execute(
                """
                SELECT s.symbol_id, s.symbol FROM user_watchlist_symbol w
                JOIN user_portfolio p ON p.portfolio_id=w.portfolio_id
                JOIN dim_symbol s ON s.symbol_id=w.symbol_id
                WHERE p.portfolio_key='local-default'
                """
            )
            symbols = cursor.fetchall()
            for symbol in symbols:
                cursor.execute(
                    """
                    SELECT event_time_utc, open_price, high_price, low_price,
                           close_price, volume, source_name
                    FROM fact_market_bar_1m
                    WHERE symbol_id=%s AND certification_status='CERTIFIED'
                    ORDER BY event_time_utc DESC LIMIT 500
                    """,
                    (symbol["symbol_id"],),
                )
                rows = list(reversed(cursor.fetchall()))
                if len(rows) < 51:
                    continue
                closes = [Decimal(row["close_price"]) for row in rows]
                true_ranges = [
                    Decimal(row["high_price"]) - Decimal(row["low_price"]) for row in rows[-14:]
                ]
                atr = sum(true_ranges, Decimal()) / len(true_ranges)
                latest = rows[-1]
                cursor.execute(
                    """
                    SELECT MAX(filed_at_utc) latest
                    FROM fact_fundamental_metric WHERE symbol_id=%s
                    """,
                    (symbol["symbol_id"],),
                )
                fundamental_time = (cursor.fetchone() or {}).get("latest")
                inputs = DecisionInputs(
                    symbol=symbol["symbol"],
                    as_of_utc=as_of,
                    market_data_time_utc=latest["event_time_utc"].replace(tzinfo=UTC),
                    fundamentals_as_of_utc=fundamental_time.replace(tzinfo=UTC)
                    if fundamental_time
                    else None,
                    price=closes[-1],
                    ema20=_ema(closes[-80:], 20),
                    ema50=_ema(closes[-120:], 50),
                    atr14=atr,
                    rsi14=_rsi(closes),
                    macd_histogram=_ema(closes[-40:], 12) - _ema(closes[-60:], 26),
                    support=min(closes[-60:]),
                    resistance_1=max(closes[-30:]),
                    resistance_2=max(closes[-120:]),
                    volume_ratio=Decimal(latest["volume"])
                    / max(
                        Decimal(1),
                        sum((Decimal(r["volume"]) for r in rows[-21:-1]), Decimal()) / 20,
                    ),
                    relative_strength_spy=Decimal(),
                    daily_trend=1 if closes[-1] > _ema(closes[-120:], 50) else -1,
                    hourly_trend=1 if closes[-1] > _ema(closes[-60:], 20) else -1,
                    revenue_growth_pct=None,
                    eps_growth_pct=None,
                    fcf_growth_pct=None,
                    net_margin_pct=None,
                    debt_to_equity=None,
                    dilution_pct=None,
                    feed=str(latest["source_name"]),
                    certification_status="CERTIFIED",
                    shadow_mode=True,
                )
                decision = build_decision(
                    inputs,
                    PortfolioRisk(
                        equity=Decimal(portfolio_row["equity"]),
                        risk_per_trade_pct=Decimal(portfolio_row["risk_per_trade_pct"]),
                        max_symbol_exposure_pct=Decimal(portfolio_row["max_symbol_exposure_pct"]),
                        max_open_risk_pct=Decimal(portfolio_row["max_open_risk_pct"]),
                    ),
                )
                recommendation_id = str(
                    uuid5(
                        NAMESPACE_URL,
                        f"marketpilot:{symbol['symbol']}:{as_of.isoformat()}:decision-intelligence-v1:CERTIFIED",
                    )
                )
                lifecycle = (
                    "INSUFFICIENT_DATA" if decision.action == "INSUFFICIENT DATA" else "CERTIFIED"
                )
                cursor.execute(
                    """
                    INSERT INTO fact_opportunity_recommendation (
                        recommendation_id, symbol_id, as_of_utc, market_data_time_utc,
                        fundamentals_as_of_utc, action, actionable, lifecycle_status,
                        technical_score, fundamental_score, opportunity_score, confidence,
                        market_price, buy_zone_low, buy_zone_high, stop_price, target_1,
                        target_2, risk_reward_1, risk_reward_2, potential_profit_1_pct,
                        potential_profit_2_pct, valid_until_utc, feed_name, model_version,
                        input_snapshot_json, explanation_json, pipeline_run_id, code_version,
                        data_version, schema_version
                    ) VALUES (
                        %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
                        %s,%s,%s,%s,%s,%s,%s,%s,%s,'decision-intelligence-v1',1
                    ) ON DUPLICATE KEY UPDATE
                        explanation_json=VALUES(explanation_json),
                        confidence=VALUES(confidence)
                    """,
                    (
                        recommendation_id,
                        symbol["symbol_id"],
                        as_of.replace(tzinfo=None),
                        latest["event_time_utc"],
                        fundamental_time,
                        decision.action,
                        decision.actionable,
                        lifecycle,
                        decision.technical_score,
                        decision.fundamental_score,
                        decision.opportunity_score,
                        decision.confidence,
                        inputs.price,
                        decision.buy_zone_low,
                        decision.buy_zone_high,
                        decision.stop_price,
                        decision.target_1,
                        decision.target_2,
                        decision.risk_reward_1,
                        decision.risk_reward_2,
                        decision.potential_profit_1_pct,
                        decision.potential_profit_2_pct,
                        decision.valid_until_utc.replace(tzinfo=None),
                        inputs.feed,
                        decision.model_version,
                        json.dumps(
                            {"symbol": inputs.symbol, "window_bars": len(rows)},
                            separators=(",", ":"),
                        ),
                        json.dumps(
                            list(decision.explanation_he), ensure_ascii=False, separators=(",", ":")
                        ),
                        args.run_id,
                        os.environ.get("MARKETPILOT_CODE_VERSION", "development"),
                    ),
                )
                published += 1
        connection.commit()
        print(
            json.dumps(
                {
                    "event": "decision_intelligence_published",
                    "count": published,
                    "run_id": args.run_id,
                },
                separators=(",", ":"),
            )
        )
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


if __name__ == "__main__":
    main()
