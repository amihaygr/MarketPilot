#!/usr/bin/env bash
set -euo pipefail

marketpilot_sql_escape() {
    local value="$1"
    printf '%s' "${value//\'/\'\'}"
}

marketpilot_publish_user="$(marketpilot_sql_escape "${MARIADB_PUBLISH_USER:?missing}")"

mariadb --protocol=socket -uroot -p"${MARIADB_ROOT_PASSWORD}" <<SQL
GRANT SELECT, INSERT, UPDATE ON marketpilot.archive_manifest
    TO '${marketpilot_publish_user}'@'%';
GRANT SELECT, INSERT, UPDATE ON marketpilot.archive_restore_result
    TO '${marketpilot_publish_user}'@'%';
GRANT SELECT, INSERT, UPDATE, DELETE ON marketpilot_restore.restore_market_bar_1m
    TO '${marketpilot_publish_user}'@'%';
FLUSH PRIVILEGES;
SQL

unset marketpilot_publish_user
unset -f marketpilot_sql_escape
