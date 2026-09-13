USE marketpilot;

CREATE TABLE IF NOT EXISTS fact_fundamental_metric (
    symbol_id BIGINT UNSIGNED NOT NULL,
    metric_code VARCHAR(64) NOT NULL,
    period_end_date DATE NOT NULL,
    period_type ENUM('QUARTER','ANNUAL','TTM') NOT NULL,
    value_decimal DECIMAL(28,8) NOT NULL,
    unit VARCHAR(32) NOT NULL,
    filed_at_utc DATETIME(6) NOT NULL,
    accession_number VARCHAR(24) NULL,
    bronze_uri VARCHAR(1024) NOT NULL,
    source_name VARCHAR(32) NOT NULL DEFAULT 'sec_companyfacts',
    pipeline_run_id CHAR(36) NOT NULL,
    code_version VARCHAR(64) NOT NULL,
    data_version VARCHAR(64) NOT NULL,
    schema_version SMALLINT UNSIGNED NOT NULL DEFAULT 1,
    PRIMARY KEY (symbol_id, metric_code, period_end_date, period_type),
    KEY ix_fundamental_freshness (symbol_id, filed_at_utc),
    CONSTRAINT fk_fundamental_symbol FOREIGN KEY (symbol_id) REFERENCES dim_symbol(symbol_id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS fact_opportunity_recommendation (
    recommendation_id CHAR(36) NOT NULL,
    symbol_id BIGINT UNSIGNED NOT NULL,
    as_of_utc DATETIME(6) NOT NULL,
    market_data_time_utc DATETIME(6) NOT NULL,
    fundamentals_as_of_utc DATETIME(6) NULL,
    action ENUM('BUY ZONE','WAIT','WATCH BREAKOUT','AVOID','INSUFFICIENT DATA') NOT NULL,
    actionable BOOLEAN NOT NULL DEFAULT FALSE,
    lifecycle_status ENUM('PROVISIONAL','CERTIFIED','STALE','INSUFFICIENT_DATA') NOT NULL,
    technical_score DECIMAL(6,2) NOT NULL,
    fundamental_score DECIMAL(6,2) NOT NULL,
    opportunity_score DECIMAL(6,2) NOT NULL,
    confidence DECIMAL(6,2) NOT NULL,
    market_price DECIMAL(19,6) NOT NULL,
    buy_zone_low DECIMAL(19,6) NOT NULL,
    buy_zone_high DECIMAL(19,6) NOT NULL,
    stop_price DECIMAL(19,6) NOT NULL,
    target_1 DECIMAL(19,6) NOT NULL,
    target_2 DECIMAL(19,6) NOT NULL,
    risk_reward_1 DECIMAL(10,4) NOT NULL,
    risk_reward_2 DECIMAL(10,4) NOT NULL,
    potential_profit_1_pct DECIMAL(10,4) NOT NULL,
    potential_profit_2_pct DECIMAL(10,4) NOT NULL,
    valid_until_utc DATETIME(6) NOT NULL,
    feed_name VARCHAR(16) NOT NULL,
    model_version VARCHAR(64) NOT NULL,
    input_snapshot_json JSON NOT NULL,
    explanation_json JSON NOT NULL,
    pipeline_run_id CHAR(36) NOT NULL,
    code_version VARCHAR(64) NOT NULL,
    data_version VARCHAR(64) NOT NULL,
    schema_version SMALLINT UNSIGNED NOT NULL DEFAULT 1,
    created_at_utc TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    PRIMARY KEY (recommendation_id),
    UNIQUE KEY uq_recommendation_version (symbol_id, as_of_utc, model_version, lifecycle_status),
    KEY ix_recommendation_current (symbol_id, as_of_utc, lifecycle_status),
    CONSTRAINT fk_recommendation_symbol FOREIGN KEY (symbol_id) REFERENCES dim_symbol(symbol_id),
    CONSTRAINT ck_recommendation_zone CHECK (buy_zone_low <= buy_zone_high),
    CONSTRAINT ck_recommendation_score CHECK (opportunity_score BETWEEN 0 AND 100)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS user_portfolio (
    portfolio_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    portfolio_key VARCHAR(64) NOT NULL DEFAULT 'local-default',
    equity DECIMAL(19,2) NOT NULL,
    cash_balance DECIMAL(19,2) NOT NULL,
    risk_per_trade_pct DECIMAL(5,2) NOT NULL DEFAULT 2.00,
    max_symbol_exposure_pct DECIMAL(5,2) NOT NULL DEFAULT 20.00,
    max_open_risk_pct DECIMAL(5,2) NOT NULL DEFAULT 6.00,
    updated_at_utc TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    PRIMARY KEY (portfolio_id),
    UNIQUE KEY uq_portfolio_key (portfolio_key)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS user_position (
    portfolio_id BIGINT UNSIGNED NOT NULL,
    symbol_id BIGINT UNSIGNED NOT NULL,
    quantity DECIMAL(19,6) NOT NULL,
    average_cost DECIMAL(19,6) NOT NULL,
    planned_stop DECIMAL(19,6) NULL,
    updated_at_utc TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    PRIMARY KEY (portfolio_id, symbol_id),
    CONSTRAINT fk_position_portfolio FOREIGN KEY (portfolio_id) REFERENCES user_portfolio(portfolio_id),
    CONSTRAINT fk_position_symbol FOREIGN KEY (symbol_id) REFERENCES dim_symbol(symbol_id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS user_watchlist_symbol (
    portfolio_id BIGINT UNSIGNED NOT NULL,
    symbol_id BIGINT UNSIGNED NOT NULL,
    added_at_utc TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    PRIMARY KEY (portfolio_id, symbol_id),
    CONSTRAINT fk_watchlist_portfolio FOREIGN KEY (portfolio_id) REFERENCES user_portfolio(portfolio_id),
    CONSTRAINT fk_watchlist_symbol FOREIGN KEY (symbol_id) REFERENCES dim_symbol(symbol_id)
) ENGINE=InnoDB;

INSERT INTO user_portfolio (portfolio_key, equity, cash_balance)
VALUES ('local-default', 10000.00, 10000.00)
ON DUPLICATE KEY UPDATE portfolio_key=VALUES(portfolio_key);

INSERT IGNORE INTO user_watchlist_symbol (portfolio_id, symbol_id)
SELECT p.portfolio_id, s.symbol_id FROM user_portfolio p JOIN dim_symbol s
WHERE p.portfolio_key='local-default' AND s.symbol IN ('AAPL','MSFT','NVDA','SPY');
