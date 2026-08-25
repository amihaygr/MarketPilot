"""XNYS market-session expectations used by bounded batch quality checks."""

from datetime import date
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
