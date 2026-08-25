"""Environment-backed settings for the read-only serving layer."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from os import environ


@dataclass(frozen=True, slots=True)
class ServingSettings:
    mariadb_host: str
    mariadb_port: int
    mariadb_database: str
    mariadb_user: str
    mariadb_password: str
    cors_origins: tuple[str, ...]
    max_market_range_days: int
    max_filing_range_days: int
    query_timeout_seconds: int
    code_version: str

    @classmethod
    def from_environ(cls, values: Mapping[str, str] | None = None) -> ServingSettings:
        source = environ if values is None else values
        origins = tuple(
            origin.strip()
            for origin in source.get("API_CORS_ORIGINS", "http://localhost:3000").split(",")
            if origin.strip()
        )
        if not origins:
            raise ValueError("API_CORS_ORIGINS must contain at least one explicit origin")
        return cls(
            mariadb_host=_required(source, "MARIADB_HOST"),
            mariadb_port=_positive_int(source.get("MARIADB_PORT", "3306"), "MARIADB_PORT"),
            mariadb_database=_required(source, "MARIADB_DATABASE"),
            mariadb_user=_required(source, "MARIADB_APP_USER"),
            mariadb_password=_required(source, "MARIADB_APP_PASSWORD"),
            cors_origins=origins,
            max_market_range_days=_positive_int(
                source.get("API_MAX_MARKET_RANGE_DAYS", "31"),
                "API_MAX_MARKET_RANGE_DAYS",
            ),
            max_filing_range_days=_positive_int(
                source.get("API_MAX_FILING_RANGE_DAYS", "3660"),
                "API_MAX_FILING_RANGE_DAYS",
            ),
            query_timeout_seconds=_positive_int(
                source.get("API_QUERY_TIMEOUT_SECONDS", "10"),
                "API_QUERY_TIMEOUT_SECONDS",
            ),
            code_version=source.get("MARKETPILOT_CODE_VERSION", "development").strip()
            or "development",
        )


def _required(values: Mapping[str, str], name: str) -> str:
    value = values.get(name, "").strip()
    if not value:
        raise ValueError(f"{name} is required")
    return value


def _positive_int(raw_value: str, name: str) -> int:
    try:
        value = int(raw_value)
    except ValueError as error:
        raise ValueError(f"{name} must be an integer") from error
    if value <= 0:
        raise ValueError(f"{name} must be positive")
    return value
