"""Operational alert state transitions without transport side effects."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CheckResult:
    name: str
    healthy: bool
    detail: str


@dataclass(frozen=True, slots=True)
class AlertEvent:
    name: str
    state: str
    detail: str


class AlertState:
    """Emit one alert on failure and one resolution when the check recovers."""

    def __init__(self) -> None:
        self._states: dict[str, bool] = {}

    def observe(self, result: CheckResult) -> AlertEvent | None:
        previous = self._states.get(result.name)
        self._states[result.name] = result.healthy
        if previous is None and result.healthy:
            return None
        if previous == result.healthy:
            return None
        return AlertEvent(
            name=result.name,
            state="RESOLVED" if result.healthy else "ALERT",
            detail=result.detail,
        )
