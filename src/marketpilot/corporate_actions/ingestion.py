"""Archive and publish bounded corporate-action pages."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any
from uuid import UUID

import boto3
import pymysql

from marketpilot.corporate_actions.client import AlpacaCorporateActionsClient


def _decimal(value: object) -> Decimal | None:
    try:
        return Decimal(str(value)) if value not in (None, "") else None
    except InvalidOperation:
        return None


def flatten_actions(payload: dict[str, Any]) -> list[dict[str, Any]]:
    groups = payload.get("corporate_actions", {})
    actions: list[dict[str, Any]] = []
    for action_type, rows in groups.items():
        if not isinstance(rows, list):
            continue
        for row in rows:
            if isinstance(row, dict):
                actions.append({**row, "action_type": action_type})
    return actions


def _archive(s3: Any, bucket: str, payload: bytes, partition_date: date) -> str:
    digest = hashlib.sha256(payload).hexdigest()
    key = (
        "source=alpaca/event=corporate_actions/"
        f"year={partition_date:%Y}/month={partition_date:%m}/day={partition_date:%d}/"
        f"sha256={digest}.json"
    )
    s3.put_object(
        Bucket=bucket,
        Key=key,
        Body=payload,
        ContentType="application/json",
        Metadata={"sha256": digest, "source": "alpaca"},
    )
    return f"s3://{bucket}/{key}"


def ingest_corporate_actions(*, start: date, end: date, run_id: UUID) -> dict[str, object]:
    import os

    symbols = tuple(value.strip().upper() for value in os.environ["MARKET_SYMBOLS"].split(","))
    client = AlpacaCorporateActionsClient(
        base_url=os.environ.get(
            "ALPACA_CORPORATE_ACTIONS_URL", "https://data.alpaca.markets/v1/corporate-actions"
        ),
        api_key=os.environ["ALPACA_API_KEY"],
        api_secret=os.environ["ALPACA_API_SECRET"],
    )
    s3 = boto3.client(
        "s3",
        endpoint_url=os.environ["MINIO_ENDPOINT"],
        aws_access_key_id=os.environ["MINIO_ROOT_USER"],
        aws_secret_access_key=os.environ["MINIO_ROOT_PASSWORD"],
    )
    connection = pymysql.connect(
        host=os.environ["MARIADB_HOST"],
        port=int(os.environ.get("MARIADB_PORT", "3306")),
        database=os.environ["MARIADB_DATABASE"],
        user=os.environ["MARIADB_PUBLISH_USER"],
        password=os.environ["MARIADB_PUBLISH_PASSWORD"],
        autocommit=False,
    )
    count = 0
    pages = 0
    try:
        with connection.cursor() as cursor:
            for page in client.pages(symbols=symbols, start=start, end=end):
                pages += 1
                uri = _archive(s3, os.environ["MINIO_BRONZE_BUCKET"], page.payload, end)
                for item in flatten_actions(page.decoded):
                    symbol = str(item.get("symbol") or item.get("initiating_symbol") or "")
                    action_id = str(item.get("id") or "")
                    process_date = item.get("process_date") or item.get("ex_date")
                    if not action_id or not symbol or not process_date:
                        continue
                    cursor.execute(
                        """
                        INSERT INTO fact_corporate_action (
                            corporate_action_id,symbol_id,action_type,process_date,ex_date,
                            record_date,payable_date,old_rate,new_rate,cash_amount,currency,
                            bronze_uri,source_payload_json,pipeline_run_id,code_version
                        ) SELECT %s,symbol_id,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s
                          FROM dim_symbol WHERE symbol=%s
                        ON DUPLICATE KEY UPDATE
                            source_payload_json=VALUES(source_payload_json),
                            bronze_uri=VALUES(bronze_uri),pipeline_run_id=VALUES(pipeline_run_id)
                        """,
                        (
                            action_id,
                            item["action_type"],
                            process_date,
                            item.get("ex_date"),
                            item.get("record_date"),
                            item.get("payable_date"),
                            _decimal(item.get("old_rate")),
                            _decimal(item.get("new_rate")),
                            _decimal(item.get("cash") or item.get("rate")),
                            item.get("currency"),
                            uri,
                            json.dumps(item, separators=(",", ":"), sort_keys=True),
                            str(run_id),
                            os.environ.get("MARKETPILOT_CODE_VERSION", "development"),
                            symbol,
                        ),
                    )
                    count += cursor.rowcount > 0
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
    return {
        "status": "published",
        "run_id": str(run_id),
        "pages_archived": pages,
        "actions_processed": count,
        "completed_at_utc": datetime.now(UTC).isoformat(),
    }
