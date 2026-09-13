"""Bounded post-market evaluation for Phase 14 recommendations."""

from __future__ import annotations

import argparse
import json
import os
from datetime import date
from decimal import Decimal

import pymysql
from pymysql.cursors import DictCursor

from marketpilot.decision_intelligence.evaluation import evaluate_path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--evaluation-date", required=True)
    args = parser.parse_args()
    evaluation_date = date.fromisoformat(args.evaluation_date)
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
                SELECT r.recommendation_id,r.symbol_id,r.as_of_utc,r.buy_zone_low,
                       r.buy_zone_high,r.stop_price,r.target_1,r.target_2
                FROM fact_opportunity_recommendation r
                WHERE r.lifecycle_status='CERTIFIED' AND DATE(r.as_of_utc)<%s
                  AND r.action IN ('BUY ZONE','WATCH BREAKOUT','WAIT')
                """,
                (evaluation_date,),
            )
            for recommendation in cursor.fetchall():
                entry = (
                    Decimal(recommendation["buy_zone_low"])
                    + Decimal(recommendation["buy_zone_high"])
                ) / 2
                cursor.execute(
                    """
                    SELECT DATE(event_time_utc) trading_date,MAX(high_price) high_price,
                           MIN(low_price) low_price,
                           SUBSTRING_INDEX(
                               GROUP_CONCAT(close_price ORDER BY event_time_utc DESC),',',1
                           )
                               close_price
                    FROM fact_market_bar_1m
                    WHERE symbol_id=%s AND certification_status='CERTIFIED'
                      AND event_time_utc>%s AND DATE(event_time_utc)<=%s
                    GROUP BY DATE(event_time_utc) ORDER BY trading_date LIMIT 20
                    """,
                    (
                        recommendation["symbol_id"],
                        recommendation["as_of_utc"],
                        evaluation_date,
                    ),
                )
                daily = cursor.fetchall()
                for horizon in (2, 5, 10, 20):
                    if len(daily) < horizon:
                        continue
                    path = daily[:horizon]
                    result = evaluate_path(
                        entry=entry,
                        target_1=Decimal(recommendation["target_1"]),
                        target_2=Decimal(recommendation["target_2"]),
                        stop=Decimal(recommendation["stop_price"]),
                        bars=path,
                    )
                    cursor.execute(
                        """
                        INSERT INTO fact_recommendation_evaluation (
                            recommendation_id,horizon_sessions,evaluation_date,entry_price,
                            observed_close,observed_high,observed_low,realized_return_pct,
                            max_favorable_excursion_pct,max_adverse_excursion_pct,target_1_hit,
                            target_2_hit,stop_hit,outcome,pipeline_run_id,code_version
                        ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                        ON DUPLICATE KEY UPDATE evaluation_date=VALUES(evaluation_date),
                            observed_close=VALUES(observed_close),observed_high=VALUES(observed_high),
                            observed_low=VALUES(observed_low),realized_return_pct=VALUES(realized_return_pct),
                            max_favorable_excursion_pct=VALUES(max_favorable_excursion_pct),
                            max_adverse_excursion_pct=VALUES(max_adverse_excursion_pct),
                            target_1_hit=VALUES(target_1_hit),target_2_hit=VALUES(target_2_hit),
                            stop_hit=VALUES(stop_hit),outcome=VALUES(outcome),
                            pipeline_run_id=VALUES(pipeline_run_id),code_version=VALUES(code_version)
                        """,
                        (
                            recommendation["recommendation_id"],
                            horizon,
                            evaluation_date,
                            entry,
                            result.observed_close,
                            result.observed_high,
                            result.observed_low,
                            result.realized_return_pct,
                            result.max_favorable_excursion_pct,
                            result.max_adverse_excursion_pct,
                            result.target_1_hit,
                            result.target_2_hit,
                            result.stop_hit,
                            result.outcome,
                            args.run_id,
                            os.environ.get("MARKETPILOT_CODE_VERSION", "development"),
                        ),
                    )
                    published += 1
        connection.commit()
        print(json.dumps({"event": "recommendations_evaluated", "count": published}))
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


if __name__ == "__main__":
    main()
