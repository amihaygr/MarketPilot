"""MariaDB staging, quality-result, and atomic certified publication boundaries."""

import os
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date, datetime, timezone
from decimal import Decimal
from itertools import islice
from typing import Any

import pymysql

from marketpilot.batch.quality import QualityResult, quality_gate_passed
from marketpilot.streaming.mariadb_sink import MariaDbConfig

SILVER_DATASET = "market_bars_1m_silver"
SILVER_DQ_PIPELINE = "market-bars-silver-dq"
CERTIFIED_PUBLICATION_PIPELINE = "market-bars-certified-publication"


@dataclass(frozen=True, slots=True)
class PublicationSummary:
    staged_rows: int
    previous_partition_rows: int
    matched_business_keys: int
    changed_business_keys: int


def publisher_config_from_env() -> MariaDbConfig:
    return MariaDbConfig(
        host=os.environ["MARIADB_HOST"],
        port=int(os.environ.get("MARIADB_PORT", "3306")),
        database=os.environ["MARIADB_DATABASE"],
        user=os.environ["MARIADB_PUBLISH_USER"],
        password=os.environ["MARIADB_PUBLISH_PASSWORD"],
    )


def stage_market_bar_partition(rows: Iterable[Any], config: MariaDbConfig) -> None:
    """Idempotently stage one Spark partition for a later atomic publication."""
    records = [row.asDict(recursive=True) if hasattr(row, "asDict") else dict(row) for row in rows]
    if not records:
        return
    connection = _connect(config)
    try:
        with connection.cursor() as cursor:
            cursor.executemany(
                """
                INSERT INTO stg_market_bar_1m (
                    run_id, logical_date, symbol, event_time_utc, bar_interval,
                    open_price, high_price, low_price, close_price, volume,
                    source_event_id, source_name, ingested_at_utc,
                    kafka_topic, kafka_partition, kafka_offset,
                    code_version, data_version, schema_version
                ) VALUES (
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s,
                    %s, %s, %s,
                    %s, %s, %s,
                    %s, %s, %s
                )
                ON DUPLICATE KEY UPDATE
                    open_price = VALUES(open_price),
                    high_price = VALUES(high_price),
                    low_price = VALUES(low_price),
                    close_price = VALUES(close_price),
                    volume = VALUES(volume),
                    source_event_id = VALUES(source_event_id),
                    source_name = VALUES(source_name),
                    ingested_at_utc = VALUES(ingested_at_utc),
                    kafka_topic = VALUES(kafka_topic),
                    kafka_partition = VALUES(kafka_partition),
                    kafka_offset = VALUES(kafka_offset),
                    code_version = VALUES(code_version),
                    data_version = VALUES(data_version),
                    schema_version = VALUES(schema_version)
                """,
                [_stage_parameters(record) for record in records],
            )
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def stage_market_bar_batches(
    rows: Iterable[Any],
    config: MariaDbConfig,
    *,
    batch_size: int = 1_000,
) -> None:
    """Stage a bounded driver-side stream without materializing the whole dataset."""
    if batch_size < 1:
        raise ValueError("batch_size must be positive")

    iterator = iter(rows)
    while batch := list(islice(iterator, batch_size)):
        stage_market_bar_partition(batch, config)


