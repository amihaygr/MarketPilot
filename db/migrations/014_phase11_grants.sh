#!/usr/bin/env bash
set -euo pipefail

marketpilot_sql_escape() {
    local value="$1"
    printf '%s' "${value//\'/\'\'}"
}

publisher="$(marketpilot_sql_escape "${MARIADB_PUBLISH_USER:?missing}")"
app="$(marketpilot_sql_escape "${MARIADB_APP_USER:?missing}")"

mariadb --protocol=socket -uroot -p"${MARIADB_ROOT_PASSWORD}" <<SQL
GRANT SELECT ON marketpilot.dim_strategy TO '${publisher}'@'%';
GRANT SELECT, INSERT, UPDATE, DELETE ON marketpilot.fact_backtest_run TO '${publisher}'@'%';
GRANT SELECT, INSERT, UPDATE, DELETE ON marketpilot.fact_backtest_result TO '${publisher}'@'%';
GRANT SELECT, INSERT, UPDATE, DELETE ON marketpilot.fact_backtest_equity_daily TO '${publisher}'@'%';
GRANT SELECT ON marketpilot.dim_strategy TO '${app}'@'%';
GRANT SELECT ON marketpilot.fact_backtest_run TO '${app}'@'%';
GRANT SELECT ON marketpilot.fact_backtest_result TO '${app}'@'%';
GRANT SELECT ON marketpilot.fact_backtest_equity_daily TO '${app}'@'%';
FLUSH PRIVILEGES;
SQL

unset publisher app
unset -f marketpilot_sql_escape
