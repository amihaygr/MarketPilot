USE marketpilot;

CREATE TABLE IF NOT EXISTS fact_decision_feature_snapshot (
    snapshot_id CHAR(36) NOT NULL,
    symbol_id BIGINT UNSIGNED NOT NULL,
    as_of_utc DATETIME(6) NOT NULL,
    feature_schema_version SMALLINT UNSIGNED NOT NULL DEFAULT 2,
    feature_json JSON NOT NULL,
    market_data_time_utc DATETIME(6) NOT NULL,
    fundamentals_as_of_utc DATETIME(6) NULL,
    certification_status ENUM('PROVISIONAL','CERTIFIED') NOT NULL,
    feed_name VARCHAR(16) NOT NULL,
    pipeline_run_id CHAR(36) NOT NULL,
    code_version VARCHAR(64) NOT NULL,
    data_version VARCHAR(64) NOT NULL DEFAULT 'decision-feature-v2',
    created_at_utc TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    PRIMARY KEY (snapshot_id),
    UNIQUE KEY uq_feature_snapshot (symbol_id, as_of_utc, feature_schema_version),
    KEY ix_feature_training_scope (certification_status, as_of_utc),
    CONSTRAINT fk_feature_symbol FOREIGN KEY (symbol_id) REFERENCES dim_symbol(symbol_id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS fact_decision_label (
    snapshot_id CHAR(36) NOT NULL,
    horizon_sessions SMALLINT UNSIGNED NOT NULL DEFAULT 10,
    entry_filled BOOLEAN NOT NULL,
    entry_time_utc DATETIME(6) NULL,
    entry_price DECIMAL(19,6) NULL,
    outcome ENUM('TARGET_2','TARGET_1','STOP','EXPIRED','NO_ENTRY') NOT NULL,
    target_before_stop BOOLEAN NULL,
    observed_close DECIMAL(19,6) NULL,
    observed_high DECIMAL(19,6) NULL,
    observed_low DECIMAL(19,6) NULL,
    evaluated_through_date DATE NOT NULL,
    pipeline_run_id CHAR(36) NOT NULL,
    code_version VARCHAR(64) NOT NULL,
    label_schema_version SMALLINT UNSIGNED NOT NULL DEFAULT 2,
    evaluated_at_utc TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    PRIMARY KEY (snapshot_id, horizon_sessions),
    KEY ix_label_training (entry_filled, target_before_stop, evaluated_through_date),
    CONSTRAINT fk_label_snapshot FOREIGN KEY (snapshot_id)
        REFERENCES fact_decision_feature_snapshot(snapshot_id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS decision_model_registry (
    model_version VARCHAR(96) NOT NULL,
    model_family ENUM('LOGISTIC_REGRESSION','HIST_GRADIENT_BOOSTING') NOT NULL,
    status ENUM('PREVIEW','ACTIVE','FALLBACK','REJECTED') NOT NULL DEFAULT 'PREVIEW',
    artifact_uri VARCHAR(1024) NOT NULL,
    artifact_sha256 CHAR(64) NOT NULL,
    feature_schema_version SMALLINT UNSIGNED NOT NULL,
    trained_from_date DATE NOT NULL,
    trained_through_date DATE NOT NULL,
    activation_threshold DECIMAL(7,6) NOT NULL,
    calibration_method VARCHAR(32) NOT NULL DEFAULT 'sigmoid',
    promotion_eligible BOOLEAN NOT NULL DEFAULT FALSE,
    promotion_reasons_json JSON NOT NULL,
    metrics_json JSON NOT NULL,
    training_run_id CHAR(36) NOT NULL,
    code_version VARCHAR(64) NOT NULL,
    created_at_utc TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    activated_at_utc DATETIME(6) NULL,
    PRIMARY KEY (model_version),
    KEY ix_model_current (status, created_at_utc),
    CONSTRAINT ck_model_threshold CHECK (activation_threshold BETWEEN 0.60 AND 1.00)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS fact_decision_model_prediction (
    recommendation_id CHAR(36) NOT NULL,
    model_version VARCHAR(96) NOT NULL,
    model_status ENUM('PREVIEW','ACTIVE','FALLBACK') NOT NULL,
    success_probability DECIMAL(8,7) NULL,
    expected_r DECIMAL(10,6) NULL,
    calibration_status ENUM('CALIBRATED','UNCALIBRATED','UNAVAILABLE') NOT NULL,
    top_positive_drivers_json JSON NOT NULL,
    top_negative_drivers_json JSON NOT NULL,
    scored_at_utc TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    PRIMARY KEY (recommendation_id, model_version),
    KEY ix_prediction_model_status (model_status, scored_at_utc),
    CONSTRAINT fk_prediction_recommendation FOREIGN KEY (recommendation_id)
        REFERENCES fact_opportunity_recommendation(recommendation_id),
    CONSTRAINT ck_prediction_probability CHECK (
        success_probability IS NULL OR success_probability BETWEEN 0 AND 1
    )
) ENGINE=InnoDB;

INSERT INTO shadow_mode_status (model_version, required_sessions)
VALUES ('decision-intelligence-v2-hybrid', 20)
ON DUPLICATE KEY UPDATE required_sessions=VALUES(required_sessions);
