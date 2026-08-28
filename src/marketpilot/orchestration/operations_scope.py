"""Materialize finite, retry-stable Airflow scopes for Phase 8 operations."""

from __future__ import annotations

from datetime import date
from uuid import NAMESPACE_URL, uuid5

from marketpilot.operations.archive import resolve_archive_scope
from marketpilot.operations.compaction import compaction_dates


def prepare_compaction_scope(
    through_date_value: str,
    lookback_days: int,
    airflow_run_id: str,
) -> dict[str, object]:
    through_date = date.fromisoformat(through_date_value)
    run_id = _stable_run_id("compaction", airflow_run_id, through_date.isoformat())
    dates = compaction_dates(through_date, int(lookback_days), run_id)
    return {
        "through_date": through_date.isoformat(),
        "lookback_days": len(dates),
        "run_id": run_id,
    }


def prepare_archive_scope(
    *,
    logical_date_value: str,
    archive_year_override: int | None,
    archive_version: int,
    airflow_run_id: str,
) -> dict[str, object]:
    logical_date = date.fromisoformat(logical_date_value)
    archive_year = (
        int(archive_year_override) if archive_year_override is not None else logical_date.year - 1
    )
    run_id = _stable_run_id(
        "archive",
        airflow_run_id,
        f"{archive_year}:v{int(archive_version)}",
    )
    scope = resolve_archive_scope(
        archive_year=archive_year,
        archive_version=int(archive_version),
        run_id=run_id,
        current_year=logical_date.year,
    )
    return {
        "archive_year": scope.archive_year,
        "archive_version": scope.archive_version,
        "run_id": scope.run_id,
    }


def _stable_run_id(kind: str, airflow_run_id: str, scope: str) -> str:
    return str(uuid5(NAMESPACE_URL, f"marketpilot:{kind}:{airflow_run_id}:{scope}"))
