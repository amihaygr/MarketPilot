USE marketpilot;

CREATE TABLE IF NOT EXISTS stg_market_bar_1m (
    run_id CHAR(36) NOT NULL,
    logical_date DATE NOT NULL,
    symbol VARCHAR(16) NOT NULL,
    event_time_utc DATETIME(6) NOT NULL,
    bar_interval VARCHAR(16) NOT NULL,
    open_price DECIMAL(19,6) NOT NULL,
    high_price DECIMAL(19,6) NOT NULL,
    low_price DECIMAL(19,6) NOT NULL,
    close_price DECIMAL(19,6) NOT NULL,
    volume BIGINT UNSIGNED NOT NULL,
    source_event_id CHAR(36) NOT NULL,
    source_name VARCHAR(32) NOT NULL,
    ingested_at_utc DATETIME(6) NOT NULL,
    kafka_topic VARCHAR(249) NOT NULL,
    kafka_partition INT NOT NULL,
    kafka_offset BIGINT NOT NULL,
    code_version VARCHAR(64) NOT NULL,
    data_version VARCHAR(64) NOT NULL,
    schema_version SMALLINT UNSIGNED NOT NULL,
    staged_at_utc TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    PRIMARY KEY (run_id, symbol, event_time_utc, bar_interval),
    KEY ix_stg_market_bar_partition (logical_date, run_id),
    CONSTRAINT ck_stg_market_bar_ohlc
        CHECK (high_price >= GREATEST(open_price, close_price, low_price)),
    CONSTRAINT ck_stg_market_bar_low
        CHECK (low_price <= LEAST(open_price, close_price, high_price))
) ENGINE=InnoDB;

CREATE UNIQUE INDEX IF NOT EXISTS uq_dq_result_run_check
    ON data_quality_result (run_id, dataset_name, partition_key, check_name);
