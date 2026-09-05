"""Retrying client for Alpaca's multi-symbol historical stock-bars endpoint."""

import json
import logging
import time
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

logger = logging.getLogger(__name__)


class ResponseLike(Protocol):
    def __enter__(self) -> "ResponseLike": ...

    def __exit__(self, *args: object) -> None: ...

    def read(self) -> bytes: ...


OpenUrl = Callable[..., ResponseLike]


@dataclass(frozen=True, slots=True)
class HistoricalPage:
    payload: bytes
    decoded: dict[str, Any]
    page_number: int


class RequestRateLimiter:
    def __init__(
        self,
        requests_per_second: float,
        *,
        clock: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        if requests_per_second <= 0:
            raise ValueError("requests_per_second must be positive")
        self.minimum_interval = 1.0 / requests_per_second
        self.clock = clock
        self.sleep = sleep
        self.last_request_at: float | None = None

    def wait(self) -> None:
        now = self.clock()
        if self.last_request_at is not None:
            remaining = self.minimum_interval - (now - self.last_request_at)
            if remaining > 0:
                self.sleep(remaining)
        self.last_request_at = self.clock()


class AlpacaHistoricalClient:
    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        api_secret: str,
        feed: str,
        timeout_seconds: float,
        max_attempts: int,
        requests_per_second: float,
        page_limit: int,
        opener: OpenUrl = urlopen,
        sleep: Callable[[float], None] = time.sleep,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.base_url = base_url
        self.api_key = api_key
        self.api_secret = api_secret
        self.feed = feed
        self.timeout_seconds = timeout_seconds
        self.max_attempts = max_attempts
        self.page_limit = page_limit
        self.opener = opener
        self.sleep = sleep
        self.rate_limiter = RequestRateLimiter(
            requests_per_second,
            clock=clock,
            sleep=sleep,
        )

    def pages(
        self,
        *,
        symbols: tuple[str, ...],
        start_utc: datetime,
        end_utc: datetime,
    ) -> Iterator[HistoricalPage]:
        page_token: str | None = None
        page_number = 0
        while True:
            page_number += 1
            if page_number > 100:
                raise RuntimeError("Alpaca historical pagination exceeded 100 pages")
            query = {
                "symbols": ",".join(symbols),
                "timeframe": "1Min",
                "start": start_utc.isoformat().replace("+00:00", "Z"),
                "end": end_utc.isoformat().replace("+00:00", "Z"),
                "limit": str(self.page_limit),
                "adjustment": "raw",
                "feed": self.feed,
                "sort": "asc",
            }
            if page_token:
                query["page_token"] = page_token
            payload = self._get(f"{self.base_url}?{urlencode(query)}")
            decoded = json.loads(payload)
            if not isinstance(decoded, dict) or not isinstance(decoded.get("bars"), dict):
                raise ValueError("Alpaca historical response must contain a bars object")
            yield HistoricalPage(payload=payload, decoded=decoded, page_number=page_number)
            raw_token = decoded.get("next_page_token")
            page_token = str(raw_token) if raw_token else None
            if page_token is None:
                return

    def _get(self, url: str) -> bytes:
        for attempt in range(1, self.max_attempts + 1):
            self.rate_limiter.wait()
            request = Request(
                url,
                headers={
                    "APCA-API-KEY-ID": self.api_key,
                    "APCA-API-SECRET-KEY": self.api_secret,
                    "Accept": "application/json",
                },
            )
            try:
                with self.opener(request, timeout=self.timeout_seconds) as response:
                    return response.read()
            except HTTPError as error:
                retryable = error.code == 429 or 500 <= error.code < 600
                if not retryable or attempt == self.max_attempts:
                    raise
                retry_after = error.headers.get("Retry-After") if error.headers else None
                delay = float(retry_after) if retry_after else min(2 ** (attempt - 1), 30)
            except (URLError, TimeoutError):
                if attempt == self.max_attempts:
                    raise
                delay = min(2 ** (attempt - 1), 30)
            logger.warning(
                "Alpaca historical request retry attempt=%d delay_seconds=%s",
                attempt,
                delay,
            )
            self.sleep(delay)
        raise RuntimeError("unreachable Alpaca retry state")
