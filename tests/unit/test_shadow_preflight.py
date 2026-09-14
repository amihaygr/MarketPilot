from datetime import date

import pytest

from marketpilot.orchestration.shadow_preflight import validate_shadow_progress


def _status(**overrides: object) -> dict[str, object]:
    value: dict[str, object] = {
        "required_sessions": 20,
        "completed_sessions": 2,
        "latest_session_date": date(2026, 9, 14),
        "promotion_status": "COLLECTING",
    }
    value.update(overrides)
    return value


def test_shadow_preflight_accepts_current_certified_progress() -> None:
    result = validate_shadow_progress(
        logical_date=date(2026, 9, 14),
        status=_status(),
        certified_sessions=2,
        recommendations_for_session=11,
    )

    assert result["event"] == "shadow_progress_verified"
    assert result["completed_sessions"] == 2


@pytest.mark.parametrize(
    ("status", "certified_sessions", "recommendations", "message"),
    [
        (_status(latest_session_date=date(2026, 9, 13)), 2, 11, "did not reach"),
        (_status(), 2, 0, "no certified recommendations"),
        (_status(completed_sessions=1), 2, 11, "does not match"),
    ],
)
def test_shadow_preflight_fails_closed(
    status: dict[str, object],
    certified_sessions: int,
    recommendations: int,
    message: str,
) -> None:
    with pytest.raises(RuntimeError, match=message):
        validate_shadow_progress(
            logical_date=date(2026, 9, 14),
            status=status,
            certified_sessions=certified_sessions,
            recommendations_for_session=recommendations,
        )
