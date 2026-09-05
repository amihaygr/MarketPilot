"""Immutable source-page and completion-manifest archival for historical backfill."""

import hashlib
import json
from datetime import date
from typing import Any

from botocore.exceptions import ClientError


def source_page_key(logical_date: date, feed: str, payload: bytes) -> tuple[str, str]:
    digest = hashlib.sha256(payload).hexdigest()
    key = (
        "source=alpaca/event=historical_market_bars_page/"
        f"year={logical_date:%Y}/month={logical_date:%m}/day={logical_date:%d}/"
        f"feed={feed}/sha256={digest}.json"
    )
    return key, digest


def archive_source_page(
    s3: Any,
    *,
    bucket: str,
    logical_date: date,
    feed: str,
    payload: bytes,
) -> tuple[str, str]:
    key, digest = source_page_key(logical_date, feed, payload)
    if not object_exists(s3, bucket=bucket, key=key):
        s3.put_object(
            Bucket=bucket,
            Key=key,
            Body=payload,
            ContentType="application/json",
            Metadata={"sha256": digest, "source": "alpaca", "feed": feed},
        )
    return key, digest


def manifest_key(run_id: str, logical_date: date) -> str:
    return (
        "source=alpaca/event=historical_backfill_manifest/"
        f"year={logical_date:%Y}/month={logical_date:%m}/day={logical_date:%d}/"
        f"run_id={run_id}/manifest.json"
    )


def read_manifest(
    s3: Any,
    *,
    bucket: str,
    run_id: str,
    logical_date: date,
) -> dict[str, Any] | None:
    key = manifest_key(run_id, logical_date)
    if not object_exists(s3, bucket=bucket, key=key):
        return None
    body = s3.get_object(Bucket=bucket, Key=key)["Body"].read()
    decoded = json.loads(body)
    if not isinstance(decoded, dict) or decoded.get("status") != "ARCHIVED":
        raise ValueError("historical backfill manifest is malformed")
    return decoded


def write_manifest(
    s3: Any,
    *,
    bucket: str,
    run_id: str,
    logical_date: date,
    manifest: dict[str, Any],
) -> str:
    key = manifest_key(run_id, logical_date)
    payload = json.dumps(manifest, separators=(",", ":"), sort_keys=True).encode()
    s3.put_object(
        Bucket=bucket,
        Key=key,
        Body=payload,
        ContentType="application/json",
        Metadata={"run-id": run_id, "logical-date": logical_date.isoformat()},
    )
    return key


def object_exists(s3: Any, *, bucket: str, key: str) -> bool:
    try:
        s3.head_object(Bucket=bucket, Key=key)
        return True
    except ClientError as error:
        status = error.response.get("ResponseMetadata", {}).get("HTTPStatusCode")
        code = error.response.get("Error", {}).get("Code")
        if status == 404 or code in {"404", "NoSuchKey", "NotFound"}:
            return False
        raise
