"""Rate-limited, retrying client for the public SEC data APIs."""

import json
import logging
import time
from collections.abc import Callable
from typing import Any, Protocol
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

logger = logging.getLogger(__name__)


class ResponseLike(Protocol):
    def __enter__(self) -> "ResponseLike": ...

    def __exit__(self, *args: object) -> None: ...

    def read(self) -> bytes: ...


OpenUrl = Callable[..., ResponseLike]


class RateLimiter:
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


class SecClient:
    def __init__(
        self,
        *,
        base_url: str,
        user_agent: str,
        requests_per_second: float,
        timeout_seconds: float,
        max_attempts: int,
        opener: OpenUrl = urlopen,
        sleep: Callable[[float], None] = time.sleep,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.user_agent = user_agent
        self.timeout_seconds = timeout_seconds
        self.max_attempts = max_attempts
        self.opener = opener
        self.sleep = sleep
        self.rate_limiter = RateLimiter(
            requests_per_second,
            clock=clock,
            sleep=sleep,
        )

    def company_submissions(self, cik: str) -> tuple[str, bytes, dict[str, Any]]:
        url = f"{self.base_url}/submissions/CIK{cik}.json"
        payload = self._get(url)
        decoded = json.loads(payload)
        if not isinstance(decoded, dict):
            raise ValueError("SEC submissions response must be a JSON object")
        return url, payload, decoded

    def _get(self, url: str) -> bytes:
        for attempt in range(1, self.max_attempts + 1):
            self.rate_limiter.wait()
            request = Request(
                url,
                headers={
                    "User-Agent": self.user_agent,
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
                "SEC request retry url=%s attempt=%d delay_seconds=%s",
                url,
                attempt,
                delay,
            )
            self.sleep(delay)
        raise RuntimeError("unreachable SEC retry state")