def clear_staging_run(config: MariaDbConfig, run_id: str) -> None:
    connection = _connect(config)
    try:
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM stg_market_bar_1m WHERE run_id = %s", (run_id,))
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def record_quality_gate(
    config: MariaDbConfig,
    run_id: str,
    logical_date: date,
    results: tuple[QualityResult, ...],
    *,
    partition_key: str | None = None,
) -> None:
    """Persist one idempotent DQ result set and its blocking watermark."""
    passed = quality_gate_passed(results)
    resolved_partition_key = partition_key or logical_date.isoformat()
    connection = _connect(config)
    try:
        with connection.cursor() as cursor:
            cursor.executemany(
                """
                INSERT INTO data_quality_result (
                    run_id, dataset_name, partition_key, check_name,
                    status, observed_value, expected_value
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    status = VALUES(status),
                    observed_value = VALUES(observed_value),
                    expected_value = VALUES(expected_value),
                    measured_at_utc = CURRENT_TIMESTAMP(6)
                """,
                [
                    (
                        run_id,
                        SILVER_DATASET,
                        resolved_partition_key,
                        result.check_name,
                        result.status,
                        result.observed_value,
                        result.expected_value,
                    )
                    for result in results
                ],
            )
            cursor.execute(
                """
                INSERT INTO etl_watermark (
                    pipeline_name, partition_key, watermark_utc, status, run_id
                ) VALUES (%s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    watermark_utc = VALUES(watermark_utc),
                    status = VALUES(status),
                    run_id = VALUES(run_id)
                """,
                (
                    SILVER_DQ_PIPELINE,
                    resolved_partition_key,
                    datetime.combine(logical_date, datetime.max.time()),
                    "VALIDATED" if passed else "FAILED",
                    run_id,
                ),
            )
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def assert_quality_gate_validated(
    config: MariaDbConfig,
    run_id: str,
    logical_date: date,
    required_quality_checks: tuple[str, ...],
    *,
    partition_key: str | None = None,
) -> None:
    """Fail before staging unless every required DQ result belongs to this run and passed."""
    connection = _connect(config)
    try:
        with connection.cursor() as cursor:
            _assert_quality_gate(
                cursor,
                run_id,
                partition_key or logical_date.isoformat(),
                required_quality_checks,
                lock_watermark=False,
            )
    finally:
        connection.close()


