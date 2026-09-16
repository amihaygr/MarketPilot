"""Bounded Spark-submit driver that publishes auditable Phase 14 shadow snapshots."""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from decimal import Decimal
from uuid import NAMESPACE_URL, uuid5

import boto3
import pymysql
from pymysql.cursors import DictCursor

from marketpilot.corporate_actions.adjustments import adjust_bars_for_splits
from marketpilot.decision_intelligence.hybrid import decision_feature_payload, hybrid_action
from marketpilot.decision_intelligence.rules import DecisionInputs, PortfolioRisk, build_decision
from marketpilot.decision_intelligence.scoring import load_artifact, score_payload

SPARK_UTC = timezone.utc  # noqa: UP017 -- Spark 3.5.8 image uses Python 3.10.


def _load_current_model(cursor: DictCursor) -> tuple[dict[str, object] | None, str | None]:
    cursor.execute(
        """
        SELECT model_version,status,artifact_uri,artifact_sha256,activation_threshold,
               trained_through_date
        FROM decision_model_registry
        WHERE status IN ('ACTIVE','PREVIEW')
        ORDER BY FIELD(status,'ACTIVE','PREVIEW'),created_at_utc DESC LIMIT 1
        """
    )
    registry = cursor.fetchone()
    if not registry:
        return None, "no registered hybrid model"
    try:
        bucket, key = str(registry["artifact_uri"])[5:].split("/", 1)
        client = boto3.client(
            "s3",
            endpoint_url=os.environ["MINIO_ENDPOINT"],
            aws_access_key_id=os.environ["MINIO_ROOT_USER"],
            aws_secret_access_key=os.environ["MINIO_ROOT_PASSWORD"],
        )
        body = client.get_object(Bucket=bucket, Key=key)["Body"].read()
        registry["artifact"] = load_artifact(body, str(registry["artifact_sha256"]))
        return registry, None
    except Exception as error:  # artifact failures must degrade to deterministic v1
        return registry, f"{type(error).__name__}: {error}"


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


def _growth(values: list[Decimal]) -> Decimal | None:
    if len(values) < 2 or values[-2] == 0:
        return None
    return (values[-1] / values[-2] - 1) * 100


