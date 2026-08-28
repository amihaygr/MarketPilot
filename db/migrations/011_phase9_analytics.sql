USE marketpilot;

CREATE TABLE IF NOT EXISTS fact_indicator_1m (
    symbol_id BIGINT UNSIGNED NOT NULL,
    event_time_utc DATETIME(6) NOT NULL,
    indicator_code VARCHAR(64) NOT NULL,
    indicator_version SMALLINT UNSIGNED NOT NULL,
    indicator_value DECIMAL(24,10) NOT NULL,
    lookback_bars SMALLINT UNSIGNED NOT NULL,
    certification_status ENUM('PROVISIONAL','CERTIFIED') NOT NULL,
    pipeline_run_id CHAR(36) NOT NULL,
    code_version VARCHAR(64) NOT NULL,
    data_version VARCHAR(64) NOT NULL,
    schema_version SMALLINT UNSIGNED NOT NULL,
    calculated_at_utc TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    PRIMARY KEY (symbol_id, event_time_utc, indicator_code, indicator_version),
    KEY ix_indicator_code_time (indicator_code, event_time_utc),
    KEY ix_indicator_symbol_time (symbol_id, event_time_utc),
    CONSTRAINT fk_indicator_symbol FOREIGN KEY (symbol_id) REFERENCES dim_symbol(symbol_id),
    CONSTRAINT ck_indicator_lookback CHECK (lookback_bars > 0),
    CONSTRAINT ck_indicator_schema CHECK (schema_version > 0)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS fact_signal (
    symbol_id BIGINT UNSIGNED NOT NULL,
    signal_time_utc DATETIME(6) NOT NULL,
    signal_code VARCHAR(64) NOT NULL,
    model_version SMALLINT UNSIGNED NOT NULL,
    direction ENUM('BULLISH','BEARISH','WATCH') NOT NULL,
    strength DECIMAL(8,6) NOT NULL,
    explanation VARCHAR(512) NOT NULL,
    certification_status ENUM('PROVISIONAL','CERTIFIED') NOT NULL,
    pipeline_run_id CHAR(36) NOT NULL,
    code_version VARCHAR(64) NOT NULL,
    data_version VARCHAR(64) NOT NULL,
    schema_version SMALLINT UNSIGNED NOT NULL,
    calculated_at_utc TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    PRIMARY KEY (symbol_id, signal_time_utc, signal_code, model_version),
    KEY ix_signal_time_direction (signal_time_utc, direction),
    KEY ix_signal_symbol_time (symbol_id, signal_time_utc),
    CONSTRAINT fk_signal_symbol FOREIGN KEY (symbol_id) REFERENCES dim_symbol(symbol_id),
    CONSTRAINT ck_signal_strength CHECK (strength >= 0 AND strength <= 1),
    CONSTRAINT ck_signal_schema CHECK (schema_version > 0)
) ENGINE=InnoDB;
