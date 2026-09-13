USE marketpilot;

CREATE TABLE IF NOT EXISTS fact_corporate_action (
    corporate_action_id VARCHAR(64) NOT NULL,
    symbol_id BIGINT UNSIGNED NOT NULL,
    action_type VARCHAR(48) NOT NULL,
    process_date DATE NOT NULL,
    ex_date DATE NULL,
    record_date DATE NULL,
    payable_date DATE NULL,
    old_rate DECIMAL(28,10) NULL,
    new_rate DECIMAL(28,10) NULL,
    cash_amount DECIMAL(28,10) NULL,
    currency VARCHAR(8) NULL,
    source_name VARCHAR(32) NOT NULL DEFAULT 'alpaca',
    bronze_uri VARCHAR(1024) NOT NULL,
    source_payload_json JSON NOT NULL,
    pipeline_run_id CHAR(36) NOT NULL,
    code_version VARCHAR(64) NOT NULL,
    data_version VARCHAR(64) NOT NULL DEFAULT 'corporate-action-v1',
    schema_version SMALLINT UNSIGNED NOT NULL DEFAULT 1,
    ingested_at_utc TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    PRIMARY KEY (corporate_action_id),
    KEY ix_corporate_action_symbol_date (symbol_id, process_date),
    CONSTRAINT fk_corporate_action_symbol FOREIGN KEY (symbol_id) REFERENCES dim_symbol(symbol_id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS fact_recommendation_evaluation (
    recommendation_id CHAR(36) NOT NULL,
    horizon_sessions SMALLINT UNSIGNED NOT NULL,
    evaluation_date DATE NOT NULL,
    entry_price DECIMAL(19,6) NOT NULL,
    observed_close DECIMAL(19,6) NOT NULL,
    observed_high DECIMAL(19,6) NOT NULL,
    observed_low DECIMAL(19,6) NOT NULL,
    realized_return_pct DECIMAL(12,6) NOT NULL,
    max_favorable_excursion_pct DECIMAL(12,6) NOT NULL,
    max_adverse_excursion_pct DECIMAL(12,6) NOT NULL,
    target_1_hit BOOLEAN NOT NULL,
    target_2_hit BOOLEAN NOT NULL,
    stop_hit BOOLEAN NOT NULL,
    outcome ENUM('TARGET_2','TARGET_1','STOP','OPEN','EXPIRED') NOT NULL,
    pipeline_run_id CHAR(36) NOT NULL,
    code_version VARCHAR(64) NOT NULL,
    data_version VARCHAR(64) NOT NULL DEFAULT 'recommendation-evaluation-v1',
    schema_version SMALLINT UNSIGNED NOT NULL DEFAULT 1,
    evaluated_at_utc TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    PRIMARY KEY (recommendation_id, horizon_sessions),
    CONSTRAINT fk_recommendation_evaluation FOREIGN KEY (recommendation_id)
        REFERENCES fact_opportunity_recommendation(recommendation_id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS fact_decision_alert (
    alert_id CHAR(36) NOT NULL,
    recommendation_id CHAR(36) NOT NULL,
    symbol_id BIGINT UNSIGNED NOT NULL,
    alert_type ENUM('ENTERED_BUY_ZONE','ACTION_CHANGED','DATA_STALE','RISK_BLOCKED') NOT NULL,
    severity ENUM('INFO','WATCH','WARNING') NOT NULL,
    title VARCHAR(160) NOT NULL,
    message VARCHAR(512) NOT NULL,
    created_at_utc DATETIME(6) NOT NULL,
    acknowledged_at_utc DATETIME(6) NULL,
    schema_version SMALLINT UNSIGNED NOT NULL DEFAULT 1,
    PRIMARY KEY (alert_id),
    UNIQUE KEY uq_decision_alert_event (recommendation_id, alert_type),
    KEY ix_decision_alert_current (created_at_utc, acknowledged_at_utc),
    CONSTRAINT fk_decision_alert_recommendation FOREIGN KEY (recommendation_id)
        REFERENCES fact_opportunity_recommendation(recommendation_id),
    CONSTRAINT fk_decision_alert_symbol FOREIGN KEY (symbol_id) REFERENCES dim_symbol(symbol_id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS shadow_mode_status (
    model_version VARCHAR(64) NOT NULL,
    required_sessions SMALLINT UNSIGNED NOT NULL DEFAULT 20,
    completed_sessions SMALLINT UNSIGNED NOT NULL DEFAULT 0,
    first_session_date DATE NULL,
    latest_session_date DATE NULL,
    promotion_status ENUM('COLLECTING','READY_FOR_REVIEW','APPROVED','REJECTED') NOT NULL
        DEFAULT 'COLLECTING',
    approved_at_utc DATETIME(6) NULL,
    approval_note VARCHAR(512) NULL,
    updated_at_utc TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    PRIMARY KEY (model_version),
    CONSTRAINT ck_shadow_completed CHECK (completed_sessions <= required_sessions)
) ENGINE=InnoDB;

INSERT INTO shadow_mode_status (model_version, required_sessions)
VALUES ('decision-intelligence-v1', 20)
ON DUPLICATE KEY UPDATE required_sessions=VALUES(required_sessions);
