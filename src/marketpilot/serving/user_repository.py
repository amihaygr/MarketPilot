"""Least-privilege persistence for local watchlist and portfolio preferences."""

from __future__ import annotations

from typing import Any

import pymysql
from pymysql.cursors import DictCursor

from marketpilot.serving.settings import ServingSettings


class UserStateUnavailable(RuntimeError):
    pass


class MariaDbUserRepository:
    def __init__(self, settings: ServingSettings) -> None:
        self.settings = settings

    def _connect(self) -> pymysql.Connection[DictCursor]:
        if not self.settings.mariadb_write_user or not self.settings.mariadb_write_password:
            raise UserStateUnavailable("user-state writer is not configured")
        return pymysql.connect(
            host=self.settings.mariadb_host,
            port=self.settings.mariadb_port,
            database=self.settings.mariadb_database,
            user=self.settings.mariadb_write_user,
            password=self.settings.mariadb_write_password,
            charset="utf8mb4",
            autocommit=False,
            connect_timeout=self.settings.query_timeout_seconds,
            cursorclass=DictCursor,
        )

    def get(self) -> dict[str, Any]:
        connection = self._connect()
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """SELECT portfolio_id,equity,cash_balance,risk_per_trade_pct,
                        max_symbol_exposure_pct,max_open_risk_pct
                    FROM user_portfolio WHERE portfolio_key='local-default'"""
                )
                state = cursor.fetchone()
                if not state:
                    raise UserStateUnavailable("local portfolio is missing")
                cursor.execute(
                    """
                    SELECT s.symbol FROM user_watchlist_symbol w
                    JOIN dim_symbol s ON s.symbol_id=w.symbol_id
                    WHERE w.portfolio_id=%s ORDER BY s.symbol
                    """,
                    (state["portfolio_id"],),
                )
                symbols = [row["symbol"] for row in cursor.fetchall()]
            state.pop("portfolio_id")
            return {**state, "symbols": symbols}
        finally:
            connection.close()

    def update(self, payload: dict[str, Any]) -> dict[str, Any]:
        symbols = sorted(set(payload.pop("symbols")))
        connection = self._connect()
        try:
            with connection.cursor() as cursor:
                placeholders = ",".join(["%s"] * len(symbols))
                cursor.execute(
                    f"SELECT symbol FROM dim_symbol WHERE symbol IN ({placeholders})",
                    tuple(symbols),
                )
                known = {row["symbol"] for row in cursor.fetchall()}
                if known != set(symbols):
                    raise ValueError(f"unknown symbols: {', '.join(sorted(set(symbols) - known))}")
                cursor.execute(
                    """
                    UPDATE user_portfolio SET equity=%s,cash_balance=%s,risk_per_trade_pct=%s,
                        max_symbol_exposure_pct=%s,max_open_risk_pct=%s
                    WHERE portfolio_key='local-default'
                    """,
                    (
                        payload["equity"],
                        payload["cash_balance"],
                        payload["risk_per_trade_pct"],
                        payload["max_symbol_exposure_pct"],
                        payload["max_open_risk_pct"],
                    ),
                )
                cursor.execute(
                    "SELECT portfolio_id FROM user_portfolio WHERE portfolio_key='local-default'"
                )
                portfolio_id = cursor.fetchone()["portfolio_id"]
                cursor.execute(
                    "DELETE FROM user_watchlist_symbol WHERE portfolio_id=%s", (portfolio_id,)
                )
                cursor.executemany(
                    """INSERT INTO user_watchlist_symbol (portfolio_id,symbol_id)
                    SELECT %s,symbol_id FROM dim_symbol WHERE symbol=%s""",
                    [(portfolio_id, symbol) for symbol in symbols],
                )
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()
        return self.get()
