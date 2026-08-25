#!/usr/bin/env bash
set -euo pipefail

marketpilot_sql_escape() {
    local value="$1"
    printf '%s' "${value//\'/\'\'}"
}

marketpilot_ingest_user="$(marketpilot_sql_escape "${MARIADB_INGEST_USER:?missing}")"
marketpilot_ingest_password="$(marketpilot_sql_escape "${MARIADB_INGEST_PASSWORD:?missing}")"

mariadb --protocol=socket -uroot -p"${MARIADB_ROOT_PASSWORD}" <<SQL
CREATE USER IF NOT EXISTS '${marketpilot_ingest_user}'@'%'
    IDENTIFIED BY '${marketpilot_ingest_password}';
ALTER USER '${marketpilot_ingest_user}'@'%'
    IDENTIFIED BY '${marketpilot_ingest_password}';
REVOKE ALL PRIVILEGES, GRANT OPTION FROM '${marketpilot_ingest_user}'@'%';
GRANT SELECT, INSERT, UPDATE ON marketpilot.dim_symbol
    TO '${marketpilot_ingest_user}'@'%';
GRANT SELECT, INSERT, UPDATE ON marketpilot.fact_market_bar_1m
    TO '${marketpilot_ingest_user}'@'%';
FLUSH PRIVILEGES;
SQL

unset marketpilot_ingest_user marketpilot_ingest_password
unset -f marketpilot_sql_escape
