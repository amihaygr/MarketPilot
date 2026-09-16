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

    def list_opportunities(self, *, symbols: list[str] | None = None) -> list[Row]: ...

    def opportunity_history(self, *, symbol: str, limit: int) -> list[Row]: ...

    def decision_model_status(self) -> Row: ...

    def list_market_bars(
        self,
        *,
        symbol: str,
        start_utc: datetime,
        end_utc: datetime,
        certification_status: str | None,
        source_name: str | None,
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

    def list_backtest_runs(self, *, page: int, page_size: int) -> Row: ...

    def get_backtest_run(self, *, run_id: str) -> Row | None: ...

    def list_backtest_equity(self, *, run_id: str, symbol: str) -> list[Row]: ...

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

    def list_opportunities(self, *, symbols: list[str] | None = None) -> list[Row]:
        parameters: tuple[Any, ...] = ()
        symbol_filter = ""
        if symbols:
            placeholders = ",".join(["%s"] * len(symbols))
            symbol_filter = f"AND symbols.symbol IN ({placeholders})"
            parameters = tuple(symbols)
        rows = self._fetch_all(
            f"""
            SELECT r.recommendation_id, symbols.symbol, r.as_of_utc,
                   r.market_data_time_utc, r.fundamentals_as_of_utc, r.action,
                   r.actionable, r.lifecycle_status, r.technical_score,
                   r.fundamental_score, r.opportunity_score, r.confidence,
                   r.market_price, r.buy_zone_low, r.buy_zone_high, r.stop_price,
                   r.target_1, r.target_2, r.risk_reward_1, r.risk_reward_2,
                   r.potential_profit_1_pct, r.potential_profit_2_pct,
                   r.valid_until_utc, r.feed_name, r.model_version, r.explanation_json,
                   p.success_probability,p.expected_r,
                   COALESCE(p.model_status,'FALLBACK') model_status,
                   p.model_version probability_model_version,
                   p.top_positive_drivers_json,p.top_negative_drivers_json,
                   registry.trained_through_date,p.calibration_status
            FROM fact_opportunity_recommendation r
            JOIN dim_symbol symbols ON symbols.symbol_id=r.symbol_id
            LEFT JOIN fact_decision_model_prediction p
              ON p.recommendation_id=r.recommendation_id
             AND p.model_version=(
                 SELECT p2.model_version FROM fact_decision_model_prediction p2
                 WHERE p2.recommendation_id=r.recommendation_id
                 ORDER BY (p2.model_status='ACTIVE') DESC,p2.scored_at_utc DESC LIMIT 1
             )
            LEFT JOIN decision_model_registry registry ON registry.model_version=p.model_version
            JOIN (
                SELECT symbol_id, MAX(as_of_utc) AS latest
                FROM fact_opportunity_recommendation GROUP BY symbol_id
            ) latest ON latest.symbol_id=r.symbol_id AND latest.latest=r.as_of_utc
            WHERE 1=1 {symbol_filter}
            ORDER BY COALESCE(p.expected_r,-999) DESC, r.opportunity_score DESC, symbols.symbol
            """,
            parameters,
        )
        return [_public_opportunity(row) for row in rows]

    def opportunity_history(self, *, symbol: str, limit: int) -> list[Row]:
        rows = self._fetch_all(
            """
            SELECT r.recommendation_id, symbols.symbol, r.as_of_utc,
                   r.market_data_time_utc, r.fundamentals_as_of_utc, r.action,
                   r.actionable, r.lifecycle_status, r.technical_score,
                   r.fundamental_score, r.opportunity_score, r.confidence,
                   r.market_price, r.buy_zone_low, r.buy_zone_high, r.stop_price,
                   r.target_1, r.target_2, r.risk_reward_1, r.risk_reward_2,
                   r.potential_profit_1_pct, r.potential_profit_2_pct,
                   r.valid_until_utc, r.feed_name, r.model_version, r.explanation_json,
                   p.success_probability,p.expected_r,
                   COALESCE(p.model_status,'FALLBACK') model_status,
                   p.model_version probability_model_version,
                   p.top_positive_drivers_json,p.top_negative_drivers_json,
                   registry.trained_through_date,p.calibration_status
            FROM fact_opportunity_recommendation r
            JOIN dim_symbol symbols ON symbols.symbol_id=r.symbol_id
            LEFT JOIN fact_decision_model_prediction p
              ON p.recommendation_id=r.recommendation_id
             AND p.model_version=(
                 SELECT p2.model_version FROM fact_decision_model_prediction p2
                 WHERE p2.recommendation_id=r.recommendation_id
                 ORDER BY (p2.model_status='ACTIVE') DESC,p2.scored_at_utc DESC LIMIT 1
             )
            LEFT JOIN decision_model_registry registry ON registry.model_version=p.model_version
            WHERE symbols.symbol=%s ORDER BY r.as_of_utc DESC LIMIT %s
            """,
            (symbol, limit),
        )
        return [_public_opportunity(row) for row in rows]

    def decision_model_status(self) -> Row:
        rows = self._fetch_all(
            """
            SELECT model_version,model_family,status,feature_schema_version,
                   trained_from_date,trained_through_date,activation_threshold,
                   calibration_method,promotion_eligible,promotion_reasons_json,metrics_json
            FROM decision_model_registry
            ORDER BY (status='ACTIVE') DESC,created_at_utc DESC LIMIT 1
            """
        )
        if not rows:
            return {
                "model_version": "decision-intelligence-v2-hybrid",
                "model_family": None,
                "status": "FALLBACK",
                "feature_schema_version": 2,
                "trained_from_date": None,
                "trained_through_date": None,
                "activation_threshold": "0.60",
                "calibration_method": None,
                "promotion_eligible": False,
                "promotion_reasons": ["no trained model is registered"],
                "metrics": {},
            }
        row = _normalize_datetimes(rows[0])
        for source, target in (
            ("promotion_reasons_json", "promotion_reasons"),
            ("metrics_json", "metrics"),
        ):
            raw = row.pop(source)
            row[target] = raw if isinstance(raw, (list, dict)) else __import__("json").loads(raw)
        return row

    def decision_alerts(self, *, limit: int) -> list[Row]:
        rows = self._fetch_all(
            """
            SELECT a.alert_id,s.symbol,a.alert_type,a.severity,a.title,a.message,a.created_at_utc
            FROM fact_decision_alert a JOIN dim_symbol s ON s.symbol_id=a.symbol_id
            ORDER BY a.created_at_utc DESC LIMIT %s
            """,
            (limit,),
        )
        return [_normalize_datetimes(row) for row in rows]

    def decision_evaluation_status(self) -> Row:
        rows = self._fetch_all(
            """
            SELECT s.model_version,s.required_sessions,s.completed_sessions,
                   s.first_session_date,s.latest_session_date,s.promotion_status,
                   COUNT(e.recommendation_id) evaluated_recommendations,
                   ROUND(100*AVG(e.outcome IN ('TARGET_1','TARGET_2')),2) hit_rate_pct,
                   ROUND(AVG(e.realized_return_pct),4) average_return_pct,
                   (SELECT COUNT(DISTINCT DATE(b.event_time_utc))
                      FROM fact_market_bar_1m b
                     WHERE b.certification_status='CERTIFIED') historical_certified_sessions,
                   (SELECT MIN(DATE(b.event_time_utc)) FROM fact_market_bar_1m b
                     WHERE b.certification_status='CERTIFIED') historical_first_session_date,
                   (SELECT MAX(DATE(b.event_time_utc)) FROM fact_market_bar_1m b
                     WHERE b.certification_status='CERTIFIED') historical_latest_session_date,
                   (SELECT COUNT(*) FROM fact_backtest_run b
                     WHERE b.status='PUBLISHED') published_backtest_runs
            FROM shadow_mode_status s
            LEFT JOIN fact_opportunity_recommendation r ON r.model_version=s.model_version
            LEFT JOIN fact_recommendation_evaluation e ON e.recommendation_id=r.recommendation_id
                AND e.horizon_sessions=5
            WHERE s.model_version='decision-intelligence-v1'
            GROUP BY s.model_version,s.required_sessions,s.completed_sessions,
                     s.first_session_date,s.latest_session_date,s.promotion_status
            """
        )
        if not rows:
            raise RuntimeError("decision evaluation status is missing")
        return _normalize_datetimes(rows[0])

    def list_market_bars(
        self,
        *,
        symbol: str,
        start_utc: datetime,
        end_utc: datetime,
        certification_status: str | None,
        source_name: str | None,
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
        if source_name:
            predicates.append("bars.source_name = %s")
            parameters.append(source_name)
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

    def list_backtest_runs(self, *, page: int, page_size: int) -> Row:
        result = self._page(
            "SELECT COUNT(*) AS total FROM fact_backtest_run",
            """
            SELECT run_id, strategy_code, strategy_version, start_date, end_date,
                   symbols_csv, benchmark_symbol, short_window, long_window,
                   initial_capital, transaction_cost_bps, slippage_bps, status,
                   schema_version, started_at_utc, completed_at_utc
            FROM fact_backtest_run
            ORDER BY started_at_utc DESC, run_id DESC
            LIMIT %s OFFSET %s
            """,
            [],
            page,
            page_size,
        )
        result["items"] = [_public_backtest_run(row) for row in result["items"]]
        return result

    def get_backtest_run(self, *, run_id: str) -> Row | None:
        rows = self._fetch_all(
            """
            SELECT run_id, strategy_code, strategy_version, start_date, end_date,
                   symbols_csv, benchmark_symbol, short_window, long_window,
                   initial_capital, transaction_cost_bps, slippage_bps, status,
                   schema_version, started_at_utc, completed_at_utc
            FROM fact_backtest_run WHERE run_id=%s
            """,
            (run_id,),
        )
        if not rows:
            return None
        results = self._fetch_all(
            """
            SELECT symbols.symbol, results.first_event_time_utc,
                   results.last_event_time_utc, results.observation_count,
                   results.trade_count, results.total_return_pct,
                   results.benchmark_return_pct, results.excess_return_pct,
                   results.max_drawdown_pct, results.annualized_volatility_pct,
                   results.sharpe_ratio
            FROM fact_backtest_result AS results
            JOIN dim_symbol AS symbols ON symbols.symbol_id=results.symbol_id
            WHERE results.run_id=%s
            ORDER BY symbols.symbol
            """,
            (run_id,),
        )
        return {
            "run": _public_backtest_run(_normalize_datetimes(rows[0])),
            "results": [_normalize_datetimes(row) for row in results],
        }

    def list_backtest_equity(self, *, run_id: str, symbol: str) -> list[Row]:
        rows = self._fetch_all(
            """
            SELECT symbols.symbol, equity.trading_date, equity.event_time_utc,
                   equity.equity, equity.benchmark_equity, equity.drawdown_pct,
                   equity.applied_position
            FROM fact_backtest_equity_daily AS equity
            JOIN dim_symbol AS symbols ON symbols.symbol_id=equity.symbol_id
            WHERE equity.run_id=%s AND symbols.symbol=%s
            ORDER BY equity.trading_date
            LIMIT 367
            """,
            (run_id, symbol),
        )
        return [_normalize_datetimes(row) for row in rows]

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


def _public_backtest_run(row: Row) -> Row:
    public = dict(row)
    public["symbols"] = [value for value in str(public.pop("symbols_csv")).split(",") if value]
    return public


def _public_opportunity(row: Row) -> Row:
    public = _normalize_datetimes(row)
    raw = public.pop("explanation_json", "[]")
    public["explanations"] = raw if isinstance(raw, list) else __import__("json").loads(raw)
    for source, target in (
        ("top_positive_drivers_json", "top_positive_drivers"),
        ("top_negative_drivers_json", "top_negative_drivers"),
    ):
        raw_drivers = public.pop(source, None)
        public[target] = (
            raw_drivers
            if isinstance(raw_drivers, list)
            else __import__("json").loads(raw_drivers or "[]")
        )
    public["model_status"] = public.get("model_status") or "FALLBACK"
    public["calibration_status"] = public.get("calibration_status") or "UNAVAILABLE"
    return public
