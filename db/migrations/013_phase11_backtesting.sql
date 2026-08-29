USE marketpilot;

CREATE TABLE IF NOT EXISTS dim_strategy (
    strategy_code VARCHAR(64) NOT NULL,
    strategy_version SMALLINT UNSIGNED NOT NULL,
    display_name VARCHAR(128) NOT NULL,
    description VARCHAR(512) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at_utc TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    PRIMARY KEY (strategy_code, strategy_version)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS fact_backtest_run (
    run_id CHAR(36) NOT NULL,
    strategy_code VARCHAR(64) NOT NULL,
    strategy_version SMALLINT UNSIGNED NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    symbols_csv VARCHAR(512) NOT NULL,
    benchmark_symbol VARCHAR(12) NOT NULL,
    short_window SMALLINT UNSIGNED NOT NULL,
    long_window SMALLINT UNSIGNED NOT NULL,
    initial_capital DECIMAL(24,6) NOT NULL,
    transaction_cost_bps DECIMAL(10,4) NOT NULL,
    slippage_bps DECIMAL(10,4) NOT NULL,
    status ENUM('RUNNING','PUBLISHED','FAILED') NOT NULL,
    detailed_output_uri VARCHAR(1024) NULL,
    error_message VARCHAR(512) NULL,
    code_version VARCHAR(64) NOT NULL,
    data_version VARCHAR(64) NOT NULL,
    schema_version SMALLINT UNSIGNED NOT NULL,
    started_at_utc TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    completed_at_utc TIMESTAMP(6) NULL,
    PRIMARY KEY (run_id),
    KEY ix_backtest_run_status_time (status, started_at_utc),
    CONSTRAINT fk_backtest_strategy FOREIGN KEY (strategy_code, strategy_version)
        REFERENCES dim_strategy(strategy_code, strategy_version),
    CONSTRAINT ck_backtest_run_dates CHECK (end_date >= start_date),
    CONSTRAINT ck_backtest_windows CHECK (short_window >= 2 AND long_window > short_window),
    CONSTRAINT ck_backtest_capital CHECK (initial_capital > 0),
    CONSTRAINT ck_backtest_costs CHECK (transaction_cost_bps >= 0 AND slippage_bps >= 0),
    CONSTRAINT ck_backtest_schema CHECK (schema_version > 0)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS fact_backtest_result (
    run_id CHAR(36) NOT NULL,
    symbol_id BIGINT UNSIGNED NOT NULL,
    first_event_time_utc DATETIME(6) NOT NULL,
    last_event_time_utc DATETIME(6) NOT NULL,
    observation_count BIGINT UNSIGNED NOT NULL,
    trade_count INT UNSIGNED NOT NULL,
    total_return_pct DECIMAL(20,8) NOT NULL,
    benchmark_return_pct DECIMAL(20,8) NOT NULL,
    excess_return_pct DECIMAL(20,8) NOT NULL,
    max_drawdown_pct DECIMAL(20,8) NOT NULL,
    annualized_volatility_pct DECIMAL(20,8) NOT NULL,
    sharpe_ratio DECIMAL(20,8) NULL,
    created_at_utc TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    PRIMARY KEY (run_id, symbol_id),
    KEY ix_backtest_result_symbol_time (symbol_id, last_event_time_utc),
    CONSTRAINT fk_backtest_result_run FOREIGN KEY (run_id)
        REFERENCES fact_backtest_run(run_id) ON DELETE CASCADE,
    CONSTRAINT fk_backtest_result_symbol FOREIGN KEY (symbol_id)
        REFERENCES dim_symbol(symbol_id),
    CONSTRAINT ck_backtest_observations CHECK (observation_count > 0),
    CONSTRAINT ck_backtest_drawdown CHECK (max_drawdown_pct <= 0)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS fact_backtest_equity_daily (
    run_id CHAR(36) NOT NULL,
    symbol_id BIGINT UNSIGNED NOT NULL,
    trading_date DATE NOT NULL,
    event_time_utc DATETIME(6) NOT NULL,
    equity DECIMAL(24,6) NOT NULL,
    benchmark_equity DECIMAL(24,6) NOT NULL,
    drawdown_pct DECIMAL(20,8) NOT NULL,
    applied_position TINYINT UNSIGNED NOT NULL,
    created_at_utc TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    PRIMARY KEY (run_id, symbol_id, trading_date),
    KEY ix_backtest_equity_run_date (run_id, trading_date),
    CONSTRAINT fk_backtest_equity_run FOREIGN KEY (run_id)
        REFERENCES fact_backtest_run(run_id) ON DELETE CASCADE,
    CONSTRAINT fk_backtest_equity_symbol FOREIGN KEY (symbol_id)
        REFERENCES dim_symbol(symbol_id),
    CONSTRAINT ck_backtest_equity_positive CHECK (equity > 0 AND benchmark_equity > 0),
    CONSTRAINT ck_backtest_equity_drawdown CHECK (drawdown_pct <= 0),
    CONSTRAINT ck_backtest_position CHECK (applied_position IN (0, 1))
) ENGINE=InnoDB;

INSERT INTO dim_strategy (
    strategy_code, strategy_version, display_name, description
) VALUES (
    'SMA_CROSS_LONG_CASH', 1, 'SMA Crossover: Long or Cash',
    'A close-of-bar short/long SMA signal is applied from the following bar return.'
) ON DUPLICATE KEY UPDATE
    display_name = VALUES(display_name),
    description = VALUES(description);