def publish_certified_partition(
    config: MariaDbConfig,
    run_id: str,
    logical_date: date,
    required_quality_checks: tuple[str, ...],
    *,
    partition_key: str | None = None,
) -> PublicationSummary:
    """Atomically replace the staged symbol scope after rechecking its DQ gate."""
    resolved_partition_key = partition_key or logical_date.isoformat()
    connection = _connect(config)
    try:
        with connection.cursor() as cursor:
            _assert_quality_gate(
                cursor,
                run_id,
                resolved_partition_key,
                required_quality_checks,
                lock_watermark=True,
            )

            cursor.execute(
                "SELECT COUNT(*) FROM stg_market_bar_1m WHERE run_id = %s AND logical_date = %s",
                (run_id, logical_date),
            )
            staged_rows = int(cursor.fetchone()[0])
            if staged_rows == 0:
                raise RuntimeError("certified publication blocked: staging partition is empty")

            cursor.execute(
                """
                INSERT IGNORE INTO dim_symbol (symbol)
                SELECT DISTINCT symbol
                FROM stg_market_bar_1m
                WHERE run_id = %s AND logical_date = %s
                """,
                (run_id, logical_date),
            )
            cursor.execute(
                """
                SELECT COUNT(*)
                FROM fact_market_bar_1m f
                JOIN dim_symbol d ON d.symbol_id = f.symbol_id
                JOIN (
                    SELECT DISTINCT symbol
                    FROM stg_market_bar_1m
                    WHERE run_id = %s AND logical_date = %s
                ) scope ON scope.symbol = d.symbol
                WHERE f.event_time_utc >= %s
                  AND f.event_time_utc < DATE_ADD(%s, INTERVAL 1 DAY)
                """,
                (run_id, logical_date, logical_date, logical_date),
            )
            previous_rows = int(cursor.fetchone()[0])
            cursor.execute(
                """
                SELECT
                    COALESCE(SUM(f.symbol_id IS NOT NULL), 0),
                    COALESCE(SUM(
                        f.symbol_id IS NOT NULL AND (
                            f.open_price <> s.open_price OR f.high_price <> s.high_price OR
                            f.low_price <> s.low_price OR f.close_price <> s.close_price OR
                            f.volume <> s.volume
                        )
                    ), 0)
                FROM stg_market_bar_1m s
                LEFT JOIN dim_symbol d ON d.symbol = s.symbol
                LEFT JOIN fact_market_bar_1m f
                  ON f.symbol_id = d.symbol_id
                 AND f.event_time_utc = s.event_time_utc
                 AND f.bar_interval = s.bar_interval
                WHERE s.run_id = %s AND s.logical_date = %s
                """,
                (run_id, logical_date),
            )
            matched_keys, changed_keys = (int(value) for value in cursor.fetchone())

            cursor.execute(
                """
                DELETE f
                FROM fact_market_bar_1m f
                JOIN dim_symbol d ON d.symbol_id = f.symbol_id
                JOIN (
                    SELECT DISTINCT symbol
                    FROM stg_market_bar_1m
                    WHERE run_id = %s AND logical_date = %s
                ) scope ON scope.symbol = d.symbol
                LEFT JOIN stg_market_bar_1m s
                  ON s.run_id = %s
                 AND s.logical_date = %s
                 AND s.symbol = d.symbol
                 AND s.event_time_utc = f.event_time_utc
                 AND s.bar_interval = f.bar_interval
                WHERE f.event_time_utc >= %s
                  AND f.event_time_utc < DATE_ADD(%s, INTERVAL 1 DAY)
                  AND s.run_id IS NULL
                """,
                (run_id, logical_date, run_id, logical_date, logical_date, logical_date),
            )
            cursor.execute(
                """
                INSERT INTO fact_market_bar_1m (
                    symbol_id, event_time_utc, bar_interval,
                    open_price, high_price, low_price, close_price, volume,
                    certification_status, source_event_id, source_name, ingested_at_utc,
                    kafka_topic, kafka_partition, kafka_offset,
                    pipeline_run_id, code_version, data_version, schema_version
                )
                SELECT
                    d.symbol_id, s.event_time_utc, s.bar_interval,
                    s.open_price, s.high_price, s.low_price, s.close_price, s.volume,
                    'CERTIFIED', s.source_event_id, s.source_name, s.ingested_at_utc,
                    s.kafka_topic, s.kafka_partition, s.kafka_offset,
                    s.run_id, s.code_version, s.data_version, s.schema_version
                FROM stg_market_bar_1m s
                JOIN dim_symbol d ON d.symbol = s.symbol
                WHERE s.run_id = %s AND s.logical_date = %s
                ON DUPLICATE KEY UPDATE
                    open_price = VALUES(open_price),
                    high_price = VALUES(high_price),
                    low_price = VALUES(low_price),
                    close_price = VALUES(close_price),
                    volume = VALUES(volume),
                    certification_status = 'CERTIFIED',
                    source_event_id = VALUES(source_event_id),
                    source_name = VALUES(source_name),
                    ingested_at_utc = VALUES(ingested_at_utc),
                    kafka_topic = VALUES(kafka_topic),
                    kafka_partition = VALUES(kafka_partition),
                    kafka_offset = VALUES(kafka_offset),
                    pipeline_run_id = VALUES(pipeline_run_id),
                    code_version = VALUES(code_version),
                    data_version = VALUES(data_version),
                    schema_version = VALUES(schema_version)
                """,
                (run_id, logical_date),
            )
            cursor.execute(
                """
                INSERT INTO data_quality_result (
                    run_id, dataset_name, partition_key, check_name,
                    status, observed_value, expected_value
                ) VALUES (%s, 'gold_reconciliation', %s, 'matched_prepublication_keys',
                          %s, %s, 'informational')
                ON DUPLICATE KEY UPDATE
                    status = VALUES(status),
                    observed_value = VALUES(observed_value),
                    expected_value = VALUES(expected_value),
                    measured_at_utc = CURRENT_TIMESTAMP(6)
                """,
                (
                    run_id,
                    resolved_partition_key,
                    "PASS" if matched_keys == staged_rows else "WARN",
                    f"matched={matched_keys};staged={staged_rows};changed={changed_keys}",
                ),
            )
            cursor.execute(
                """
                INSERT INTO etl_watermark (
                    pipeline_name, partition_key, watermark_utc, status, run_id
                ) VALUES (%s, %s, %s, 'PUBLISHED', %s)
                ON DUPLICATE KEY UPDATE
                    watermark_utc = VALUES(watermark_utc),
                    status = 'PUBLISHED',
                    run_id = VALUES(run_id)
                """,
                (
                    CERTIFIED_PUBLICATION_PIPELINE,
                    resolved_partition_key,
                    datetime.combine(logical_date, datetime.max.time()),
                    run_id,
                ),
            )
            cursor.execute("DELETE FROM stg_market_bar_1m WHERE run_id = %s", (run_id,))
        connection.commit()
        return PublicationSummary(
            staged_rows=staged_rows,
            previous_partition_rows=previous_rows,
            matched_business_keys=matched_keys,
            changed_business_keys=changed_keys,
        )
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def _stage_parameters(row: dict[str, Any]) -> tuple[Any, ...]:
    return (
        str(row["pipeline_run_id"]),
        date.fromisoformat(str(row["logical_date"])),
        str(row["symbol"]),
        _utc_naive(row["event_time_utc"]),
        str(row["interval"]),
        Decimal(str(row["open"])),
        Decimal(str(row["high"])),
        Decimal(str(row["low"])),
        Decimal(str(row["close"])),
        int(row["volume"]),
        str(row["event_id"]),
        str(row["source"]),
        _utc_naive(row["ingested_at_utc"]),
        str(row["source_topic"]),
        int(row["source_partition"]),
        int(row["source_offset"]),
        str(row["code_version"]),
        str(row["data_version"]),
        int(row["event_schema_version"]),
    )