def _aggregate(rows: list[dict[str, object]], minutes: int) -> list[dict[str, object]]:
    buckets: dict[datetime, dict[str, object]] = {}
    for row in rows:
        timestamp = row["event_time_utc"]
        if not isinstance(timestamp, datetime):
            continue
        bucket = timestamp.replace(
            minute=(timestamp.minute // minutes) * minutes if minutes < 60 else 0,
            hour=(timestamp.hour // (minutes // 60)) * (minutes // 60)
            if minutes >= 60
            else timestamp.hour,
            second=0,
            microsecond=0,
        )
        current = buckets.get(bucket)
        if current is None:
            buckets[bucket] = dict(row)
            continue
        current["high_price"] = max(Decimal(current["high_price"]), Decimal(row["high_price"]))
        current["low_price"] = min(Decimal(current["low_price"]), Decimal(row["low_price"]))
        current["close_price"] = row["close_price"]
        current["volume"] = int(current["volume"]) + int(row["volume"])
    return list(buckets.values())


def _daily(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    buckets: dict[object, dict[str, object]] = {}
    for row in rows:
        timestamp = row["event_time_utc"]
        if not isinstance(timestamp, datetime):
            continue
        key = timestamp.date()
        current = buckets.get(key)
        if current is None:
            buckets[key] = dict(row)
            continue
        current["high_price"] = max(Decimal(current["high_price"]), Decimal(row["high_price"]))
        current["low_price"] = min(Decimal(current["low_price"]), Decimal(row["low_price"]))
        current["close_price"] = row["close_price"]
        current["volume"] = int(current["volume"]) + int(row["volume"])
    return list(buckets.values())


def _period_return(values: list[Decimal], periods: int = 20) -> Decimal:
    if len(values) <= periods or values[-periods - 1] == 0:
        return Decimal()
    return (values[-1] / values[-periods - 1] - 1) * 100


def _fundamentals(cursor: DictCursor, symbol_id: int) -> dict[str, Decimal | datetime | None]:
    cursor.execute(
        """
        SELECT metric_code, period_end_date, value_decimal, filed_at_utc
        FROM fact_fundamental_metric
        WHERE symbol_id=%s AND period_type='QUARTER'
        ORDER BY period_end_date
        """,
        (symbol_id,),
    )
    series: dict[str, list[Decimal]] = {}
    latest_filed: datetime | None = None
    for row in cursor.fetchall():
        series.setdefault(str(row["metric_code"]), []).append(Decimal(row["value_decimal"]))
        latest_filed = max(latest_filed or row["filed_at_utc"], row["filed_at_utc"])
    revenue = series.get("REVENUE", [])
    income = series.get("NET_INCOME", [])
    operating_cash = series.get("OPERATING_CASH_FLOW", [])
    capex = series.get("CAPEX", [])
    fcf = [cash - spend for cash, spend in zip(operating_cash, capex, strict=False)]
    equity = series.get("EQUITY", [])
    debt = series.get("DEBT", [])
    return {
        "as_of": latest_filed,
        "revenue_growth": _growth(revenue),
        "eps_growth": _growth(series.get("EPS_DILUTED", [])),
        "fcf_growth": _growth(fcf),
        "net_margin": income[-1] / revenue[-1] * 100
        if income and revenue and revenue[-1]
        else None,
        "debt_to_equity": debt[-1] / equity[-1] if debt and equity and equity[-1] else None,
        "dilution": _growth(series.get("SHARES_DILUTED", [])),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--as-of-utc")
    parser.add_argument(
        "--certification-status", choices=("PROVISIONAL", "CERTIFIED"), default="CERTIFIED"
    )
    parser.add_argument("--symbols")
    args = parser.parse_args()
    as_of = (
        datetime.fromisoformat(args.as_of_utc).astimezone(SPARK_UTC)
        if args.as_of_utc
        else datetime.now(SPARK_UTC)
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
                "SELECT promotion_status FROM shadow_mode_status WHERE model_version=%s",
                ("decision-intelligence-v1",),
            )
            shadow_row = cursor.fetchone() or {"promotion_status": "COLLECTING"}
            model_registry, model_error = _load_current_model(cursor)
            cursor.execute(
                """
                SELECT s.symbol_id, s.symbol FROM user_watchlist_symbol w
                JOIN user_portfolio p ON p.portfolio_id=w.portfolio_id
                JOIN dim_symbol s ON s.symbol_id=w.symbol_id
                WHERE p.portfolio_key='local-default'
                """
            )
            symbols = cursor.fetchall()
            status_filter = (
                "certification_status IN ('PROVISIONAL','CERTIFIED')"
                if args.certification_status == "PROVISIONAL"
                else "certification_status='CERTIFIED'"
            )
            cursor.execute(
                f"""
                SELECT f.event_time_utc,f.open_price,f.high_price,f.low_price,
                       f.close_price,f.volume,f.source_name
                FROM fact_market_bar_1m f JOIN dim_symbol s ON s.symbol_id=f.symbol_id
                WHERE s.symbol='SPY' AND {status_filter} AND f.event_time_utc<=%s
                ORDER BY f.event_time_utc DESC LIMIT 10000
                """,
                (as_of.replace(tzinfo=None),),
            )
            spy_rows = list(reversed(cursor.fetchall()))
            spy_15m_closes = [Decimal(row["close_price"]) for row in _aggregate(spy_rows, 15)]
            requested_symbols = {
                value.strip().upper() for value in (args.symbols or "").split(",") if value.strip()
            }
            for symbol in symbols:
                if requested_symbols and symbol["symbol"] not in requested_symbols:
                    continue
                cursor.execute(
                    f"""
                    SELECT event_time_utc, open_price, high_price, low_price,
                           close_price, volume, source_name
                    FROM fact_market_bar_1m
                    WHERE symbol_id=%s AND {status_filter} AND event_time_utc<=%s
                    ORDER BY event_time_utc DESC LIMIT 10000
                    """,
                    (symbol["symbol_id"], as_of.replace(tzinfo=None)),
                )
                rows = list(reversed(cursor.fetchall()))
                if rows:
                    cursor.execute(
                        """
                        SELECT action_type,ex_date,old_rate,new_rate
                        FROM fact_corporate_action
                        WHERE symbol_id=%s AND action_type IN ('forward_splits','reverse_splits')
                          AND ex_date BETWEEN DATE(%s) AND DATE(%s)
                        ORDER BY ex_date
                        """,
                        (
                            symbol["symbol_id"],
                            rows[0]["event_time_utc"],
                            rows[-1]["event_time_utc"],
                        ),
                    )
                    rows = adjust_bars_for_splits(rows, cursor.fetchall())
                bars_5m = _aggregate(rows, 5)
                bars_15m = _aggregate(rows, 15)
                bars_1h = _aggregate(rows, 60)
                bars_1d = _daily(rows)
                if len(bars_15m) < 51 or len(bars_1h) < 20 or len(bars_1d) < 2:
                    continue
                closes = [Decimal(row["close_price"]) for row in bars_15m]
                hourly_closes = [Decimal(row["close_price"]) for row in bars_1h]
                daily_closes = [Decimal(row["close_price"]) for row in bars_1d]
                five_minute_closes = [Decimal(row["close_price"]) for row in bars_5m]
                true_ranges = [
                    Decimal(row["high_price"]) - Decimal(row["low_price"]) for row in bars_15m[-14:]
                ]
                atr = sum(true_ranges, Decimal()) / len(true_ranges)
                latest = rows[-1]
                fundamentals = _fundamentals(cursor, int(symbol["symbol_id"]))
                fundamental_time = fundamentals["as_of"]
                inputs = DecisionInputs(
                    symbol=symbol["symbol"],
                    as_of_utc=as_of,
                    market_data_time_utc=latest["event_time_utc"].replace(tzinfo=SPARK_UTC),
                    fundamentals_as_of_utc=fundamental_time.replace(tzinfo=SPARK_UTC)
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
                    volume_ratio=Decimal(bars_15m[-1]["volume"])
                    / max(
                        Decimal(1),
                        sum((Decimal(r["volume"]) for r in bars_15m[-21:-1]), Decimal()) / 20,
                    ),
                    relative_strength_spy=_period_return(closes) - _period_return(spy_15m_closes),
                    daily_trend=1 if daily_closes[-1] > daily_closes[-2] else -1,
                    hourly_trend=1 if hourly_closes[-1] > _ema(hourly_closes, 20) else -1,
                    five_minute_trend=(
                        1 if five_minute_closes[-1] > _ema(five_minute_closes[-20:], 10) else -1
                    ),
                    revenue_growth_pct=fundamentals["revenue_growth"],
                    eps_growth_pct=fundamentals["eps_growth"],
                    fcf_growth_pct=fundamentals["fcf_growth"],
                    net_margin_pct=fundamentals["net_margin"],
                    debt_to_equity=fundamentals["debt_to_equity"],
                    dilution_pct=fundamentals["dilution"],
                    feed=os.environ.get("ALPACA_DATA_FEED", "iex"),
                    certification_status=args.certification_status,
                    shadow_mode=shadow_row["promotion_status"] != "APPROVED",
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
                        f"marketpilot:{args.run_id}:{symbol['symbol']}:"
                        f"decision-intelligence-v1:{args.certification_status}",
                    )
                )
                feature_payload = decision_feature_payload(inputs, decision)
                cursor.execute(
                    """
                    INSERT INTO fact_decision_feature_snapshot (
                        snapshot_id,symbol_id,as_of_utc,feature_schema_version,feature_json,
                        market_data_time_utc,fundamentals_as_of_utc,certification_status,
                        feed_name,pipeline_run_id,code_version,data_version
                    ) VALUES (%s,%s,%s,2,%s,%s,%s,%s,%s,%s,%s,'decision-feature-v2')
                    ON DUPLICATE KEY UPDATE feature_json=VALUES(feature_json),
                        market_data_time_utc=VALUES(market_data_time_utc),
                        fundamentals_as_of_utc=VALUES(fundamentals_as_of_utc),
                        pipeline_run_id=VALUES(pipeline_run_id),code_version=VALUES(code_version)
                    """,
                    (
                        recommendation_id,
                        symbol["symbol_id"],
                        as_of.replace(tzinfo=None),
                        json.dumps(feature_payload, sort_keys=True, separators=(",", ":")),
                        latest["event_time_utc"],
                        fundamental_time,
                        args.certification_status,
                        inputs.feed,
                        args.run_id,
                        os.environ.get("MARKETPILOT_CODE_VERSION", "development"),
                    ),
                )
                lifecycle = (
                    "INSUFFICIENT_DATA"
                    if decision.action == "INSUFFICIENT DATA"
                    else args.certification_status
                )
                cursor.execute(
                    """
                    SELECT action FROM fact_opportunity_recommendation
                    WHERE symbol_id=%s ORDER BY as_of_utc DESC LIMIT 1
                    """,
                    (symbol["symbol_id"],),
                )
                previous = cursor.fetchone()
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
                            {
                                "symbol": inputs.symbol,
                                "source_rows": len(rows),
                                "bars_5m": len(bars_5m),
                                "bars_15m": len(bars_15m),
                                "bars_1h": len(bars_1h),
                                "bars_1d": len(bars_1d),
                            },
                            separators=(",", ":"),
                        ),
                        json.dumps(
                            list(decision.explanation_he), ensure_ascii=False, separators=(",", ":")
                        ),
                        args.run_id,
                        os.environ.get("MARKETPILOT_CODE_VERSION", "development"),
                    ),
                )
                model_status = "FALLBACK"
                model_version = "decision-intelligence-v2-hybrid"
                probability = expected_model_r = None
                positive_drivers: tuple[str, ...] = ()
                negative_drivers: tuple[str, ...] = ()
                if model_registry and not model_error:
                    model_status = str(model_registry["status"])
                    model_version = str(model_registry["model_version"])
                    score = score_payload(model_registry["artifact"], feature_payload)
                    probability = score.probability
                    expected_model_r = score.expected_r
                    positive_drivers = score.positive_drivers
                    negative_drivers = score.negative_drivers
                    if model_status == "ACTIVE":
                        published_action = hybrid_action(
                            rules_action=decision.action,
                            success_probability=probability,
                            activation_threshold=Decimal(model_registry["activation_threshold"]),
                            price=inputs.price,
                            zone_low=decision.buy_zone_low,
                            zone_high=decision.buy_zone_high,
                            model_status="ACTIVE",
                        )
                        cursor.execute(
                            """
                            UPDATE fact_opportunity_recommendation
                            SET action=%s, actionable=%s
                            WHERE recommendation_id=%s
                            """,
                            (published_action, published_action == "BUY ZONE", recommendation_id),
                        )
                cursor.execute(
                    """
                    INSERT INTO fact_decision_model_prediction (
                        recommendation_id,model_version,model_status,success_probability,
                        expected_r,calibration_status,top_positive_drivers_json,
                        top_negative_drivers_json
                    ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                    ON DUPLICATE KEY UPDATE model_status=VALUES(model_status),
                        success_probability=VALUES(success_probability),
                        expected_r=VALUES(expected_r),calibration_status=VALUES(calibration_status),
                        top_positive_drivers_json=VALUES(top_positive_drivers_json),
                        top_negative_drivers_json=VALUES(top_negative_drivers_json)
                    """,
                    (
                        recommendation_id,
                        model_version,
                        model_status,
                        probability,
                        expected_model_r,
                        "CALIBRATED" if probability is not None else "UNAVAILABLE",
                        json.dumps(positive_drivers),
                        json.dumps(negative_drivers),
                    ),
                )
                alert_type = None
                if decision.action == "BUY ZONE" and (
                    not previous or previous["action"] != "BUY ZONE"
                ):
                    alert_type = "ENTERED_BUY_ZONE"
                elif previous and previous["action"] != decision.action:
                    alert_type = "ACTION_CHANGED"
                if alert_type:
                    alert_id = str(uuid5(NAMESPACE_URL, f"{recommendation_id}:{alert_type}"))
                    cursor.execute(
                        """
                        INSERT IGNORE INTO fact_decision_alert (
                            alert_id,recommendation_id,symbol_id,alert_type,severity,title,
                            message,created_at_utc
                        ) VALUES (%s,%s,%s,%s,'WATCH',%s,%s,%s)
                        """,
                        (
                            alert_id,
                            recommendation_id,
                            symbol["symbol_id"],
                            alert_type,
                            f"{symbol['symbol']}: {decision.action}",
                            f"התרחיש השתנה ל-{decision.action}; יש לבדוק את רמות הסיכון והנתונים.",
                            as_of.replace(tzinfo=None),
                        ),
                    )
                published += 1
            if args.certification_status == "CERTIFIED":
                cursor.execute(
                    """
                SELECT COUNT(DISTINCT DATE(as_of_utc)) AS sessions,
                       MIN(DATE(as_of_utc)) AS first_date,MAX(DATE(as_of_utc)) AS latest_date
                FROM fact_opportunity_recommendation
                WHERE model_version=%s AND lifecycle_status='CERTIFIED'
                """,
                    ("decision-intelligence-v1",),
                )
                progress = cursor.fetchone()
                completed = min(20, int(progress["sessions"] or 0))
                cursor.execute(
                    """
                UPDATE shadow_mode_status SET completed_sessions=%s,first_session_date=%s,
                    latest_session_date=%s,
                    promotion_status=IF(promotion_status IN ('APPROVED','REJECTED'),
                        promotion_status,IF(%s>=required_sessions,'READY_FOR_REVIEW','COLLECTING'))
                WHERE model_version=%s
                """,
                    (
                        completed,
                        progress["first_date"],
                        progress["latest_date"],
                        completed,
                        "decision-intelligence-v1",
                    ),
                )
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
