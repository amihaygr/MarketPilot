"""Validate and materialize bounded Airflow batch scopes."""

from __future__ import annotations

import json
import math
from datetime import date, timedelta
from uuid import NAMESPACE_URL, uuid5

from marketpilot.batch.market_calendar import expected_xnys_market_minutes

MAX_BACKFILL_DAYS = 31


def prepare_daily_scope(
    logical_date_value: str,
    airflow_run_id: str,
    expected_bars_override: int | None = None,
) -> dict[str, object] | None:
    """Return one session scope, or ``None`` when the exchange is closed."""
    logical_date = date.fromisoformat(logical_date_value)
    expected_bars = _expected_bars(logical_date, expected_bars_override)
    if expected_bars == 0:
        return None
    return {
        "logical_date": logical_date.isoformat(),
        "run_id": _stable_run_id("daily", airflow_run_id, logical_date.isoformat()),
        "expected_bars_per_symbol": expected_bars,
    }


def prepare_backfill_arguments(
    *,
    start_date_value: str,
    end_date_value: str,
    requested_symbols: list[str],
    configured_symbols: tuple[str, ...],
    airflow_run_id: str,
    expected_bars_override: int | None = None,
    minimum_coverage_pct: int = 100,
    maximum_ingestion_lag_seconds: int | None = None,
) -> dict[str, list[list[str]]]:
    """Build mapped Spark arguments for a validated, finite replay scope."""
    start_date = date.fromisoformat(start_date_value)
    end_date = date.fromisoformat(end_date_value)
    if end_date < start_date:
        raise ValueError("end_date must be on or after start_date")
    inclusive_days = (end_date - start_date).days + 1
    if inclusive_days > MAX_BACKFILL_DAYS:
        raise ValueError(f"backfill scope cannot exceed {MAX_BACKFILL_DAYS} calendar days")
    if not 1 <= int(minimum_coverage_pct) <= 100:
        raise ValueError("minimum_coverage_pct must be in [1, 100]")
    if maximum_ingestion_lag_seconds is not None and maximum_ingestion_lag_seconds < 1:
        raise ValueError("maximum_ingestion_lag_seconds must be positive")

    configured = _normalize_symbols(list(configured_symbols))
    requested = _normalize_symbols(requested_symbols)
    unknown = sorted(set(requested) - set(configured))
    if unknown:
        raise ValueError(f"symbols are outside MARKET_SYMBOLS: {','.join(unknown)}")

    symbols_json = json.dumps(requested, separators=(",", ":"))
    scope_suffix = ",".join(requested)
    arguments: dict[str, list[list[str]]] = {"bronze": [], "quality": [], "gold": []}
    for day_offset in range(inclusive_days):
        logical_date = start_date + timedelta(days=day_offset)
        expected_bars = _expected_bars(logical_date, expected_bars_override)
        if expected_bars == 0:
            continue
        if expected_bars_override is None:
            expected_bars = math.ceil(expected_bars * int(minimum_coverage_pct) / 100)
        date_value = logical_date.isoformat()
        partition_key = f"{date_value}|symbols={scope_suffix}"
        run_id = _stable_run_id("backfill", airflow_run_id, partition_key)
        common = ["--logical-date", date_value, "--run-id", run_id]
        arguments["bronze"].append([*common, "--symbols-json", symbols_json])
        quality = [
            *common,
            "--expected-symbols-json",
            symbols_json,
            "--expected-bars-per-symbol",
            str(expected_bars),
            "--partition-key",
            partition_key,
        ]
        if maximum_ingestion_lag_seconds is not None:
            quality.extend(["--maximum-ingestion-lag-seconds", str(maximum_ingestion_lag_seconds)])
        arguments["quality"].append(quality)
        arguments["gold"].append(
            [
                *common,
                "--symbols-json",
                symbols_json,
                "--partition-key",
                partition_key,
            ]
        )

    if not arguments["bronze"]:
        raise ValueError("backfill scope contains no XNYS trading sessions")
    return arguments


def configured_market_symbols(raw_symbols: str) -> tuple[str, ...]:
    """Parse the configured market universe without silently accepting an empty value."""
    return tuple(_normalize_symbols(raw_symbols.split(",")))


def _expected_bars(logical_date: date, override: int | None) -> int:
    if override is not None:
        expected = int(override)
        if expected < 1:
            raise ValueError("expected_bars_override must be positive")
        return expected
    return expected_xnys_market_minutes(logical_date)


def _normalize_symbols(symbols: list[str]) -> list[str]:
    normalized = sorted({str(symbol).strip().upper() for symbol in symbols if str(symbol).strip()})
    if not normalized:
        raise ValueError("at least one symbol is required")
    return normalized


def _stable_run_id(kind: str, airflow_run_id: str, scope: str) -> str:
    return str(uuid5(NAMESPACE_URL, f"marketpilot:{kind}:{airflow_run_id}:{scope}"))
