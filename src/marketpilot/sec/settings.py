"""Validated environment settings for bounded SEC polling."""

from dataclasses import dataclass
from os import environ
from urllib.parse import urlparse


def parse_bool(value: str) -> bool:
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise ValueError(f"invalid boolean value: {value}")


def parse_company_ciks(value: str) -> tuple[tuple[str, str], ...]:
    companies: dict[str, str] = {}
    for entry in value.split(","):
        if not entry.strip():
            continue
        try:
            raw_symbol, raw_cik = entry.split(":", maxsplit=1)
        except ValueError as error:
            raise ValueError("SEC_COMPANY_CIKS entries must use SYMBOL:CIK") from error
        symbol = raw_symbol.strip().upper()
        cik = raw_cik.strip()
        if not symbol or not cik.isdigit() or len(cik) > 10:
            raise ValueError("SEC_COMPANY_CIKS contains an invalid symbol or CIK")
        companies[symbol] = cik.zfill(10)
    if not companies:
        raise ValueError("SEC_COMPANY_CIKS must contain at least one company")
    return tuple(sorted(companies.items()))


@dataclass(frozen=True, slots=True)
class SecSettings:
    enabled: bool
    user_agent: str
    max_requests_per_second: float
    base_url: str
    allow_insecure_http: bool
    request_timeout_seconds: float
    request_max_attempts: int
    companies: tuple[tuple[str, str], ...]
    forms: frozenset[str]
    minio_endpoint: str
    minio_access_key: str
    minio_secret_key: str
    bronze_bucket: str
    mariadb_host: str
    mariadb_port: int
    mariadb_database: str
    mariadb_user: str
    mariadb_password: str
    code_version: str

    @classmethod
    def from_env(cls) -> "SecSettings":
        base_url = environ.get("SEC_BASE_URL", "https://data.sec.gov").rstrip("/")
        allow_insecure = parse_bool(environ.get("SEC_ALLOW_INSECURE_HTTP", "false"))
        if urlparse(base_url).scheme != "https" and not allow_insecure:
            raise ValueError("SEC_BASE_URL must use HTTPS")
        rate = float(environ.get("SEC_MAX_REQUESTS_PER_SECOND", "5"))
        if rate <= 0 or rate > 10:
            raise ValueError("SEC_MAX_REQUESTS_PER_SECOND must be in (0, 10]")
        timeout = float(environ.get("SEC_REQUEST_TIMEOUT_SECONDS", "30"))
        attempts = int(environ.get("SEC_REQUEST_MAX_ATTEMPTS", "4"))
        if timeout <= 0 or attempts < 1:
            raise ValueError("SEC request timeout and attempts must be positive")
        forms = frozenset(
            form.strip().upper()
            for form in environ.get("SEC_FORMS", "10-K,10-Q,8-K").split(",")
            if form.strip()
        )
        if not forms:
            raise ValueError("SEC_FORMS must contain at least one form")
        return cls(
            enabled=parse_bool(environ.get("SEC_POLL_ENABLED", "false")),
            user_agent=environ["SEC_USER_AGENT"].strip(),
            max_requests_per_second=rate,
            base_url=base_url,
            allow_insecure_http=allow_insecure,
            request_timeout_seconds=timeout,
            request_max_attempts=attempts,
            companies=parse_company_ciks(environ["SEC_COMPANY_CIKS"]),
            forms=forms,
            minio_endpoint=environ["MINIO_ENDPOINT"],
            minio_access_key=environ["MINIO_ROOT_USER"],
            minio_secret_key=environ["MINIO_ROOT_PASSWORD"],
            bronze_bucket=environ["MINIO_BRONZE_BUCKET"],
            mariadb_host=environ["MARIADB_HOST"],
            mariadb_port=int(environ.get("MARIADB_PORT", "3306")),
            mariadb_database=environ["MARIADB_DATABASE"],
            mariadb_user=environ["MARIADB_SEC_USER"],
            mariadb_password=environ["MARIADB_SEC_PASSWORD"],
            code_version=environ.get("MARKETPILOT_CODE_VERSION", "development"),
        )

    def validate_external_identity(self) -> None:
        lowered = self.user_agent.lower()
        if "@" not in self.user_agent or "replace-with-contact" in lowered:
            raise ValueError("SEC_USER_AGENT must identify the project and a real contact email")
