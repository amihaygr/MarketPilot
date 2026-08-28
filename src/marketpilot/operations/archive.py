"""Pure annual archive scope and manifest models."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from marketpilot.operations.object_store import ObjectDigest, inventory_checksum

ARCHIVE_SCHEMA_VERSION = 1
ANNUAL_DATASET = "fact_market_bar_1m"
VALIDATION_DATASET = "fact_market_bar_1m_validation_snapshot"
SPARK_UTC = timezone.utc  # noqa: UP017 -- imported by Spark's Python 3.10 runtime.


@dataclass(frozen=True, slots=True)
class ArchiveScope:
    archive_year: int
    archive_version: int
    run_id: str
    dataset_name: str
    period_closed: bool


@dataclass(frozen=True, slots=True)
class ArchiveManifest:
    dataset_name: str
    archive_year: int
    archive_version: int
    run_id: str
    object_uri: str
    manifest_uri: str
    row_count: int
    object_count: int
    checksum_sha256: str
    schema_version: int
    code_version: str
    min_event_time_utc: str
    max_event_time_utc: str
    period_closed: bool
    verified_at_utc: str
    objects: tuple[ObjectDigest, ...]

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["objects"] = [asdict(item) for item in self.objects]
        return payload

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> ArchiveManifest:
        values = dict(payload)
        values["objects"] = tuple(ObjectDigest(**item) for item in payload["objects"])
        return cls(**values)

    def validate_inventory(self) -> None:
        if self.row_count < 1:
            raise ValueError("verified archive must contain at least one row")
        if self.object_count != len(self.objects):
            raise ValueError("archive object count does not match inventory")
        if self.checksum_sha256 != inventory_checksum(self.objects):
            raise ValueError("archive inventory checksum does not match manifest")


def resolve_archive_scope(
    *,
    archive_year: int,
    archive_version: int,
    run_id: str,
    current_year: int | None = None,
    validation_snapshot: bool = False,
) -> ArchiveScope:
    resolved_current_year = current_year or datetime.now(SPARK_UTC).year
    if archive_year < 1990 or archive_year > resolved_current_year:
        raise ValueError("archive year is outside the supported range")
    if archive_version < 1:
        raise ValueError("archive version must be positive")
    UUID(run_id)
    period_closed = archive_year < resolved_current_year
    if not period_closed and not validation_snapshot:
        raise ValueError("annual archive requires a closed calendar year")
    return ArchiveScope(
        archive_year=archive_year,
        archive_version=archive_version,
        run_id=run_id,
        dataset_name=VALIDATION_DATASET if validation_snapshot else ANNUAL_DATASET,
        period_closed=period_closed,
    )


def spark_mariadb_jdbc_url(url: str) -> str:
    """Make Spark select its MySQL-compatible dialect while retaining MariaDB Connector/J."""
    if not url.startswith("jdbc:mariadb://"):
        raise ValueError("archive JDBC URL must use the MariaDB scheme")
    converted = "jdbc:mysql://" + url.removeprefix("jdbc:mariadb://")
    separator = "&" if "?" in converted else "?"
    return f"{converted}{separator}permitMysqlScheme=true"
