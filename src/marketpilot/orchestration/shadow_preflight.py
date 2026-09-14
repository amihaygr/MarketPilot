"""Post-market guardrails for Decision Intelligence shadow-mode progress."""

from __future__ import annotations

import json
import os
from collections.abc import Mapping
from datetime import date
from typing import Any

import pymysql
from pymysql.cursors import DictCursor

MODEL_VERSION = "decision-intelligence-v1"


def validate_shadow_progress(
    *,
    logical_date: date,
    status: Mapping[str, Any],
    certified_sessions: int,
    recommendations_for_session: int,
) -> dict[str, object]:
    """Validate that the completed daily run is represented in the shadow counter."""
    required_sessions = int(status["required_sessions"])
    completed_sessions = int(status["completed_sessions"])
    expected_completed = min(required_sessions, int(certified_sessions))
    latest_session = status.get("latest_session_date")

    if latest_session != logical_date:
        raise RuntimeError(
            "shadow progress did not reach the processed session: "
            f"expected={logical_date.isoformat()} actual={latest_session}"
        )
    if recommendations_for_session < 1:
        raise RuntimeError(
            f"no certified recommendations were published for {logical_date.isoformat()}"
        )
    if completed_sessions != expected_completed:
        raise RuntimeError(
            "shadow counter does not match certified recommendation sessions: "
            f"counter={completed_sessions} expected={expected_completed}"
        )

    return {
        "event": "shadow_progress_verified",
        "logical_date": logical_date.isoformat(),
        "completed_sessions": completed_sessions,
        "required_sessions": required_sessions,
        "recommendations_for_session": recommendations_for_session,
        "promotion_status": str(status["promotion_status"]),
    }


def verify_shadow_progress(logical_date_value: str, run_id: str) -> dict[str, object]:
    """Read Gold state after the daily pipeline and fail closed on missing progress."""
    logical_date = date.fromisoformat(logical_date_value)
    connection = pymysql.connect(
        host=os.environ["MARIADB_HOST"],
        port=int(os.environ.get("MARIADB_PORT", "3306")),
        database=os.environ["MARIADB_DATABASE"],
        user=os.environ["MARIADB_PUBLISH_USER"],
        password=os.environ["MARIADB_PUBLISH_PASSWORD"],
        charset="utf8mb4",
        cursorclass=DictCursor,
    )
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT required_sessions,completed_sessions,latest_session_date,promotion_status
                FROM shadow_mode_status WHERE model_version=%s
                """,
                (MODEL_VERSION,),
            )
            status = cursor.fetchone()
            if status is None:
                raise RuntimeError(f"shadow status is missing for {MODEL_VERSION}")
            cursor.execute(
                """
                SELECT COUNT(DISTINCT DATE(as_of_utc)) AS certified_sessions
                FROM fact_opportunity_recommendation
                WHERE model_version=%s AND lifecycle_status='CERTIFIED'
                """,
                (MODEL_VERSION,),
            )
            certified_sessions = int(cursor.fetchone()["certified_sessions"] or 0)
            cursor.execute(
                """
                SELECT COUNT(*) AS recommendations
                FROM fact_opportunity_recommendation
                WHERE model_version=%s AND lifecycle_status='CERTIFIED'
                  AND DATE(as_of_utc)=%s AND pipeline_run_id=%s
                """,
                (MODEL_VERSION, logical_date, run_id),
            )
            recommendations = int(cursor.fetchone()["recommendations"] or 0)
    finally:
        connection.close()

    result = validate_shadow_progress(
        logical_date=logical_date,
        status=status,
        certified_sessions=certified_sessions,
        recommendations_for_session=recommendations,
    )
    print(json.dumps(result, separators=(",", ":"), sort_keys=True))
    return result
