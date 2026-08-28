from datetime import UTC, date, datetime
from pathlib import Path
from uuid import uuid4

import pytest

from marketpilot.operations.archive import (
    ArchiveManifest,
    resolve_archive_scope,
    spark_mariadb_jdbc_url,
)
from marketpilot.operations.compaction import DatasetMetrics, compaction_dates, validate_compaction
from marketpilot.operations.monitoring import AlertState, CheckResult
from marketpilot.operations.object_store import ObjectDigest, inventory_checksum, parse_s3_uri
from marketpilot.orchestration.operations_scope import (
    prepare_archive_scope,
    prepare_compaction_scope,
)

ROOT = Path(__file__).resolve().parents[2]


def metrics(row_count: int = 10) -> DatasetMetrics:
    return DatasetMetrics(
        row_count=row_count,
        distinct_business_keys=row_count,
        logical_hash_xor=123,
        logical_hash_sum=456,
        schema_fields=(("symbol", "string", False),),
    )


def test_compaction_scope_is_bounded_retry_stable_and_exact() -> None:
    run_id = str(uuid4())
    dates = compaction_dates(date(2026, 8, 28), 7, run_id)

    assert dates[0] == date(2026, 8, 22)
    assert dates[-1] == date(2026, 8, 28)
    assert len(dates) == 7
    validate_compaction(metrics(), metrics())
    with pytest.raises(ValueError, match="changed"):
        validate_compaction(metrics(), metrics(row_count=9))
    with pytest.raises(ValueError, match="between 1 and 31"):
        compaction_dates(date(2026, 8, 28), 32, run_id)


def test_archive_requires_closed_year_except_explicit_validation_snapshot() -> None:
    run_id = str(uuid4())
    closed = resolve_archive_scope(
        archive_year=2025,
        archive_version=1,
        run_id=run_id,
        current_year=2026,
    )
    assert closed.period_closed is True
    with pytest.raises(ValueError, match="closed calendar year"):
        resolve_archive_scope(
            archive_year=2026,
            archive_version=1,
            run_id=run_id,
            current_year=2026,
        )
    snapshot = resolve_archive_scope(
        archive_year=2026,
        archive_version=1,
        run_id=run_id,
        current_year=2026,
        validation_snapshot=True,
    )
    assert snapshot.period_closed is False
    assert snapshot.dataset_name.endswith("validation_snapshot")


def test_archive_manifest_validates_object_count_and_sha256_inventory() -> None:
    objects = (
        ObjectDigest("data/a.parquet", 10, "a" * 64),
        ObjectDigest("data/b.parquet", 20, "b" * 64),
    )
    manifest = ArchiveManifest(
        dataset_name="fact_market_bar_1m",
        archive_year=2025,
        archive_version=1,
        run_id=str(uuid4()),
        object_uri="s3a://archive/data",
        manifest_uri="s3a://archive/manifest.json",
        row_count=20,
        object_count=2,
        checksum_sha256=inventory_checksum(objects),
        schema_version=1,
        code_version="test",
        min_event_time_utc=datetime(2025, 1, 2, tzinfo=UTC).isoformat(),
        max_event_time_utc=datetime(2025, 12, 30, tzinfo=UTC).isoformat(),
        period_closed=True,
        verified_at_utc=datetime(2026, 1, 10, tzinfo=UTC).isoformat(),
        objects=objects,
    )
    manifest.validate_inventory()
    restored = ArchiveManifest.from_dict(manifest.to_dict())
    assert restored == manifest


def test_object_uri_parser_rejects_non_object_storage_schemes() -> None:
    assert parse_s3_uri("s3a://marketpilot-archive/path").bucket == "marketpilot-archive"
    assert parse_s3_uri("s3://bucket").prefix == ""
    with pytest.raises(ValueError, match="s3a"):
        parse_s3_uri("https://minio/archive")


def test_spark_uses_mysql_dialect_with_mariadb_connector_permission() -> None:
    assert spark_mariadb_jdbc_url("jdbc:mariadb://mariadb:3306/marketpilot") == (
        "jdbc:mysql://mariadb:3306/marketpilot?permitMysqlScheme=true"
    )
    with pytest.raises(ValueError, match="MariaDB scheme"):
        spark_mariadb_jdbc_url("jdbc:postgresql://database/marketpilot")


def test_alert_state_deduplicates_and_emits_resolution() -> None:
    state = AlertState()
    assert state.observe(CheckResult("api", True, "ready")) is None
    alert = state.observe(CheckResult("api", False, "timeout"))
    assert alert is not None and alert.state == "ALERT"
    assert state.observe(CheckResult("api", False, "timeout")) is None
    resolved = state.observe(CheckResult("api", True, "ready"))
    assert resolved is not None and resolved.state == "RESOLVED"


def test_airflow_operation_scopes_are_stable_and_reject_open_year() -> None:
    first = prepare_compaction_scope("2026-08-28", 7, "scheduled__weekly")
    assert first == prepare_compaction_scope("2026-08-28", 7, "scheduled__weekly")
    archive = prepare_archive_scope(
        logical_date_value="2027-01-10",
        archive_year_override=None,
        archive_version=1,
        airflow_run_id="scheduled__annual",
    )
    assert archive["archive_year"] == 2026
    with pytest.raises(ValueError, match="closed calendar year"):
        prepare_archive_scope(
            logical_date_value="2026-01-10",
            archive_year_override=2026,
            archive_version=1,
            airflow_run_id="manual__open",
        )


def test_phase8_dags_are_bounded_spark_jobs_and_never_control_services() -> None:
    weekly = (ROOT / "airflow" / "dags" / "weekly_compaction.py").read_text(encoding="utf-8")
    annual = (ROOT / "airflow" / "dags" / "annual_archive.py").read_text(encoding="utf-8")
    combined = weekly + annual

    assert 'schedule="0 6 * * 6"' in weekly
    assert 'schedule="0 2 10 1 *"' in annual
    assert combined.count("max_active_runs=1") == 2
    assert combined.count("catchup=False") == 2
    assert combined.count("SparkSubmitOperator") >= 4
    assert "stream_market_bars.py" not in combined
    assert "docker compose" not in combined.lower()


def test_restore_script_restricts_destructive_database_scope() -> None:
    source = (ROOT / "scripts" / "restore_mariadb_backup.ps1").read_text(encoding="utf-8")
    assert "^marketpilot_restore_" in source
    assert "DROP DATABASE IF EXISTS" in source
    assert "MARIADB_ROOT_PASSWORD" in source
