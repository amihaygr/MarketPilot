"""Idempotent SEC filing publication to the MariaDB Gold boundary."""

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

import pymysql

from marketpilot.contracts.sec_filing import SecFilingV1
from marketpilot.sec.settings import SecSettings


@dataclass(frozen=True, slots=True)
class SecPublicationSummary:
    discovered: int
    inserted: int
    updated: int


def publish_sec_filings(
    settings: SecSettings,
    filings: tuple[SecFilingV1, ...],
    *,
    run_id: UUID,
    watermark_utc: datetime,
) -> SecPublicationSummary:
    connection = pymysql.connect(
        host=settings.mariadb_host,
        port=settings.mariadb_port,
        database=settings.mariadb_database,
        user=settings.mariadb_user,
        password=settings.mariadb_password,
        charset="utf8mb4",
        autocommit=False,
        connect_timeout=10,
    )
    try:
        with connection.cursor() as cursor:
            existing: set[str] = set()
            if filings:
                placeholders = ",".join(["%s"] * len(filings))
                cursor.execute(
                    f"SELECT accession_number FROM fact_sec_filing "
                    f"WHERE accession_number IN ({placeholders})",
                    tuple(filing.accession_number for filing in filings),
                )
                existing = {str(row[0]) for row in cursor.fetchall()}
                cursor.executemany(
                    "INSERT IGNORE INTO dim_symbol (symbol) VALUES (%s)",
                    [(filing.symbol,) for filing in filings],
                )
                cursor.executemany(_UPSERT_SQL, [filing.db_parameters() for filing in filings])

            cursor.execute(
                """
                INSERT INTO etl_watermark (
                    pipeline_name, partition_key, watermark_utc, status, run_id
                ) VALUES ('sec-filings-poll', 'latest', %s, 'PUBLISHED', %s)
                ON DUPLICATE KEY UPDATE
                    watermark_utc = VALUES(watermark_utc),
                    status = 'PUBLISHED',
                    run_id = VALUES(run_id)
                """,
                (
                    watermark_utc.astimezone(UTC).replace(tzinfo=None),
                    str(run_id),
                ),
            )
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()

    inserted = sum(filing.accession_number not in existing for filing in filings)
    return SecPublicationSummary(
        discovered=len(filings),
        inserted=inserted,
        updated=len(filings) - inserted,
    )


_UPSERT_SQL = """
    INSERT INTO fact_sec_filing (
        accession_number, symbol_id, cik, company_name, form_type,
        filing_date, report_date, acceptance_datetime_utc,
        primary_document, primary_document_description, items,
        file_number, film_number, filing_size, is_xbrl, is_inline_xbrl,
        source_url, bronze_uri, source_sha256, pipeline_run_id,
        code_version, schema_version, ingested_at_utc
    ) VALUES (
        %s, (SELECT symbol_id FROM dim_symbol WHERE symbol = %s), %s, %s, %s,
        %s, %s, %s,
        %s, %s, %s,
        %s, %s, %s, %s, %s,
        %s, %s, %s, %s,
        %s, %s, %s
    )
    ON DUPLICATE KEY UPDATE
        symbol_id = VALUES(symbol_id),
        cik = VALUES(cik),
        company_name = VALUES(company_name),
        form_type = VALUES(form_type),
        filing_date = VALUES(filing_date),
        report_date = VALUES(report_date),
        acceptance_datetime_utc = VALUES(acceptance_datetime_utc),
        primary_document = VALUES(primary_document),
        primary_document_description = VALUES(primary_document_description),
        items = VALUES(items),
        file_number = VALUES(file_number),
        film_number = VALUES(film_number),
        filing_size = VALUES(filing_size),
        is_xbrl = VALUES(is_xbrl),
        is_inline_xbrl = VALUES(is_inline_xbrl),
        source_url = VALUES(source_url),
        bronze_uri = VALUES(bronze_uri),
        source_sha256 = VALUES(source_sha256),
        pipeline_run_id = VALUES(pipeline_run_id),
        code_version = VALUES(code_version),
        schema_version = VALUES(schema_version),
        ingested_at_utc = VALUES(ingested_at_utc)
"""
