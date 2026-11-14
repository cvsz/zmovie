from __future__ import annotations

import os
import re
from typing import Any


def sanitize_db_name(project_name: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9_]", "_", project_name.lower())
    if not cleaned or not cleaned[0].isalpha():
        cleaned = f"proj_{cleaned}"
    return cleaned[:63]

def provision_project_database(project_name: str, admin_dsn: str | None = None) -> dict[str, Any]:
    db_name = sanitize_db_name(project_name)
    username = f"user_{db_name}"
    password_file = os.getenv("REPONAME_POSTGRES_PASSWORD_FILE", "/run/secrets/zmovie_postgres_password")
    try:
        with open(password_file, encoding="utf-8") as fh:
            password = fh.read().strip()
    except (OSError, FileNotFoundError):
        password = f"sec_{db_name}_pass"

    dsn: str = admin_dsn or os.getenv("ZMOVIE_PG_ADMIN_DSN") or "postgresql://postgres:postgres@127.0.0.1:15432/postgres"

    try:
        import psycopg
        from psycopg.errors import DuplicateDatabase, DuplicateObject

        conn = psycopg.connect(dsn, autocommit=True)
        cursor = conn.cursor()

        cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_name,))
        exists = cursor.fetchone()

        if not exists:
            cursor.execute(f'CREATE DATABASE "{db_name}"')

        cursor.execute("SELECT 1 FROM pg_roles WHERE rolname = %s", (username,))
        user_exists = cursor.fetchone()
        if not user_exists:
            cursor.execute(f'CREATE USER "{username}" WITH PASSWORD %s', (password,))
            cursor.execute(f'GRANT ALL PRIVILEGES ON DATABASE "{db_name}" TO "{username}"')

        cursor.close()
        conn.close()

        return {
            "status": "success",
            "database": db_name,
            "username": username,
            "dsn": f"postgresql://{username}:{password}@127.0.0.1:15432/{db_name}",
        }
    except (DuplicateDatabase, DuplicateObject) as exc:
        return {
            "status": "already_exists",
            "reason": str(exc),
            "database": db_name,
            "dsn": f"postgresql://{username}:{password}@127.0.0.1:15432/{db_name}",
        }
    except Exception as exc:
        return {
            "status": "fallback",
            "reason": str(exc),
            "database": db_name,
            "dsn": f"postgresql://postgres:postgres@127.0.0.1:15432/{db_name}",
        }