def _assert_quality_gate(
    cursor: Any,
    run_id: str,
    partition_key: str,
    required_quality_checks: tuple[str, ...],
    *,
    lock_watermark: bool,
) -> None:
    lock_clause = " FOR UPDATE" if lock_watermark else ""
    cursor.execute(
        """
        SELECT status, run_id
        FROM etl_watermark
        WHERE pipeline_name = %s AND partition_key = %s
        """
        + lock_clause,
        (SILVER_DQ_PIPELINE, partition_key),
    )
    watermark = cursor.fetchone()
    if watermark != ("VALIDATED", run_id):
        raise RuntimeError("certified publication blocked: DQ watermark is not validated")

    placeholders = ",".join(["%s"] * len(required_quality_checks))
    cursor.execute(
        f"""
        SELECT COUNT(*), COALESCE(SUM(status = 'FAIL'), 0)
        FROM data_quality_result
        WHERE run_id = %s
          AND dataset_name = %s
          AND partition_key = %s
          AND check_name IN ({placeholders})
        """,
        (run_id, SILVER_DATASET, partition_key, *required_quality_checks),
    )
    result_count, failed_count = cursor.fetchone()
    if result_count != len(required_quality_checks) or failed_count:
        raise RuntimeError("certified publication blocked: required DQ checks are incomplete")


def _connect(config: MariaDbConfig):  # type: ignore[no-untyped-def]
    return pymysql.connect(
        host=config.host,
        port=config.port,
        database=config.database,
        user=config.user,
        password=config.password,
        charset="utf8mb4",
        autocommit=False,
        connect_timeout=config.connect_timeout_seconds,
    )


def _utc_naive(value: Any) -> datetime:
    if not isinstance(value, datetime):
        raise TypeError("timestamp values must be datetime instances")
    if value.tzinfo is not None:
        return value.astimezone(timezone.utc).replace(tzinfo=None)  # noqa: UP017
    return value
