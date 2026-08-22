from datetime import UTC, datetime

from services.market_producer.main import build_synthetic_bar


def test_synthetic_bar_is_deterministic_within_a_minute() -> None:
    first = build_synthetic_bar("SPY", datetime(2026, 8, 22, 14, 30, 1, tzinfo=UTC), "1Min")
    second = build_synthetic_bar("SPY", datetime(2026, 8, 22, 14, 30, 59, tzinfo=UTC), "1Min")
    assert first == second
    assert first.source == "synthetic"
