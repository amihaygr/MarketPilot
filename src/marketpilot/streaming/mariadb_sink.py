"""Idempotent MariaDB Gold writes for streaming market bars."""

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

import pymysql

UPSERT_SYMBOL_SQL = """
INSERT INTO dim_symbol (symbol)
VALUES (%s)
ON DUPLICATE KEY UPDATE symbol = VALUES(symbol)
""".strip()

UPSERT_MARKET_BAR_SQL = """
INSERT INTO fact_market_bar_1m (
    symbol_id, event_time_utc, bar_interval,
    open_price, high_price, low_price, close_price, volume,
    certification_status, source_event_id, source_name, ingested_at_utc,
    kafka_topic, kafka_partition, kafka_offset,
    pipeline_run_id, code_version, data_version, schema_version
)
SELECT
    symbol_id, %s, %s,
    %s, %s, %s, %s, %s,
    'PROVISIONAL', %s, %s, %s,
    %s, %s, %s,
    %s, %s, %s, %s
FROM dim_symbol
WHERE symbol = %s
ON DUPLICATE KEY UPDATE
    open_price = IF(certification_status = 'PROVISIONAL', VALUES(open_price), open_price),
    high_price = IF(certification_status = 'PROVISIONAL', VALUES(high_price), high_price),
    low_price = IF(certification_status = 'PROVISIONAL', VALUES(low_price), low_price),
    close_price = IF(certification_status = 'PROVISIONAL', VALUES(close_price), close_price),
    volume = IF(certification_status = 'PROVISIONAL', VALUES(volume), volume),
    source_event_id = IF(
        certification_status = 'PROVISIONAL', VALUES(source_event_id), source_event_id
    ),
    source_name = IF(certification_status = 'PROVISIONAL', VALUES(source_name), source_name),
    ingested_at_utc = IF(
        certification_status = 'PROVISIONAL', VALUES(ingested_at_utc), ingested_at_utc
    ),
    kafka_topic = IF(certification_status = 'PROVISIONAL', VALUES(kafka_topic), kafka_topic),
    kafka_partition = IF(
        certification_status = 'PROVISIONAL', VALUES(kafka_partition), kafka_partition
    ),
    kafka_offset = IF(certification_status = 'PROVISIONAL', VALUES(kafka_offset), kafka_offset),
    pipeline_run_id = IF(
        certification_status = 'PROVISIONAL', VALUES(pipeline_run_id), pipeline_run_id
    ),
    code_version = IF(certification_status = 'PROVISIONAL', VALUES(code_version), code_version),
    data_version = IF(certification_status = 'PROVISIONAL', VALUES(data_version), data_version),
    schema_version = IF(
        certification_status = 'PROVISIONAL', VALUES(schema_version), schema_version
    )
""".strip()


@dataclass(frozen=True, slots=True)
class MariaDbConfig:
    host: str
    port: int
    database: str
    user: str
    password: str
    connect_timeout_seconds: int = 10


def market_bar_parameters(row: Mapping[str, Any]) -> tuple[Any, ...]:
    """Convert a validated Spark row to the parameter order used by the Gold upsert."""
    return (
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
        str(row["kafka_topic"]),
        int(row["kafka_partition"]),
        int(row["kafka_offset"]),
        str(row["pipeline_run_id"]),
        str(row["code_version"]),
        str(row["data_version"]),
        int(row["schema_version"]),
        str(row["symbol"]),
    )


def upsert_market_bar_partition(rows: Iterable[Any], config: MariaDbConfig) -> None:
    """Write one Spark partition transactionally and safely under task retries."""
    records = [row.asDict(recursive=True) if hasattr(row, "asDict") else dict(row) for row in rows]
    if not records:
        return

    connection = pymysql.connect(
        host=config.host,
        port=config.port,
        database=config.database,
        user=config.user,
        password=config.password,
        charset="utf8mb4",
        autocommit=False,
        connect_timeout=config.connect_timeout_seconds,
    )
    try:
        with connection.cursor() as cursor:
            cursor.executemany(UPSERT_SYMBOL_SQL, [(str(row["symbol"]),) for row in records])
            cursor.executemany(
                UPSERT_MARKET_BAR_SQL,
                [market_bar_parameters(row) for row in records],
            )
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def _utc_naive(value: Any) -> datetime:
    if not isinstance(value, datetime):
        raise TypeError("timestamp values must be datetime instances")
    if value.tzinfo is not None:
        return value.astimezone(timezone.utc).replace(tzinfo=None)  # noqa: UP017
    return value
