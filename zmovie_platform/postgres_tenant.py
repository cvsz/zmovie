from __future__ import annotations

import os
import re
from typing import Any


def sanitize_db_name(project_name: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9_]", "_", project_name.lower())
    if not cleaned or not cleaned[0].isalpha():
        cleaned = f"proj_{cleaned}"
    return cleaned[:63]


_DSN_SECRET_RE = re.compile(r"://([^:]+):([^@]+)@")


def _mask_dsn(dsn: str) -> str:
    """ซ่อนรหัสผ่านใน DSN ก่อนส่งกลับผลลัพธ์ (ไม่รั่วไหล credentials ต่อผู้เรียกใช้)."""
    return _DSN_SECRET_RE.sub(r"://\1:****@", dsn)


def provision_project_database(project_name: str, admin_dsn: str | None = None) -> dict[str, Any]:
    """จัดเตรียมฐานข้อมูลและ role สำหรับโครงการอย่างปลอดภัย (fail-closed).

    รหัสผ่านต้องอ่านจากไฟล์ลับรันไทม์เท่านั้น ห้ามสร้างรหัสผ่าน fallback แบบคาดเดาได้
    และห้ามใช้ admin credentials แบบ hard-coded เมื่อไม่ระบุ DSN ผู้ดูแลระบบ.
    """
    db_name = sanitize_db_name(project_name)
    username = f"user_{db_name}"

    password_file = os.getenv("REPONAME_POSTGRES_PASSWORD_FILE", "/run/secrets/zmovie_postgres_password")
    try:
        with open(password_file, encoding="utf-8") as fh:
            password = fh.read().strip()
    except (OSError, FileNotFoundError) as exc:
        raise RuntimeError(
            f"PostgreSQL password file {password_file} must exist before provisioning database {db_name}"
        ) from exc
    if not password:
        raise RuntimeError(f"PostgreSQL password file {password_file} is empty")

    resolved_dsn = admin_dsn or os.getenv("ZMOVIE_PG_ADMIN_DSN")
    if not resolved_dsn:
        raise RuntimeError(
            "PostgreSQL admin DSN is required (pass admin_dsn or set ZMOVIE_PG_ADMIN_DSN); "
            "refusing to fall back to predictable credentials"
        )

    try:
        import psycopg
        from psycopg.errors import DuplicateDatabase, DuplicateObject

        conn = psycopg.connect(resolved_dsn, autocommit=True)
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
            "dsn": _mask_dsn(resolved_dsn),
        }
