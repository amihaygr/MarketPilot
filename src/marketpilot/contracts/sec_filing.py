"""Versioned canonical contract for SEC filing metadata."""

import re
from dataclasses import dataclass
from datetime import UTC, date, datetime
from uuid import UUID

ACCESSION_PATTERN = re.compile(r"^\d{10}-\d{2}-\d{6}$")


@dataclass(frozen=True, slots=True)
class SecFilingV1:
    accession_number: str
    cik: str
    symbol: str
    company_name: str
    form_type: str
    filing_date: date
    report_date: date | None
    acceptance_datetime_utc: datetime | None
    primary_document: str
    primary_document_description: str | None
    items: str | None
    file_number: str | None
    film_number: str | None
    filing_size: int | None
    is_xbrl: bool
    is_inline_xbrl: bool
    source_url: str
    bronze_uri: str
    source_sha256: str
    pipeline_run_id: UUID
    code_version: str
    ingested_at_utc: datetime
    schema_version: int = 1

    def validate(self) -> None:
        if not ACCESSION_PATTERN.fullmatch(self.accession_number):
            raise ValueError("accession_number has an invalid format")
        if len(self.cik) != 10 or not self.cik.isdigit():
            raise ValueError("cik must contain exactly 10 digits")
        if not self.symbol or self.symbol != self.symbol.upper():
            raise ValueError("symbol must be non-empty uppercase text")
        if not self.company_name or not self.form_type or not self.primary_document:
            raise ValueError("company, form, and primary document are required")
        if self.filing_size is not None and self.filing_size < 0:
            raise ValueError("filing_size must be non-negative")
        if not re.fullmatch(r"[0-9a-f]{64}", self.source_sha256):
            raise ValueError("source_sha256 must be a SHA-256 hex digest")
        if self.schema_version != 1:
            raise ValueError("schema_version must be 1")
        for timestamp in (self.acceptance_datetime_utc, self.ingested_at_utc):
            if timestamp is not None and (
                timestamp.tzinfo is None or timestamp.utcoffset() is None
            ):
                raise ValueError("SEC timestamps must be timezone-aware")

    def db_parameters(self) -> tuple[object, ...]:
        self.validate()
        accepted = (
            self.acceptance_datetime_utc.astimezone(UTC).replace(tzinfo=None)
            if self.acceptance_datetime_utc
            else None
        )
        return (
            self.accession_number,
            self.symbol,
            self.cik,
            self.company_name,
            self.form_type,
            self.filing_date,
            self.report_date,
            accepted,
            self.primary_document,
            self.primary_document_description,
            self.items,
            self.file_number,
            self.film_number,
            self.filing_size,
            self.is_xbrl,
            self.is_inline_xbrl,
            self.source_url,
            self.bronze_uri,
            self.source_sha256,
            str(self.pipeline_run_id),
            self.code_version,
            self.schema_version,
            self.ingested_at_utc.astimezone(UTC).replace(tzinfo=None),
        )
