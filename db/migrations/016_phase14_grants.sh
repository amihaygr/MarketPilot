#!/usr/bin/env bash
set -euo pipefail
esc() { printf '%s' "${1//\'/\'\'}"; }
publisher="$(esc "${MARIADB_PUBLISH_USER:?missing}")"
app="$(esc "${MARIADB_APP_USER:?missing}")"
sec="$(esc "${MARIADB_SEC_USER:?missing}")"
mariadb --protocol=socket -uroot -p"${MARIADB_ROOT_PASSWORD}" <<SQL
GRANT SELECT, INSERT, UPDATE, DELETE ON marketpilot.fact_opportunity_recommendation TO '${publisher}'@'%';
GRANT SELECT, INSERT, UPDATE, DELETE ON marketpilot.fact_fundamental_metric TO '${publisher}'@'%';
GRANT SELECT ON marketpilot.user_portfolio TO '${publisher}'@'%';
GRANT SELECT ON marketpilot.user_position TO '${publisher}'@'%';
GRANT SELECT ON marketpilot.user_watchlist_symbol TO '${publisher}'@'%';
GRANT SELECT, INSERT, UPDATE ON marketpilot.fact_fundamental_metric TO '${sec}'@'%';
GRANT SELECT ON marketpilot.fact_opportunity_recommendation TO '${app}'@'%';
GRANT SELECT ON marketpilot.fact_fundamental_metric TO '${app}'@'%';
FLUSH PRIVILEGES;
SQL
