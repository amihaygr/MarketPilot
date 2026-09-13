#!/usr/bin/env bash
set -euo pipefail
escape_sql() { printf '%s' "${1//\'/\'\'}"; }
writer="$(escape_sql "${MARIADB_USER_WRITE_USER:-marketpilot_user_write}")"
password="$(escape_sql "${MARIADB_USER_WRITE_PASSWORD:-${MARIADB_APP_PASSWORD:?missing}}")"
mariadb --protocol=socket -uroot -p"${MARIADB_ROOT_PASSWORD}" <<SQL
CREATE USER IF NOT EXISTS '${writer}'@'%' IDENTIFIED BY '${password}';
ALTER USER '${writer}'@'%' IDENTIFIED BY '${password}';
REVOKE ALL PRIVILEGES, GRANT OPTION FROM '${writer}'@'%';
GRANT SELECT, INSERT, UPDATE ON marketpilot.user_portfolio TO '${writer}'@'%';
GRANT SELECT, INSERT, UPDATE, DELETE ON marketpilot.user_position TO '${writer}'@'%';
GRANT SELECT, INSERT, DELETE ON marketpilot.user_watchlist_symbol TO '${writer}'@'%';
GRANT SELECT ON marketpilot.dim_symbol TO '${writer}'@'%';
FLUSH PRIVILEGES;
SQL
