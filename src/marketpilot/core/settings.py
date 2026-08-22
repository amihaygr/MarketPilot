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
        return cls(
            kafka_bootstrap_servers=environ["KAFKA_BOOTSTRAP_SERVERS"],
            market_bars_topic=environ["KAFKA_MARKET_BARS_TOPIC"],
            symbols=symbols,
            market_bar_interval=environ.get("MARKET_BAR_INTERVAL", "1Min"),
            synthetic_publish_seconds=publish_seconds,
        )
