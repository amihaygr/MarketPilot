"""Atomic, idempotent publication of one Gold analytics partition."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import date, datetime, timedelta
from typing import Any

import pymysql

from marketpilot.streaming.mariadb_sink import MariaDbConfig


def publish_analytics_partition(
    config: MariaDbConfig,
    *,
    logical_date: date,
    run_id: str,
    indicators: Iterable[Any],
    signals: Iterable[Any],
) -> tuple[int, int]:
    indicator_records = [_mapping(row) for row in indicators]
    signal_records = [_mapping(row) for row in signals]
    _validate_records(indicator_records, signal_records)
    start = datetime.combine(logical_date, datetime.min.time())
    end = start + timedelta(days=1)
    connection = pymysql.connect(
        host=config.host,
        port=config.port,
        database=config.database,
        user=config.user,
        password=config.password,
        charset="utf8mb4",
        autocommit=False,
        connect_timeout=10,
    )
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "DELETE FROM fact_signal WHERE signal_time_utc >= %s AND signal_time_utc < %s",
                (start, end),
            )
            cursor.execute(
                "DELETE FROM fact_indicator_1m WHERE event_time_utc >= %s AND event_time_utc < %s",
                (start, end),
            )
            if indicator_records:
                cursor.executemany(
                    """
                    INSERT INTO fact_indicator_1m (
                        symbol_id, event_time_utc, indicator_code, indicator_version,
                        indicator_value, lookback_bars, certification_status,
                        pipeline_run_id, code_version, data_version, schema_version
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    [
                        (
                            row["symbol_id"],
                            row["event_time_utc"],
                            row["indicator_code"],
                            row["indicator_version"],
                            row["indicator_value"],
                            row["lookback_bars"],
                            row["certification_status"],
                            run_id,
                            row["code_version"],
                            row["data_version"],
                            row["schema_version"],
                        )
                        for row in indicator_records
                    ],
                )
            if signal_records:
                cursor.executemany(
                    """
                    INSERT INTO fact_signal (
                        symbol_id, signal_time_utc, signal_code, model_version,
                        direction, strength, explanation, certification_status,
                        pipeline_run_id, code_version, data_version, schema_version
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    [
                        (
                            row["symbol_id"],
                            row["signal_time_utc"],
                            row["signal_code"],
                            row["model_version"],
                            row["direction"],
                            row["strength"],
                            row["explanation"],
                            row["certification_status"],
                            run_id,
                            row["code_version"],
                            row["data_version"],
                            row["schema_version"],
                        )
                        for row in signal_records
                    ],
                )
            cursor.executemany(
                """
                INSERT INTO data_quality_result (
                    run_id, dataset_name, partition_key, check_name,
                    status, observed_value, expected_value
                ) VALUES (%s, 'market_analytics_gold', %s, %s, 'PASS', %s, %s)
                ON DUPLICATE KEY UPDATE status='PASS',
                    observed_value=VALUES(observed_value),
                    expected_value=VALUES(expected_value),
                    measured_at_utc=CURRENT_TIMESTAMP(6)
                """,
                [
                    (run_id, logical_date.isoformat(), "non_empty", len(indicator_records), ">0"),
                    (run_id, logical_date.isoformat(), "indicator_duplicates", 0, 0),
                    (run_id, logical_date.isoformat(), "rsi_range", 0, 0),
                    (run_id, logical_date.isoformat(), "signal_strength_range", 0, 0),
                ],
            )
            cursor.execute(
                """
                INSERT INTO etl_watermark (
                    pipeline_name, partition_key, watermark_utc, status, run_id
                ) VALUES ('market-analytics-publication', %s, %s, 'PUBLISHED', %s)
                ON DUPLICATE KEY UPDATE watermark_utc=VALUES(watermark_utc),
                    status='PUBLISHED', run_id=VALUES(run_id)
                """,
                (logical_date.isoformat(), end - timedelta(microseconds=1), run_id),
            )
        connection.commit()
        return len(indicator_records), len(signal_records)
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def _mapping(row: Any) -> dict[str, Any]:
    return row.asDict(recursive=True) if hasattr(row, "asDict") else dict(row)


def _validate_records(
    indicators: list[dict[str, Any]],
    signals: list[dict[str, Any]],
) -> None:
    if not indicators:
        raise ValueError("analytics publication requires indicator rows")
    indicator_keys = {
        (
            row["symbol_id"],
            row["event_time_utc"],
            row["indicator_code"],
            row["indicator_version"],
        )
        for row in indicators
    }
    if len(indicator_keys) != len(indicators):
        raise ValueError("analytics publication contains duplicate indicator keys")
    for row in indicators:
        if row["indicator_code"] == "RSI_14" and not 0 <= float(row["indicator_value"]) <= 100:
            raise ValueError("RSI value is outside the supported range")
    signal_keys = {
        (row["symbol_id"], row["signal_time_utc"], row["signal_code"], row["model_version"])
        for row in signals
    }
    if len(signal_keys) != len(signals):
        raise ValueError("analytics publication contains duplicate signal keys")
    if any(not 0 <= float(row["strength"]) <= 1 for row in signals):
        raise ValueError("signal strength is outside the supported range")
