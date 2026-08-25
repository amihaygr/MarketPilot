#!/usr/bin/env bash
set -euo pipefail

marketpilot_sql_escape() {
    local value="$1"
    printf '%s' "${value//\'/\'\'}"
}

marketpilot_sec_user="$(marketpilot_sql_escape "${MARIADB_SEC_USER:?missing}")"
marketpilot_sec_password="$(marketpilot_sql_escape "${MARIADB_SEC_PASSWORD:?missing}")"

mariadb --protocol=socket -uroot -p"${MARIADB_ROOT_PASSWORD}" <<SQL
CREATE USER IF NOT EXISTS '${marketpilot_sec_user}'@'%'
    IDENTIFIED BY '${marketpilot_sec_password}';
ALTER USER '${marketpilot_sec_user}'@'%'
    IDENTIFIED BY '${marketpilot_sec_password}';
REVOKE ALL PRIVILEGES, GRANT OPTION FROM '${marketpilot_sec_user}'@'%';
GRANT SELECT, INSERT ON marketpilot.dim_symbol
    TO '${marketpilot_sec_user}'@'%';
GRANT SELECT, INSERT, UPDATE ON marketpilot.fact_sec_filing
    TO '${marketpilot_sec_user}'@'%';
GRANT SELECT, INSERT, UPDATE ON marketpilot.etl_watermark
    TO '${marketpilot_sec_user}'@'%';
FLUSH PRIVILEGES;
SQL

unset marketpilot_sec_user marketpilot_sec_password
unset -f marketpilot_sql_escape
