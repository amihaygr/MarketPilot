"""XNYS market-session expectations used by bounded batch quality checks."""

from datetime import UTC, date, datetime
from functools import lru_cache

import exchange_calendars
import pandas as pd


@lru_cache(maxsize=512)
def expected_xnys_market_minutes(logical_date: date) -> int:
    """Return regular-session minutes, including early-close awareness, or zero."""
    calendar = exchange_calendars.get_calendar("XNYS")
    session = pd.Timestamp(logical_date)
    if not calendar.is_session(session):
        return 0
    session_open = calendar.session_open(session)
    session_close = calendar.session_close(session)
    return int((session_close - session_open).total_seconds() // 60)


def is_xnys_regular_market_minute(timestamp: datetime) -> bool:
    """Return whether a timezone-aware timestamp belongs to a regular XNYS session."""
    if timestamp.tzinfo is None or timestamp.utcoffset() is None:
        raise ValueError("timestamp must be timezone-aware")
    calendar = exchange_calendars.get_calendar("XNYS")
    return bool(calendar.is_open_on_minute(pd.Timestamp(timestamp), ignore_breaks=True))


@lru_cache(maxsize=512)
def xnys_session_bounds(logical_date: date) -> tuple[datetime, datetime]:
    """Return the regular XNYS session bounds as timezone-aware UTC datetimes."""
    calendar = exchange_calendars.get_calendar("XNYS")
    session = pd.Timestamp(logical_date)
    if not calendar.is_session(session):
        raise ValueError(f"{logical_date} is not an XNYS trading session")
    session_open = calendar.session_open(session).to_pydatetime().astimezone(UTC)
    session_close = calendar.session_close(session).to_pydatetime().astimezone(UTC)
    return session_open, session_close


@lru_cache(maxsize=128)
def xnys_session_windows(
    start_date: date, end_date: date
) -> tuple[tuple[date, datetime, datetime], ...]:
    """Return every regular XNYS session window in an inclusive date range."""
    if end_date < start_date:
        raise ValueError("XNYS session range end date must not precede start date")
    calendar = exchange_calendars.get_calendar("XNYS")
    sessions = calendar.sessions_in_range(pd.Timestamp(start_date), pd.Timestamp(end_date))
    return tuple(
        (
            session.date(),
            calendar.session_open(session).to_pydatetime().astimezone(UTC),
            calendar.session_close(session).to_pydatetime().astimezone(UTC),
        )
        for session in sessions
    )
