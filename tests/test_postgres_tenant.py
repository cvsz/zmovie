from __future__ import annotations

import os
import tempfile
from pathlib import Path
from unittest import mock

from zmovie_platform.postgres_tenant import provision_project_database, sanitize_db_name


def test_sanitize_db_name():
    assert sanitize_db_name("My Project 123") == "my_project_123"
    assert sanitize_db_name("123project") == "proj_123project"
    assert sanitize_db_name("test-db_name") == "test_db_name"


def test_provision_project_database_missing_secret_file_raises():
    # รหัสผ่านต้องอ่านจากไฟล์ลับรันไทม์เท่านั้น ห้ามสร้าง fallback แบบคาดเดาได้
    with tempfile.TemporaryDirectory() as tmp:
        missing = Path(tmp) / "does_not_exist_postgres_password"
        with mock.patch.dict(
            os.environ, {"REPONAME_POSTGRES_PASSWORD_FILE": str(missing)}, clear=False
        ):
            try:
                provision_project_database(
                    "Test Project", admin_dsn="postgresql://invalid:invalid@127.0.0.1:15432/postgres"
                )
            except RuntimeError:
                pass
            else:
                raise AssertionError("คาดหวัง RuntimeError เมื่อไฟล์รหัสลับ PostgreSQL หายไป")


def test_provision_project_database_empty_secret_file_raises():
    # ไฟล์รหัสลับที่ว่างเปล่าต้องถูกปฏิเสธเช่นกัน
    with tempfile.TemporaryDirectory() as tmp:
        empty = Path(tmp) / "empty_postgres_password"
        empty.write_text("", encoding="utf-8")
        with mock.patch.dict(
            os.environ, {"REPONAME_POSTGRES_PASSWORD_FILE": str(empty)}, clear=False
        ):
            try:
                provision_project_database(
                    "Test Project", admin_dsn="postgresql://invalid:invalid@127.0.0.1:15432/postgres"
                )
            except RuntimeError:
                pass
            else:
                raise AssertionError("คาดหวัง RuntimeError เมื่อไฟล์รหัสลับว่างเปล่า")


def test_provision_project_database_no_admin_dsn_raises():
    # ห้ามใช้ admin credentials แบบ hard-coded เมื่อไม่ระบุ DSN ผู้ดูแลระบบ
    with tempfile.TemporaryDirectory() as tmp:
        pw_file = Path(tmp) / "zmovie_postgres_password"
        pw_file.write_text("real-provisioning-password-12345", encoding="utf-8")
        with mock.patch.dict(
            os.environ,
            {
                "REPONAME_POSTGRES_PASSWORD_FILE": str(pw_file),
                "ZMOVIE_PG_ADMIN_DSN": "",
            },
            clear=False,
        ):
            try:
                provision_project_database("Test Project")
            except RuntimeError:
                pass
            else:
                raise AssertionError("คาดหวัง RuntimeError เมื่อไม่ระบุ admin DSN")


def test_provision_project_database_fallback_no_credential_leak():
    # เมื่อฐานข้อมูลเชื่อมต่อล้มเหลว ต้องคืน fallback โดยไม่รั่วไหลรหัสผ่าน admin 真实 credentials
    with tempfile.TemporaryDirectory() as tmp:
        pw_file = Path(tmp) / "zmovie_postgres_password"
        pw_file.write_text("real-provisioning-password-12345", encoding="utf-8")
        with mock.patch.dict(
            os.environ, {"REPONAME_POSTGRES_PASSWORD_FILE": str(pw_file)}, clear=False
        ):
            res = provision_project_database(
                "Test Project", admin_dsn="postgresql://invalid:invalid@127.0.0.1:15432/postgres"
            )
            assert res["database"] == "test_project"
            assert res["status"] == "fallback"
            # dsn ที่ส่งกลับต้องไม่บรรจุ postgres:postgres (credentials จริงของระบบ)
            dsn = str(res.get("dsn", ""))
            assert "postgres:postgres" not in dsn, "ไม่ควรรั่วไหล credentials postgres:postgres"
            # ควรมีการป้องกันการรั่วไหล (masked หรือค่าอื่น)