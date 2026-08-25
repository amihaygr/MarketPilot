"""Immutable, content-addressed SEC Bronze archival."""

import hashlib
from datetime import date
from typing import Any

from botocore.exceptions import ClientError


def archive_submissions_payload(
    s3: Any,
    *,
    bucket: str,
    cik: str,
    payload: bytes,
    partition_date: date,
) -> tuple[str, str]:
    digest = hashlib.sha256(payload).hexdigest()
    key = (
        "source=sec/event=submissions/"
        f"year={partition_date:%Y}/month={partition_date:%m}/day={partition_date:%d}/"
        f"cik={cik}/sha256={digest}.json"
    )
    try:
        s3.head_object(Bucket=bucket, Key=key)
    except ClientError as error:
        status = error.response.get("ResponseMetadata", {}).get("HTTPStatusCode")
        code = error.response.get("Error", {}).get("Code")
        if status != 404 and code not in {"404", "NoSuchKey", "NotFound"}:
            raise
        s3.put_object(
            Bucket=bucket,
            Key=key,
            Body=payload,
            ContentType="application/json",
            Metadata={"sha256": digest, "source": "sec"},
        )
    return f"s3://{bucket}/{key}", digest
