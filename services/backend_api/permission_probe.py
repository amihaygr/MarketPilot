"""Verify that the configured Backend API identity can read but cannot mutate Gold."""

from __future__ import annotations

import json

import pymysql

from marketpilot.serving.repository import MariaDbReadRepository
from marketpilot.serving.settings import ServingSettings


def main() -> None:
    settings = ServingSettings.from_environ()
    repository = MariaDbReadRepository(settings)
    read_allowed = repository.ready()
    write_denied = False
    connection = pymysql.connect(
        host=settings.mariadb_host,
        port=settings.mariadb_port,
        database=settings.mariadb_database,
        user=settings.mariadb_user,
        password=settings.mariadb_password,
        autocommit=False,
        connect_timeout=settings.query_timeout_seconds,
    )
    try:
        with connection.cursor() as cursor:
            try:
                cursor.execute("UPDATE dim_symbol SET display_name = display_name WHERE 1 = 0")
            except pymysql.MySQLError as error:
                write_denied = bool(error.args and error.args[0] in {1142, 1143})
            else:
                connection.rollback()
    finally:
        connection.close()
    print(json.dumps({"read_allowed": read_allowed, "write_denied": write_denied}))
    if not read_allowed or not write_denied:
        raise SystemExit("Backend API privilege boundary check failed")


if __name__ == "__main__":
    main()
