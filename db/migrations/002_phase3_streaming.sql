USE marketpilot;

ALTER TABLE fact_market_bar_1m
    ADD COLUMN IF NOT EXISTS bar_interval VARCHAR(16) NOT NULL DEFAULT '1Min'
        AFTER event_time_utc,
    ADD COLUMN IF NOT EXISTS source_name VARCHAR(32) NOT NULL DEFAULT 'synthetic'
        AFTER source_event_id,
    ADD COLUMN IF NOT EXISTS ingested_at_utc DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
        AFTER source_name,
    ADD COLUMN IF NOT EXISTS kafka_topic VARCHAR(249) NOT NULL DEFAULT 'legacy'
        AFTER ingested_at_utc,
    ADD COLUMN IF NOT EXISTS kafka_partition INT NOT NULL DEFAULT -1
        AFTER kafka_topic,
    ADD COLUMN IF NOT EXISTS kafka_offset BIGINT NOT NULL DEFAULT -1
        AFTER kafka_partition,
    ADD COLUMN IF NOT EXISTS code_version VARCHAR(64) NOT NULL DEFAULT 'legacy'
        AFTER pipeline_run_id,
    ADD COLUMN IF NOT EXISTS data_version VARCHAR(64) NOT NULL DEFAULT 'market-bar-v1'
        AFTER code_version;

DROP PROCEDURE IF EXISTS migrate_market_bar_primary_key;
DELIMITER //
CREATE PROCEDURE migrate_market_bar_primary_key()
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.statistics
        WHERE table_schema = DATABASE()
          AND table_name = 'fact_market_bar_1m'
          AND index_name = 'PRIMARY'
          AND column_name = 'bar_interval'
    ) THEN
        ALTER TABLE fact_market_bar_1m
            DROP PRIMARY KEY,
            ADD PRIMARY KEY (symbol_id, event_time_utc, bar_interval);
    END IF;
END //
DELIMITER ;
CALL migrate_market_bar_primary_key();
DROP PROCEDURE migrate_market_bar_primary_key;

CREATE INDEX IF NOT EXISTS ix_market_bar_time_status
    ON fact_market_bar_1m (event_time_utc, certification_status);
