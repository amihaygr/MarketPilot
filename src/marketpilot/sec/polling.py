"""Bounded SEC submissions poller used by Airflow and local verification."""

import argparse
import json
import logging
from dataclasses import asdict
from datetime import UTC, datetime
from uuid import UUID, uuid4

import boto3

from marketpilot.contracts.sec_filing import SecFilingV1
from marketpilot.sec.archive import archive_submissions_payload
from marketpilot.sec.client import SecClient
from marketpilot.sec.mariadb import publish_sec_filings
from marketpilot.sec.parsing import latest_filing_date, parse_recent_filings
from marketpilot.sec.settings import SecSettings

logger = logging.getLogger(__name__)


def poll_sec(settings: SecSettings, run_id: UUID) -> dict[str, object]:
    if not settings.enabled:
        return {"status": "disabled", "run_id": str(run_id)}
    settings.validate_external_identity()
    client = SecClient(
        base_url=settings.base_url,
        user_agent=settings.user_agent,
        requests_per_second=settings.max_requests_per_second,
        timeout_seconds=settings.request_timeout_seconds,
        max_attempts=settings.request_max_attempts,
    )
    s3 = boto3.client(
        "s3",
        endpoint_url=settings.minio_endpoint,
        aws_access_key_id=settings.minio_access_key,
        aws_secret_access_key=settings.minio_secret_key,
    )
    ingested_at = datetime.now(UTC)
    filings: list[SecFilingV1] = []
    archived_payloads = 0
    for symbol, cik in settings.companies:
        _source_url, raw_payload, decoded = client.company_submissions(cik)
        bronze_uri, digest = archive_submissions_payload(
            s3,
            bucket=settings.bronze_bucket,
            cik=cik,
            payload=raw_payload,
            partition_date=latest_filing_date(decoded, ingested_at.date()),
        )
        archived_payloads += 1
        filings.extend(
            parse_recent_filings(
                decoded,
                symbol=symbol,
                cik=cik,
                forms=settings.forms,
                bronze_uri=bronze_uri,
                source_sha256=digest,
                pipeline_run_id=run_id,
                code_version=settings.code_version,
                ingested_at_utc=ingested_at,
            )
        )
    publication = publish_sec_filings(
        settings,
        tuple(filings),
        run_id=run_id,
        watermark_utc=ingested_at,
    )
    summary: dict[str, object] = {
        "status": "published",
        "run_id": str(run_id),
        "companies_polled": len(settings.companies),
        "payloads_archived": archived_payloads,
        **asdict(publication),
    }
    logger.info(
        "SEC poll completed run_id=%s companies=%d discovered=%d inserted=%d updated=%d",
        summary["run_id"],
        summary["companies_polled"],
        summary["discovered"],
        summary["inserted"],
        summary["updated"],
    )
    return summary


def poll_sec_from_env(run_id: str) -> dict[str, object]:
    return poll_sec(SecSettings.from_env(), UUID(run_id))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", default=str(uuid4()))
    args = parser.parse_args()
    logging.basicConfig(
        level=logging.INFO,
        format='{"level":"%(levelname)s","logger":"%(name)s","message":"%(message)s"}',
    )
    print(json.dumps(poll_sec_from_env(args.run_id), separators=(",", ":")))


if __name__ == "__main__":
    main()
