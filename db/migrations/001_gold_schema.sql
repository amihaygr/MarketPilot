CREATE DATABASE IF NOT EXISTS marketpilot CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE marketpilot;

CREATE TABLE IF NOT EXISTS dim_symbol (
    symbol_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    symbol VARCHAR(16) NOT NULL,
    display_name VARCHAR(255) NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at_utc TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    PRIMARY KEY (symbol_id),
    UNIQUE KEY uq_dim_symbol_symbol (symbol)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS fact_market_bar_1m (
    symbol_id BIGINT UNSIGNED NOT NULL,
    event_time_utc DATETIME(6) NOT NULL,
    open_price DECIMAL(19,6) NOT NULL,
    high_price DECIMAL(19,6) NOT NULL,
    low_price DECIMAL(19,6) NOT NULL,
    close_price DECIMAL(19,6) NOT NULL,
    volume BIGINT UNSIGNED NOT NULL,
    certification_status ENUM('PROVISIONAL','CERTIFIED') NOT NULL,
    source_event_id CHAR(36) NOT NULL,
    pipeline_run_id CHAR(36) NOT NULL,
    schema_version SMALLINT UNSIGNED NOT NULL,
    updated_at_utc TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    PRIMARY KEY (symbol_id, event_time_utc),
    UNIQUE KEY uq_market_bar_source_event (source_event_id),
    CONSTRAINT fk_market_bar_symbol FOREIGN KEY (symbol_id) REFERENCES dim_symbol(symbol_id),
    CONSTRAINT ck_market_bar_ohlc CHECK (high_price >= GREATEST(open_price, close_price, low_price)),
    CONSTRAINT ck_market_bar_low CHECK (low_price <= LEAST(open_price, close_price, high_price))
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS etl_watermark (
    pipeline_name VARCHAR(128) NOT NULL,
    partition_key VARCHAR(255) NOT NULL,
    watermark_utc DATETIME(6) NULL,
    status ENUM('STARTED','VALIDATED','PUBLISHED','FAILED') NOT NULL,
    run_id CHAR(36) NOT NULL,
    updated_at_utc TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    PRIMARY KEY (pipeline_name, partition_key)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS data_quality_result (
    result_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    run_id CHAR(36) NOT NULL,
    dataset_name VARCHAR(128) NOT NULL,
    partition_key VARCHAR(255) NOT NULL,
    check_name VARCHAR(128) NOT NULL,
    status ENUM('PASS','WARN','FAIL') NOT NULL,
    observed_value VARCHAR(255) NULL,
    expected_value VARCHAR(255) NULL,
    measured_at_utc TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    PRIMARY KEY (result_id),
    KEY ix_dq_run_dataset (run_id, dataset_name)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS archive_manifest (
    dataset_name VARCHAR(128) NOT NULL,
    archive_year SMALLINT UNSIGNED NOT NULL,
    archive_version INT UNSIGNED NOT NULL,
    object_uri VARCHAR(1024) NOT NULL,
    row_count BIGINT UNSIGNED NOT NULL,
    checksum_sha256 CHAR(64) NOT NULL,
    schema_version SMALLINT UNSIGNED NOT NULL,
    verified_at_utc DATETIME(6) NOT NULL,
    PRIMARY KEY (dataset_name, archive_year, archive_version)
) ENGINE=InnoDB;
