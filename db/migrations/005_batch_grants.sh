#!/usr/bin/env bash
set -euo pipefail

marketpilot_sql_escape() {
    local value="$1"
    printf '%s' "${value//\'/\'\'}"
}

marketpilot_publish_user="$(marketpilot_sql_escape "${MARIADB_PUBLISH_USER:?missing}")"
marketpilot_publish_password="$(marketpilot_sql_escape "${MARIADB_PUBLISH_PASSWORD:?missing}")"

mariadb --protocol=socket -uroot -p"${MARIADB_ROOT_PASSWORD}" <<SQL
CREATE USER IF NOT EXISTS '${marketpilot_publish_user}'@'%'
    IDENTIFIED BY '${marketpilot_publish_password}';
ALTER USER '${marketpilot_publish_user}'@'%'
    IDENTIFIED BY '${marketpilot_publish_password}';
REVOKE ALL PRIVILEGES, GRANT OPTION FROM '${marketpilot_publish_user}'@'%';
GRANT SELECT, INSERT ON marketpilot.dim_symbol
    TO '${marketpilot_publish_user}'@'%';
GRANT SELECT, INSERT, UPDATE, DELETE ON marketpilot.fact_market_bar_1m
    TO '${marketpilot_publish_user}'@'%';
GRANT SELECT, INSERT, UPDATE, DELETE ON marketpilot.stg_market_bar_1m
    TO '${marketpilot_publish_user}'@'%';
GRANT SELECT, INSERT, UPDATE ON marketpilot.data_quality_result
    TO '${marketpilot_publish_user}'@'%';
GRANT SELECT, INSERT, UPDATE ON marketpilot.etl_watermark
    TO '${marketpilot_publish_user}'@'%';
FLUSH PRIVILEGES;
SQL

unset marketpilot_publish_user marketpilot_publish_password
unset -f marketpilot_sql_escape
