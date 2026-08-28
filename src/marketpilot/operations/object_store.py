"""Small, deterministic helpers for versioned S3-compatible operational objects."""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import asdict, dataclass
from typing import Any

import boto3


@dataclass(frozen=True, slots=True)
class S3Location:
    bucket: str
    prefix: str


@dataclass(frozen=True, slots=True)
class ObjectDigest:
    key: str
    size_bytes: int
    checksum_sha256: str


def parse_s3_uri(uri: str) -> S3Location:
    """Parse an s3a:// or s3:// URI without accepting ambiguous bucket paths."""
    if uri.startswith("s3a://"):
        value = uri.removeprefix("s3a://")
    elif uri.startswith("s3://"):
        value = uri.removeprefix("s3://")
    else:
        raise ValueError("object URI must use s3a:// or s3://")
    bucket, separator, prefix = value.partition("/")
    if not bucket or bucket in {".", ".."}:
        raise ValueError("object URI must include a bucket")
    return S3Location(bucket=bucket, prefix=prefix.strip("/") if separator else "")


def object_store_client() -> Any:
    return boto3.client(
        "s3",
        endpoint_url=os.environ["MINIO_ENDPOINT"],
        aws_access_key_id=os.environ["MINIO_ROOT_USER"],
        aws_secret_access_key=os.environ["MINIO_ROOT_PASSWORD"],
    )


def list_objects(client: Any, bucket: str, prefix: str) -> list[dict[str, Any]]:
    objects: list[dict[str, Any]] = []
    continuation_token: str | None = None
    while True:
        parameters: dict[str, Any] = {"Bucket": bucket, "Prefix": prefix.strip("/")}
        if continuation_token:
            parameters["ContinuationToken"] = continuation_token
        response = client.list_objects_v2(**parameters)
        objects.extend(response.get("Contents", []))
        if not response.get("IsTruncated"):
            return objects
        continuation_token = response["NextContinuationToken"]


def delete_keys(client: Any, bucket: str, keys: list[str]) -> None:
    for start in range(0, len(keys), 1_000):
        batch = keys[start : start + 1_000]
        if batch:
            client.delete_objects(
                Bucket=bucket,
                Delete={"Objects": [{"Key": key} for key in batch], "Quiet": True},
            )


def delete_prefix(client: Any, bucket: str, prefix: str) -> None:
    delete_keys(client, bucket, [str(item["Key"]) for item in list_objects(client, bucket, prefix)])


def copy_key(
    client: Any,
    *,
    source_bucket: str,
    source_key: str,
    target_bucket: str,
    target_key: str,
) -> None:
    client.copy_object(
        Bucket=target_bucket,
        Key=target_key,
        CopySource={"Bucket": source_bucket, "Key": source_key},
    )


def copy_prefix(
    client: Any,
    *,
    source_bucket: str,
    source_prefix: str,
    target_bucket: str,
    target_prefix: str,
) -> list[str]:
    copied: list[str] = []
    normalized_source = source_prefix.strip("/") + "/"
    normalized_target = target_prefix.strip("/")
    for item in list_objects(client, source_bucket, normalized_source):
        source_key = str(item["Key"])
        relative = source_key.removeprefix(normalized_source)
        target_key = f"{normalized_target}/{relative}"
        copy_key(
            client,
            source_bucket=source_bucket,
            source_key=source_key,
            target_bucket=target_bucket,
            target_key=target_key,
        )
        copied.append(target_key)
    return copied


def sha256_object(client: Any, bucket: str, key: str) -> str:
    digest = hashlib.sha256()
    body = client.get_object(Bucket=bucket, Key=key)["Body"]
    try:
        while chunk := body.read(1024 * 1024):
            digest.update(chunk)
    finally:
        body.close()
    return digest.hexdigest()


def inventory(client: Any, bucket: str, prefix: str) -> tuple[ObjectDigest, ...]:
    entries = []
    for item in list_objects(client, bucket, prefix):
        key = str(item["Key"])
        if not key.endswith(".parquet"):
            continue
        entries.append(
            ObjectDigest(
                key=key,
                size_bytes=int(item["Size"]),
                checksum_sha256=sha256_object(client, bucket, key),
            )
        )
    return tuple(sorted(entries, key=lambda entry: entry.key))


def inventory_checksum(entries: tuple[ObjectDigest, ...]) -> str:
    if not entries:
        raise ValueError("archive inventory must contain at least one Parquet object")
    payload = json.dumps(
        [asdict(entry) for entry in entries],
        sort_keys=True,
        separators=(",", ":"),
    ).encode()
    return hashlib.sha256(payload).hexdigest()


def write_json(client: Any, bucket: str, key: str, payload: dict[str, Any]) -> None:
    client.put_object(
        Bucket=bucket,
        Key=key,
        Body=(json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n").encode(),
        ContentType="application/json",
    )


def read_json(client: Any, bucket: str, key: str) -> dict[str, Any]:
    body = client.get_object(Bucket=bucket, Key=key)["Body"]
    try:
        return json.loads(body.read())
    finally:
        body.close()
