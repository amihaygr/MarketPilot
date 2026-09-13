"""Retrying client for Alpaca's versioned corporate-actions endpoint."""

from __future__ import annotations

import json
import time
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from datetime import date
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


@dataclass(frozen=True, slots=True)
class CorporateActionPage:
    payload: bytes
    decoded: dict[str, Any]
    page_number: int


class AlpacaCorporateActionsClient:
    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        api_secret: str,
        timeout_seconds: float = 20,
        max_attempts: int = 4,
        opener: Callable[..., Any] = urlopen,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self.base_url = base_url
        self.api_key = api_key
        self.api_secret = api_secret
        self.timeout_seconds = timeout_seconds
        self.max_attempts = max_attempts
        self.opener = opener
        self.sleep = sleep

    def pages(
        self, *, symbols: tuple[str, ...], start: date, end: date
    ) -> Iterator[CorporateActionPage]:
        token: str | None = None
        for page_number in range(1, 101):
            query = {
                "symbols": ",".join(symbols),
                "start": start.isoformat(),
                "end": end.isoformat(),
                "region": "us",
                "data_quality": "complete",
                "sort": "asc",
                "limit": "1000",
            }
            if token:
                query["page_token"] = token
            payload = self._get(f"{self.base_url}?{urlencode(query)}")
            decoded = json.loads(payload)
            if not isinstance(decoded, dict) or not isinstance(
                decoded.get("corporate_actions"), dict
            ):
                raise ValueError("Alpaca response must contain corporate_actions")
            yield CorporateActionPage(payload, decoded, page_number)
            token_value = decoded.get("next_page_token")
            token = str(token_value) if token_value else None
            if token is None:
                return
        raise RuntimeError("corporate-action pagination exceeded 100 pages")

    def _get(self, url: str) -> bytes:
        for attempt in range(1, self.max_attempts + 1):
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
                if error.code != 429 and not 500 <= error.code < 600:
                    raise
                if attempt == self.max_attempts:
                    raise
            except (URLError, TimeoutError):
                if attempt == self.max_attempts:
                    raise
            self.sleep(min(2 ** (attempt - 1), 30))
        raise RuntimeError("unreachable retry state")
