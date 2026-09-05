"""Validated settings for bounded Alpaca historical market-data ingestion."""

from dataclasses import dataclass
from os import environ
from urllib.parse import urlparse


@dataclass(frozen=True, slots=True)
class HistoricalSettings:
    base_url: str
    api_key: str
    api_secret: str
    feed: str
    request_timeout_seconds: float
    request_max_attempts: int
    max_requests_per_second: float
    page_limit: int
    kafka_bootstrap_servers: str
    kafka_topic: str
    bronze_wait_timeout_seconds: float
    bronze_poll_seconds: float
    minio_endpoint: str
    minio_access_key: str
    minio_secret_key: str
    bronze_bucket: str
    configured_symbols: tuple[str, ...]

    @classmethod
    def from_env(cls) -> "HistoricalSettings":
        base_url = environ.get(
            "ALPACA_HISTORICAL_BASE_URL",
            "https://data.alpaca.markets/v2/stocks/bars",
        ).rstrip("/")
        if urlparse(base_url).scheme != "https":
            raise ValueError("ALPACA_HISTORICAL_BASE_URL must use HTTPS")
        feed = environ.get("ALPACA_DATA_FEED", "iex").strip().lower()
        if feed not in {"iex", "sip"}:
            raise ValueError("historical stock backfill supports only iex or sip")
        timeout = float(environ.get("ALPACA_HISTORICAL_TIMEOUT_SECONDS", "30"))
        attempts = int(environ.get("ALPACA_HISTORICAL_MAX_ATTEMPTS", "4"))
        rate = float(environ.get("ALPACA_HISTORICAL_REQUESTS_PER_SECOND", "2"))
        page_limit = int(environ.get("ALPACA_HISTORICAL_PAGE_LIMIT", "10000"))
        wait_timeout = float(environ.get("HISTORICAL_BRONZE_WAIT_TIMEOUT_SECONDS", "180"))
        poll_seconds = float(environ.get("HISTORICAL_BRONZE_POLL_SECONDS", "1"))
        if timeout <= 0 or attempts < 1:
            raise ValueError("historical request timeout and attempts must be positive")
        if rate <= 0 or rate > 10:
            raise ValueError("ALPACA_HISTORICAL_REQUESTS_PER_SECOND must be in (0, 10]")
        if not 1 <= page_limit <= 10000:
            raise ValueError("ALPACA_HISTORICAL_PAGE_LIMIT must be in [1, 10000]")
        if wait_timeout <= 0 or poll_seconds <= 0 or poll_seconds > wait_timeout:
            raise ValueError("historical Bronze barrier timing is invalid")
        symbols = tuple(
            sorted(
                {
                    symbol.strip().upper()
                    for symbol in environ["MARKET_SYMBOLS"].split(",")
                    if symbol.strip()
                }
            )
        )
        if not symbols:
            raise ValueError("MARKET_SYMBOLS must contain at least one symbol")
        settings = cls(
            base_url=base_url,
            api_key=environ["ALPACA_API_KEY"].strip(),
            api_secret=environ["ALPACA_API_SECRET"].strip(),
            feed=feed,
            request_timeout_seconds=timeout,
            request_max_attempts=attempts,
            max_requests_per_second=rate,
            page_limit=page_limit,
            kafka_bootstrap_servers=environ["KAFKA_BOOTSTRAP_SERVERS"],
            kafka_topic=environ.get(
                "KAFKA_HISTORICAL_BARS_TOPIC",
                "market.bars.1m.backfill.v1",
            ),
            bronze_wait_timeout_seconds=wait_timeout,
            bronze_poll_seconds=poll_seconds,
            minio_endpoint=environ["MINIO_ENDPOINT"],
            minio_access_key=environ["MINIO_ROOT_USER"],
            minio_secret_key=environ["MINIO_ROOT_PASSWORD"],
            bronze_bucket=environ["MINIO_BRONZE_BUCKET"],
            configured_symbols=symbols,
        )
        settings.validate_credentials()
        return settings

    def validate_credentials(self) -> None:
        if not self.api_key or not self.api_secret:
            raise ValueError("Alpaca historical backfill requires API credentials")
        if self.api_key.lower() == "replace_me" or self.api_secret.lower() == "replace_me":
            raise ValueError("replace Alpaca credential placeholders before historical backfill")
