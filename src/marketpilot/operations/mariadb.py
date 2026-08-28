"""Narrow MariaDB boundary for archive manifests and isolated restore drills."""

from __future__ import annotations

import os
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import pymysql

from marketpilot.operations.archive import ArchiveManifest

SPARK_UTC = timezone.utc  # noqa: UP017 -- imported by Spark's Python 3.10 runtime.


@dataclass(frozen=True, slots=True)
class OperationsDbConfig:
    host: str
    port: int
    database: str
    user: str
    password: str

    @classmethod
    def from_env(cls) -> OperationsDbConfig:
        return cls(
            host=os.environ["MARIADB_HOST"],
            port=int(os.environ.get("MARIADB_PORT", "3306")),
            database=os.environ["MARIADB_DATABASE"],
            user=os.environ["MARIADB_PUBLISH_USER"],
            password=os.environ["MARIADB_PUBLISH_PASSWORD"],
        )


def archive_manifest_exists(
    config: OperationsDbConfig,
    dataset_name: str,
    archive_year: int,
    archive_version: int,
) -> bool:
    connection = _connect(config)
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT COUNT(*)
                FROM archive_manifest
                WHERE dataset_name = %s AND archive_year = %s AND archive_version = %s
                """,
                (dataset_name, archive_year, archive_version),
            )
            return int(cursor.fetchone()[0]) == 1
    finally:
        connection.close()


def register_archive_manifest(config: OperationsDbConfig, manifest: ArchiveManifest) -> None:
    manifest.validate_inventory()
    connection = _connect(config)
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO archive_manifest (
                    dataset_name, archive_year, archive_version, object_uri, manifest_uri,
                    row_count, object_count, checksum_sha256, schema_version, run_id,
                    code_version, min_event_time_utc, max_event_time_utc, period_closed,
                    verified_at_utc
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    object_uri = VALUES(object_uri),
                    manifest_uri = VALUES(manifest_uri),
                    row_count = VALUES(row_count),
                    object_count = VALUES(object_count),
                    checksum_sha256 = VALUES(checksum_sha256),
                    schema_version = VALUES(schema_version),
                    run_id = VALUES(run_id),
                    code_version = VALUES(code_version),
                    min_event_time_utc = VALUES(min_event_time_utc),
                    max_event_time_utc = VALUES(max_event_time_utc),
                    period_closed = VALUES(period_closed),
                    verified_at_utc = VALUES(verified_at_utc)
                """,
                (
                    manifest.dataset_name,
                    manifest.archive_year,
                    manifest.archive_version,
                    manifest.object_uri,
                    manifest.manifest_uri,
                    manifest.row_count,
                    manifest.object_count,
                    manifest.checksum_sha256,
                    manifest.schema_version,
                    manifest.run_id,
                    manifest.code_version,
                    _utc_naive(manifest.min_event_time_utc),
                    _utc_naive(manifest.max_event_time_utc),
                    manifest.period_closed,
                    _utc_naive(manifest.verified_at_utc),
                ),
            )
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def restore_market_bar_sample(
    config: OperationsDbConfig,
    *,
    restore_run_id: str,
    dataset_name: str,
    archive_year: int,
    archive_version: int,
    rows: Iterable[dict[str, Any]],
) -> int:
    records = list(rows)
    if not records:
        raise ValueError("restore sample must contain at least one row")
    connection = _connect(config)
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "DELETE FROM marketpilot_restore.restore_market_bar_1m WHERE restore_run_id = %s",
                (restore_run_id,),
            )
            cursor.executemany(
                """
                INSERT INTO marketpilot_restore.restore_market_bar_1m (
                    restore_run_id, symbol, event_time_utc, bar_interval,
                    open_price, high_price, low_price, close_price, volume,
                    certification_status, source_event_id, source_name, ingested_at_utc,
                    pipeline_run_id, code_version, data_version, schema_version
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s, %s
                )
                """,
                [
                    (
                        restore_run_id,
                        row["symbol"],
                        row["event_time_utc"],
                        row["bar_interval"],
                        row["open_price"],
                        row["high_price"],
                        row["low_price"],
                        row["close_price"],
                        row["volume"],
                        row["certification_status"],
                        row["source_event_id"],
                        row["source_name"],
                        row["ingested_at_utc"],
                        row["pipeline_run_id"],
                        row["code_version"],
                        row["data_version"],
                        row["schema_version"],
                    )
                    for row in records
                ],
            )
            cursor.execute(
                """
                SELECT COUNT(*)
                FROM marketpilot_restore.restore_market_bar_1m
                WHERE restore_run_id = %s
                """,
                (restore_run_id,),
            )
            restored_count = int(cursor.fetchone()[0])
            if restored_count != len(records):
                raise RuntimeError("restored sample row count does not match source sample")
            cursor.execute(
                """
                INSERT INTO archive_restore_result (
                    restore_run_id, dataset_name, archive_year, archive_version,
                    sample_row_count, status, verified_at_utc
                ) VALUES (%s, %s, %s, %s, %s, 'PASS', CURRENT_TIMESTAMP(6))
                ON DUPLICATE KEY UPDATE
                    sample_row_count = VALUES(sample_row_count),
                    status = 'PASS',
                    verified_at_utc = CURRENT_TIMESTAMP(6)
                """,
                (
                    restore_run_id,
                    dataset_name,
                    archive_year,
                    archive_version,
                    restored_count,
                ),
            )
        connection.commit()
        return restored_count
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def _connect(config: OperationsDbConfig):  # type: ignore[no-untyped-def]
    return pymysql.connect(
        host=config.host,
        port=config.port,
        database=config.database,
        user=config.user,
        password=config.password,
        charset="utf8mb4",
        autocommit=False,
        connect_timeout=10,
    )


def _utc_naive(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("archive timestamps must include a UTC offset")
    return parsed.astimezone(SPARK_UTC).replace(tzinfo=None)
