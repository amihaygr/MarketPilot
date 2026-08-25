#!/usr/bin/env bash
set -euo pipefail

marketpilot_sql_escape() {
    local value="$1"
    printf '%s' "${value//\'/\'\'}"
}

marketpilot_app_user="$(marketpilot_sql_escape "${MARIADB_APP_USER:?missing}")"
marketpilot_app_password="$(marketpilot_sql_escape "${MARIADB_APP_PASSWORD:?missing}")"

mariadb --protocol=socket -uroot -p"${MARIADB_ROOT_PASSWORD}" <<SQL
CREATE USER IF NOT EXISTS '${marketpilot_app_user}'@'%'
    IDENTIFIED BY '${marketpilot_app_password}';
ALTER USER '${marketpilot_app_user}'@'%'
    IDENTIFIED BY '${marketpilot_app_password}';
REVOKE ALL PRIVILEGES, GRANT OPTION FROM '${marketpilot_app_user}'@'%';
GRANT SELECT ON marketpilot.dim_symbol
    TO '${marketpilot_app_user}'@'%';
GRANT SELECT ON marketpilot.fact_market_bar_1m
    TO '${marketpilot_app_user}'@'%';
GRANT SELECT ON marketpilot.fact_sec_filing
    TO '${marketpilot_app_user}'@'%';
GRANT SELECT ON marketpilot.etl_watermark
    TO '${marketpilot_app_user}'@'%';
FLUSH PRIVILEGES;
SQL

unset marketpilot_app_user marketpilot_app_password
unset -f marketpilot_sql_escape
