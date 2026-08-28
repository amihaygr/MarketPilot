"""Parameterized, read-only MariaDB queries for application-facing Gold data."""

from __future__ import annotations

import math
from collections.abc import Callable
from datetime import UTC, date, datetime
from typing import Any, Protocol

import pymysql
from pymysql.cursors import DictCursor

from marketpilot.serving.settings import ServingSettings

Row = dict[str, Any]


class ReadRepository(Protocol):
    def ready(self) -> bool: ...

    def list_symbols(self) -> list[Row]: ...

    def list_market_bars(
        self,
        *,
        symbol: str,
        start_utc: datetime,
        end_utc: datetime,
        certification_status: str | None,
        page: int,
        page_size: int,
    ) -> Row: ...

    def list_sec_filings(
        self,
        *,
        symbol: str | None,
        form_type: str | None,
        start_date: date,
        end_date: date,
        page: int,
        page_size: int,
    ) -> Row: ...

    def list_indicators(
        self,
        *,
        symbol: str,
        start_utc: datetime,
        end_utc: datetime,
        indicator_code: str | None,
        page: int,
        page_size: int,
    ) -> Row: ...

    def list_signals(
        self,
        *,
        symbol: str | None,
        start_utc: datetime,
        end_utc: datetime,
        direction: str | None,
        page: int,
        page_size: int,
    ) -> Row: ...

    def freshness(self, *, code_version: str, generated_at_utc: datetime) -> Row: ...


