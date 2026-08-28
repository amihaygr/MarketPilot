USE marketpilot;

ALTER TABLE archive_manifest
    ADD COLUMN IF NOT EXISTS manifest_uri VARCHAR(1024) NULL AFTER object_uri,
    ADD COLUMN IF NOT EXISTS object_count INT UNSIGNED NOT NULL DEFAULT 0 AFTER row_count,
    ADD COLUMN IF NOT EXISTS run_id CHAR(36) NULL AFTER schema_version,
    ADD COLUMN IF NOT EXISTS code_version VARCHAR(64) NULL AFTER run_id,
    ADD COLUMN IF NOT EXISTS min_event_time_utc DATETIME(6) NULL AFTER code_version,
    ADD COLUMN IF NOT EXISTS max_event_time_utc DATETIME(6) NULL AFTER min_event_time_utc,
    ADD COLUMN IF NOT EXISTS period_closed BOOLEAN NOT NULL DEFAULT TRUE
        AFTER max_event_time_utc;

CREATE TABLE IF NOT EXISTS archive_restore_result (
    restore_run_id CHAR(36) NOT NULL,
    dataset_name VARCHAR(128) NOT NULL,
    archive_year SMALLINT UNSIGNED NOT NULL,
    archive_version INT UNSIGNED NOT NULL,
    sample_row_count INT UNSIGNED NOT NULL,
    status ENUM('PASS','FAIL') NOT NULL,
    verified_at_utc DATETIME(6) NOT NULL,
    PRIMARY KEY (restore_run_id),
    KEY ix_archive_restore_source (dataset_name, archive_year, archive_version)
) ENGINE=InnoDB;

CREATE DATABASE IF NOT EXISTS marketpilot_restore
    CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS marketpilot_restore.restore_market_bar_1m (
    restore_run_id CHAR(36) NOT NULL,
    symbol VARCHAR(16) NOT NULL,
    event_time_utc DATETIME(6) NOT NULL,
    bar_interval VARCHAR(16) NOT NULL,
    open_price DECIMAL(19,6) NOT NULL,
    high_price DECIMAL(19,6) NOT NULL,
    low_price DECIMAL(19,6) NOT NULL,
    close_price DECIMAL(19,6) NOT NULL,
    volume BIGINT UNSIGNED NOT NULL,
    certification_status ENUM('PROVISIONAL','CERTIFIED') NOT NULL,
    source_event_id CHAR(36) NOT NULL,
    source_name VARCHAR(32) NOT NULL,
    ingested_at_utc DATETIME(6) NOT NULL,
    pipeline_run_id CHAR(36) NOT NULL,
    code_version VARCHAR(64) NOT NULL,
    data_version VARCHAR(64) NOT NULL,
    schema_version SMALLINT UNSIGNED NOT NULL,
    restored_at_utc TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    PRIMARY KEY (restore_run_id, symbol, event_time_utc, bar_interval),
    CONSTRAINT ck_restore_market_bar_ohlc
        CHECK (high_price >= GREATEST(open_price, close_price, low_price)),
    CONSTRAINT ck_restore_market_bar_low
        CHECK (low_price <= LEAST(open_price, close_price, high_price))
) ENGINE=InnoDB;
