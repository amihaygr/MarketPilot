"""Environment-backed settings with fail-fast validation."""

from dataclasses import dataclass
from os import environ


@dataclass(frozen=True, slots=True)
class Settings:
    kafka_bootstrap_servers: str
    market_bars_topic: str
    symbols: tuple[str, ...]
    market_bar_interval: str
    synthetic_publish_seconds: int
    market_data_source: str
    alpaca_data_feed: str
    alpaca_data_timeout_seconds: float | None
    alpaca_reconnect_initial_seconds: float
    alpaca_reconnect_max_seconds: float

    @classmethod
    def from_env(cls) -> "Settings":
        symbols = tuple(
            symbol.strip().upper()
            for symbol in environ["MARKET_SYMBOLS"].split(",")
            if symbol.strip()
        )
        if not symbols:
            raise ValueError("MARKET_SYMBOLS must contain at least one symbol")
        publish_seconds = int(environ.get("SYNTHETIC_PUBLISH_SECONDS", "60"))
        if publish_seconds < 1:
            raise ValueError("SYNTHETIC_PUBLISH_SECONDS must be positive")
        source = environ.get("MARKET_DATA_SOURCE", "synthetic").strip().lower()
        if source not in {"synthetic", "alpaca"}:
            raise ValueError("MARKET_DATA_SOURCE must be synthetic or alpaca")
        feed = environ.get("ALPACA_DATA_FEED", "iex").strip().lower()
        if feed not in {"iex", "sip", "delayed_sip", "boats", "overnight"}:
            raise ValueError("ALPACA_DATA_FEED is not supported")
        data_timeout = float(environ.get("ALPACA_DATA_TIMEOUT_SECONDS", "0"))
        if data_timeout < 0:
            raise ValueError("ALPACA_DATA_TIMEOUT_SECONDS must be non-negative")
        reconnect_initial = float(environ.get("ALPACA_RECONNECT_INITIAL_SECONDS", "1"))
        reconnect_max = float(environ.get("ALPACA_RECONNECT_MAX_SECONDS", "60"))
        if reconnect_initial <= 0 or reconnect_max < reconnect_initial:
            raise ValueError("Alpaca reconnect delays are invalid")
        return cls(
            kafka_bootstrap_servers=environ["KAFKA_BOOTSTRAP_SERVERS"],
            market_bars_topic=environ["KAFKA_MARKET_BARS_TOPIC"],
            symbols=symbols,
            market_bar_interval=environ.get("MARKET_BAR_INTERVAL", "1Min"),
            synthetic_publish_seconds=publish_seconds,
            market_data_source=source,
            alpaca_data_feed=feed,
            alpaca_data_timeout_seconds=data_timeout or None,
            alpaca_reconnect_initial_seconds=reconnect_initial,
            alpaca_reconnect_max_seconds=reconnect_max,
        )