class MariaDbReadRepository:
    def __init__(
        self,
        settings: ServingSettings,
        *,
        connector: Callable[..., pymysql.Connection[DictCursor]] = pymysql.connect,
    ) -> None:
        self._settings = settings
        self._connector = connector

    def _connect(self) -> pymysql.Connection[DictCursor]:
        return self._connector(
            host=self._settings.mariadb_host,
            port=self._settings.mariadb_port,
            database=self._settings.mariadb_database,
            user=self._settings.mariadb_user,
            password=self._settings.mariadb_password,
            charset="utf8mb4",
            autocommit=True,
            connect_timeout=self._settings.query_timeout_seconds,
            read_timeout=self._settings.query_timeout_seconds,
            cursorclass=DictCursor,
        )

    def ready(self) -> bool:
        connection = self._connect()
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1 AS ready")
                row = cursor.fetchone()
            return bool(row and row["ready"] == 1)
        finally:
            connection.close()

    def list_symbols(self) -> list[Row]:
        rows = self._fetch_all(
            """
            SELECT
                symbol,
                display_name,
                is_active,
                (
                    SELECT COUNT(*)
                    FROM fact_market_bar_1m AS bars
                    WHERE bars.symbol_id = symbols.symbol_id
                ) AS market_bar_count,
                (
                    SELECT MAX(event_time_utc)
                    FROM fact_market_bar_1m AS bars
                    WHERE bars.symbol_id = symbols.symbol_id
                ) AS latest_bar_time_utc,
                (
                    SELECT certification_status
                    FROM fact_market_bar_1m AS bars
                    WHERE bars.symbol_id = symbols.symbol_id
                    ORDER BY event_time_utc DESC
                    LIMIT 1
                ) AS latest_certification_status
            FROM dim_symbol AS symbols
            WHERE is_active = TRUE
            ORDER BY symbol
            """
        )
        return [_normalize_datetimes(row) for row in rows]

    def list_market_bars(
        self,
        *,
        symbol: str,
        start_utc: datetime,
        end_utc: datetime,
        certification_status: str | None,
        page: int,
        page_size: int,
    ) -> Row:
        predicates = [
            "symbols.symbol = %s",
            "bars.event_time_utc >= %s",
            "bars.event_time_utc < %s",
        ]
        parameters: list[Any] = [symbol, _database_utc(start_utc), _database_utc(end_utc)]
        if certification_status:
            predicates.append("bars.certification_status = %s")
            parameters.append(certification_status)
        where_clause = " AND ".join(predicates)
        count_sql = f"""
            SELECT COUNT(*) AS total
            FROM fact_market_bar_1m AS bars
            JOIN dim_symbol AS symbols ON symbols.symbol_id = bars.symbol_id
            WHERE {where_clause}
        """
        item_sql = f"""
            SELECT
                symbols.symbol,
                bars.event_time_utc,
                bars.bar_interval AS `interval`,
                bars.open_price AS open,
                bars.high_price AS high,
                bars.low_price AS low,
                bars.close_price AS close,
                bars.volume,
                bars.certification_status,
                bars.source_name AS source,
                bars.ingested_at_utc,
                bars.data_version,
                bars.schema_version
            FROM fact_market_bar_1m AS bars
            JOIN dim_symbol AS symbols ON symbols.symbol_id = bars.symbol_id
            WHERE {where_clause}
            ORDER BY bars.event_time_utc DESC
            LIMIT %s OFFSET %s
        """
        return self._page(count_sql, item_sql, parameters, page, page_size)

    def list_sec_filings(
        self,
        *,
        symbol: str | None,
        form_type: str | None,
        start_date: date,
        end_date: date,
        page: int,
        page_size: int,
    ) -> Row:
        predicates = ["filings.filing_date >= %s", "filings.filing_date <= %s"]
        parameters: list[Any] = [start_date, end_date]
        if symbol:
            predicates.append("symbols.symbol = %s")
            parameters.append(symbol)
        if form_type:
            predicates.append("filings.form_type = %s")
            parameters.append(form_type)
        where_clause = " AND ".join(predicates)
        count_sql = f"""
            SELECT COUNT(*) AS total
            FROM fact_sec_filing AS filings
            JOIN dim_symbol AS symbols ON symbols.symbol_id = filings.symbol_id
            WHERE {where_clause}
        """
        item_sql = f"""
            SELECT
                filings.accession_number,
                symbols.symbol,
                filings.company_name,
                filings.form_type,
                filings.filing_date,
                filings.report_date,
                filings.acceptance_datetime_utc,
                filings.primary_document,
                filings.primary_document_description,
                filings.source_url,
                filings.ingested_at_utc,
                filings.schema_version
            FROM fact_sec_filing AS filings
            JOIN dim_symbol AS symbols ON symbols.symbol_id = filings.symbol_id
            WHERE {where_clause}
            ORDER BY filings.filing_date DESC, filings.accession_number DESC
            LIMIT %s OFFSET %s
        """
        return self._page(count_sql, item_sql, parameters, page, page_size)

    def list_indicators(
        self,
        *,
        symbol: str,
        start_utc: datetime,
        end_utc: datetime,
        indicator_code: str | None,
        page: int,
        page_size: int,
    ) -> Row:
        predicates = [
            "symbols.symbol = %s",
            "indicators.event_time_utc >= %s",
            "indicators.event_time_utc < %s",
        ]
        parameters: list[Any] = [symbol, _database_utc(start_utc), _database_utc(end_utc)]
        if indicator_code:
            predicates.append("indicators.indicator_code = %s")
            parameters.append(indicator_code)
        where_clause = " AND ".join(predicates)
        count_sql = f"""
            SELECT COUNT(*) AS total
            FROM fact_indicator_1m AS indicators
            JOIN dim_symbol AS symbols ON symbols.symbol_id = indicators.symbol_id
            WHERE {where_clause}
        """
        item_sql = f"""
            SELECT symbols.symbol, indicators.event_time_utc,
                   indicators.indicator_code, indicators.indicator_version,
                   indicators.indicator_value AS value, indicators.lookback_bars,
                   indicators.certification_status, indicators.data_version,
                   indicators.schema_version
            FROM fact_indicator_1m AS indicators
            JOIN dim_symbol AS symbols ON symbols.symbol_id = indicators.symbol_id
            WHERE {where_clause}
            ORDER BY indicators.event_time_utc DESC, indicators.indicator_code
            LIMIT %s OFFSET %s
        """
        return self._page(count_sql, item_sql, parameters, page, page_size)

    def list_signals(
        self,
        *,
        symbol: str | None,
        start_utc: datetime,
        end_utc: datetime,
        direction: str | None,
        page: int,
        page_size: int,
    ) -> Row:
        predicates = ["signals.signal_time_utc >= %s", "signals.signal_time_utc < %s"]
        parameters: list[Any] = [_database_utc(start_utc), _database_utc(end_utc)]
        if symbol:
            predicates.append("symbols.symbol = %s")
            parameters.append(symbol)
        if direction:
            predicates.append("signals.direction = %s")
            parameters.append(direction)
        where_clause = " AND ".join(predicates)
        count_sql = f"""
            SELECT COUNT(*) AS total
            FROM fact_signal AS signals
            JOIN dim_symbol AS symbols ON symbols.symbol_id = signals.symbol_id
            WHERE {where_clause}
        """
        item_sql = f"""
            SELECT symbols.symbol, signals.signal_time_utc, signals.signal_code,
                   signals.model_version, signals.direction, signals.strength,
                   signals.explanation, signals.certification_status,
                   signals.data_version, signals.schema_version
            FROM fact_signal AS signals
            JOIN dim_symbol AS symbols ON symbols.symbol_id = signals.symbol_id
            WHERE {where_clause}
            ORDER BY signals.signal_time_utc DESC, signals.signal_code
            LIMIT %s OFFSET %s
        """
        return self._page(count_sql, item_sql, parameters, page, page_size)

    def freshness(self, *, code_version: str, generated_at_utc: datetime) -> Row:
        connection = self._connect()
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT
                        MAX(event_time_utc) AS latest_event_time_utc,
                        MAX(ingested_at_utc) AS latest_ingested_at_utc,
                        COUNT(*) AS bar_count,
                        COALESCE(SUM(certification_status = 'PROVISIONAL'), 0)
                            AS provisional_count,
                        COALESCE(SUM(certification_status = 'CERTIFIED'), 0)
                            AS certified_count,
                        (
                            SELECT certification_status
                            FROM fact_market_bar_1m
                            ORDER BY event_time_utc DESC
                            LIMIT 1
                        ) AS latest_certification_status
                    FROM fact_market_bar_1m
                    """
                )
                market = cursor.fetchone() or {}
                cursor.execute(
                    """
                    SELECT
                        MAX(filing_date) AS latest_filing_date,
                        MAX(ingested_at_utc) AS latest_ingested_at_utc,
                        COUNT(*) AS filing_count
                    FROM fact_sec_filing
                    """
                )
                sec = cursor.fetchone() or {}
                cursor.execute(
                    """
                    SELECT
                        symbols.symbol,
                        MAX(bars.event_time_utc) AS latest_event_time_utc,
                        MAX(bars.ingested_at_utc) AS latest_ingested_at_utc,
                        (
                            SELECT recent.certification_status
                            FROM fact_market_bar_1m AS recent
                            WHERE recent.symbol_id = symbols.symbol_id
                            ORDER BY recent.event_time_utc DESC
                            LIMIT 1
                        ) AS latest_certification_status
                    FROM dim_symbol AS symbols
                    LEFT JOIN fact_market_bar_1m AS bars
                        ON bars.symbol_id = symbols.symbol_id
                    WHERE symbols.is_active = TRUE
                    GROUP BY symbols.symbol_id, symbols.symbol
                    ORDER BY symbols.symbol
                    """
                )
                symbols = list(cursor.fetchall())
                cursor.execute(
                    """
                    SELECT pipeline_name, partition_key, watermark_utc, status, updated_at_utc
                    FROM etl_watermark
                    ORDER BY updated_at_utc DESC, pipeline_name, partition_key
                    LIMIT 25
                    """
                )
                pipelines = list(cursor.fetchall())
        finally:
            connection.close()
        return {
            "generated_at_utc": generated_at_utc,
            "market": _normalize_datetimes(market),
            "sec": _normalize_datetimes(sec),
            "symbols": [_normalize_datetimes(row) for row in symbols],
            "pipelines": [_normalize_datetimes(row) for row in pipelines],
            "code_version": code_version,
        }

    def _page(
        self,
        count_sql: str,
        item_sql: str,
        parameters: list[Any],
        page: int,
        page_size: int,
    ) -> Row:
        connection = self._connect()
        try:
            with connection.cursor() as cursor:
                cursor.execute(count_sql, tuple(parameters))
                total = int((cursor.fetchone() or {"total": 0})["total"])
                offset = (page - 1) * page_size
                cursor.execute(item_sql, (*parameters, page_size, offset))
                items = [_normalize_datetimes(row) for row in cursor.fetchall()]
        finally:
            connection.close()
        return {
            "items": items,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
                "total_pages": math.ceil(total / page_size) if total else 0,
            },
        }

    def _fetch_all(self, sql: str, parameters: tuple[Any, ...] = ()) -> list[Row]:
        connection = self._connect()
        try:
            with connection.cursor() as cursor:
                cursor.execute(sql, parameters)
                return list(cursor.fetchall())
        finally:
            connection.close()


def _database_utc(value: datetime) -> datetime:
    return value.astimezone(UTC).replace(tzinfo=None)


def _normalize_datetimes(row: Row) -> Row:
    normalized = dict(row)
    for key, value in normalized.items():
        if isinstance(value, datetime):
            normalized[key] = (
                value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)
            )
    return normalized
