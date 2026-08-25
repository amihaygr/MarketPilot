USE marketpilot;

CREATE TABLE IF NOT EXISTS fact_sec_filing (
    accession_number VARCHAR(24) NOT NULL,
    symbol_id BIGINT UNSIGNED NOT NULL,
    cik CHAR(10) NOT NULL,
    company_name VARCHAR(255) NOT NULL,
    form_type VARCHAR(32) NOT NULL,
    filing_date DATE NOT NULL,
    report_date DATE NULL,
    acceptance_datetime_utc DATETIME(6) NULL,
    primary_document VARCHAR(255) NOT NULL,
    primary_document_description VARCHAR(512) NULL,
    items VARCHAR(512) NULL,
    file_number VARCHAR(64) NULL,
    film_number VARCHAR(64) NULL,
    filing_size BIGINT UNSIGNED NULL,
    is_xbrl BOOLEAN NOT NULL DEFAULT FALSE,
    is_inline_xbrl BOOLEAN NOT NULL DEFAULT FALSE,
    source_url VARCHAR(1024) NOT NULL,
    bronze_uri VARCHAR(1024) NOT NULL,
    source_sha256 CHAR(64) NOT NULL,
    pipeline_run_id CHAR(36) NOT NULL,
    code_version VARCHAR(64) NOT NULL,
    schema_version SMALLINT UNSIGNED NOT NULL,
    ingested_at_utc DATETIME(6) NOT NULL,
    first_seen_at_utc TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at_utc TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
        ON UPDATE CURRENT_TIMESTAMP(6),
    PRIMARY KEY (accession_number),
    KEY ix_sec_filing_symbol_date (symbol_id, filing_date),
    KEY ix_sec_filing_form_date (form_type, filing_date),
    KEY ix_sec_filing_cik_date (cik, filing_date),
    CONSTRAINT fk_sec_filing_symbol
        FOREIGN KEY (symbol_id) REFERENCES dim_symbol(symbol_id)
) ENGINE=InnoDB;
