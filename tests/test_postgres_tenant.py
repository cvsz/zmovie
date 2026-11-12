from __future__ import annotations

from zmovie_platform.postgres_tenant import provision_project_database, sanitize_db_name


def test_sanitize_db_name():
    assert sanitize_db_name("My Project 123") == "my_project_123"
    assert sanitize_db_name("123project") == "proj_123project"
    assert sanitize_db_name("test-db_name") == "test_db_name"

def test_provision_project_database_fallback():
    res = provision_project_database("Test Project", admin_dsn="postgresql://invalid:invalid@127.0.0.1:15432/postgres")
    assert res["database"] == "test_project"
    assert res["status"] == "fallback"
