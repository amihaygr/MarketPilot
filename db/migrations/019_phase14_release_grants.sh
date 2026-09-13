#!/usr/bin/env bash
set -euo pipefail

publisher="${MARIADB_PUBLISH_USER:?missing MARIADB_PUBLISH_USER}"
app="${MARIADB_APP_USER:?missing MARIADB_APP_USER}"

mariadb -uroot -p"${MARIADB_ROOT_PASSWORD}" <<SQL
GRANT SELECT, INSERT, UPDATE ON marketpilot.fact_corporate_action TO '${publisher}'@'%';
GRANT SELECT, INSERT, UPDATE ON marketpilot.fact_recommendation_evaluation TO '${publisher}'@'%';
GRANT SELECT, INSERT, UPDATE ON marketpilot.fact_decision_alert TO '${publisher}'@'%';
GRANT SELECT, INSERT, UPDATE ON marketpilot.shadow_mode_status TO '${publisher}'@'%';
GRANT SELECT ON marketpilot.fact_corporate_action TO '${app}'@'%';
GRANT SELECT ON marketpilot.fact_recommendation_evaluation TO '${app}'@'%';
GRANT SELECT ON marketpilot.fact_decision_alert TO '${app}'@'%';
GRANT SELECT ON marketpilot.shadow_mode_status TO '${app}'@'%';
FLUSH PRIVILEGES;
SQL
