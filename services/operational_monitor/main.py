"""Continuously evaluate local platform dependencies and emit deduplicated alerts."""

from __future__ import annotations

import json
import logging
import os
import signal
import threading
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from time import monotonic

import boto3
import pymysql
from confluent_kafka.admin import AdminClient

from marketpilot.operations.monitoring import AlertEvent, AlertState, CheckResult

logger = logging.getLogger("marketpilot.operational_monitor")
READY_FILE = Path("/tmp/operational-monitor-ready")


def configure_logging() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")


def emit(event: str, **values: object) -> None:
    logger.info(
        json.dumps(
            {
                "timestamp_utc": datetime.now(UTC).isoformat(),
                "event": event,
                **values,
            },
            separators=(",", ":"),
        )
    )


def dependency_checks(now_utc: datetime | None = None) -> tuple[CheckResult, ...]:
    now = now_utc or datetime.now(UTC)
    results = [_safe_check("backend_api", _check_api)]
    results.append(_safe_check("kafka", _check_kafka))
    results.append(_safe_check("object_storage", _check_object_storage))
    results.extend(_database_checks(now))
    return tuple(results)


def _safe_check(name: str, callback) -> CheckResult:  # type: ignore[no-untyped-def]
    started = monotonic()
    try:
        detail = callback()
        duration_ms = (monotonic() - started) * 1000
        return CheckResult(name=name, healthy=True, detail=f"{detail};ms={duration_ms:.1f}")
    except Exception as error:
        return CheckResult(name=name, healthy=False, detail=f"error_type={type(error).__name__}")


def _check_api() -> str:
    with urllib.request.urlopen("http://backend-api:8000/health/ready", timeout=5) as response:
        if response.status != 200:
            raise RuntimeError("backend API readiness returned non-200")
    return "ready"


def _check_kafka() -> str:
    metadata = AdminClient(
        {"bootstrap.servers": os.environ["KAFKA_BOOTSTRAP_SERVERS"]}
    ).list_topics(timeout=5)
    required = {
        os.environ["KAFKA_MARKET_BARS_TOPIC"],
        os.environ["KAFKA_DEAD_LETTER_TOPIC"],
    }
    missing = required - set(metadata.topics)
    if missing:
        raise RuntimeError("required Kafka topics are missing")
    return f"topics={len(metadata.topics)}"


def _check_object_storage() -> str:
    client = boto3.client(
        "s3",
        endpoint_url=os.environ["MINIO_ENDPOINT"],
        aws_access_key_id=os.environ["MINIO_ROOT_USER"],
        aws_secret_access_key=os.environ["MINIO_ROOT_PASSWORD"],
    )
    buckets = (
        os.environ["MINIO_BRONZE_BUCKET"],
        os.environ["MINIO_SILVER_BUCKET"],
        os.environ.get("MINIO_ARCHIVE_BUCKET", "marketpilot-archive"),
    )
    for bucket in buckets:
        client.head_bucket(Bucket=bucket)
    return f"buckets={len(buckets)}"


def _database_checks(now: datetime) -> list[CheckResult]:
    try:
        connection = pymysql.connect(
            host=os.environ["MARIADB_HOST"],
            port=int(os.environ.get("MARIADB_PORT", "3306")),
            database=os.environ["MARIADB_DATABASE"],
            user=os.environ["MARIADB_APP_USER"],
            password=os.environ["MARIADB_APP_PASSWORD"],
            connect_timeout=5,
        )
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT MAX(event_time_utc) FROM fact_market_bar_1m")
                market_time = cursor.fetchone()[0]
                cursor.execute("SELECT MAX(ingested_at_utc) FROM fact_sec_filing")
                sec_time = cursor.fetchone()[0]
        finally:
            connection.close()
    except Exception as error:
        return [
            CheckResult("mariadb", False, f"error_type={type(error).__name__}"),
            CheckResult("market_freshness", False, "database_unavailable"),
            CheckResult("sec_freshness", False, "database_unavailable"),
        ]

    return [
        CheckResult("mariadb", True, "read_query_ok"),
        _freshness_result(
            "market_freshness",
            market_time,
            now,
            float(os.environ.get("OPERATIONS_MARKET_FRESHNESS_MAX_HOURS", "96")),
        ),
        _freshness_result(
            "sec_freshness",
            sec_time,
            now,
            float(os.environ.get("OPERATIONS_SEC_FRESHNESS_MAX_HOURS", "336")),
        ),
    ]


def _freshness_result(
    name: str,
    value: datetime | None,
    now: datetime,
    maximum_hours: float,
) -> CheckResult:
    if value is None:
        return CheckResult(name, False, "no_data")
    timestamp = value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)
    age_hours = max(0.0, (now - timestamp).total_seconds() / 3600)
    return CheckResult(
        name=name,
        healthy=age_hours <= maximum_hours,
        detail=f"age_hours={age_hours:.2f};maximum_hours={maximum_hours:.2f}",
    )


def deliver_alert(event: AlertEvent) -> None:
    emit("operational_alert", check=event.name, state=event.state, detail=event.detail)
    webhook = os.environ.get("OPERATIONS_ALERT_WEBHOOK_URL", "").strip()
    if not webhook:
        return
    request = urllib.request.Request(
        webhook,
        data=json.dumps(
            {
                "service": "MarketPilot",
                "check": event.name,
                "state": event.state,
                "detail": event.detail,
            }
        ).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            if response.status >= 400:
                raise RuntimeError("alert webhook returned an error status")
    except Exception as error:
        emit("alert_delivery_failed", check=event.name, error_type=type(error).__name__)


def main() -> None:
    configure_logging()
    stop = threading.Event()
    signal.signal(signal.SIGTERM, lambda *_arguments: stop.set())
    signal.signal(signal.SIGINT, lambda *_arguments: stop.set())
    interval = int(os.environ.get("OPERATIONS_CHECK_INTERVAL_SECONDS", "60"))
    if interval < 10:
        raise ValueError("OPERATIONS_CHECK_INTERVAL_SECONDS must be at least 10")
    state = AlertState()
    emit("operational_monitor_started", interval_seconds=interval)
    while not stop.is_set():
        checks = dependency_checks()
        for check in checks:
            if event := state.observe(check):
                deliver_alert(event)
        emit(
            "operational_check_completed",
            healthy=all(check.healthy for check in checks),
            checks=[
                {"name": check.name, "healthy": check.healthy, "detail": check.detail}
                for check in checks
            ],
        )
        READY_FILE.write_text(datetime.now(UTC).isoformat(), encoding="utf-8")
        stop.wait(interval)
    emit("operational_monitor_stopped")


if __name__ == "__main__":
    main()
