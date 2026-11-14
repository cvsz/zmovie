"""PostgreSQL readiness: versioned ledger, PG-gated concurrency/backup tests.

SQLite remains the default backend. PostgreSQL tests run only when
ZMOVIE_PG_DSN is set (isolated PG environment); otherwise they skip.
Never invent credentials: without a DSN the PG path is reported BLOCKED.
"""
from __future__ import annotations

import os
import shutil
import sqlite3
import subprocess
import tempfile
import threading
import unittest
from pathlib import Path
from unittest import mock

from zmovie_platform import migrations, storage
from zmovie_platform.config import Settings, validate_database_settings

PG_DSN = os.getenv("ZMOVIE_PG_DSN", "")


class MigrationLedgerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.old_db = storage.DB_PATH
        storage.DB_PATH = Path(self.tmp.name) / "zmovie.db"

    def tearDown(self) -> None:
        storage.DB_PATH = self.old_db
        self.tmp.cleanup()

    def test_migrate_is_idempotent_and_ledgered(self) -> None:
        migrations.migrate()
        first = migrations.applied_versions()
        self.assertEqual(first, sorted(migrations.MIGRATION_VERSIONS))
        migrations.migrate()
        self.assertEqual(migrations.applied_versions(), first)

    def test_rollback_via_backup_restore(self) -> None:
        """Rollback contract: pre-migration backup restores the prior state."""
        db = Path(self.tmp.name) / "zmovie.db"
        migrations.migrate()
        backup = Path(self.tmp.name) / "pre-migration.db"
        shutil.copyfile(db, backup)
        with storage.connect() as conn:
            conn.execute("INSERT INTO projects(id,owner,name,concept,genre,visual_style,aspect_ratio,"
                         "target_duration_seconds,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?)",
                         ("prj-x", "u", "n", "c", "g", "v", "16:9", 60, "t", "t"))
        with sqlite3.connect(backup) as src, sqlite3.connect(db) as dst:
            src.backup(dst)
        with storage.connect() as conn:
            row = conn.execute("SELECT * FROM projects WHERE id='prj-x'").fetchone()
            self.assertIsNone(row)
            self.assertEqual(len(migrations.applied_versions()), len(migrations.MIGRATION_VERSIONS))


@unittest.skipUnless(PG_DSN, "ZMOVIE_PG_DSN not set: isolated PostgreSQL unavailable")
class PostgresReadinessTests(unittest.TestCase):
    def test_pg_version_and_booking_concurrency(self) -> None:
        import psycopg

        with psycopg.connect(PG_DSN, autocommit=True) as conn:
            version = conn.execute("SELECT version()").fetchone()[0]
            self.assertIn("PostgreSQL", version)
            conn.execute("DROP TABLE IF EXISTS p3_seat_test")
            conn.execute("CREATE TABLE p3_seat_test(showtime_id TEXT NOT NULL, seat_no TEXT NOT NULL,"
                         " holder TEXT NOT NULL, PRIMARY KEY (showtime_id, seat_no))")
            wins: list[str] = []
            lock = threading.Lock()

            def attempt(n: int) -> None:
                try:
                    with psycopg.connect(PG_DSN) as c:
                        c.execute("INSERT INTO p3_seat_test VALUES('st-1','A01',%s)", (f"u{n}",))
                        c.commit()
                    with lock:
                        wins.append(f"u{n}")
                except Exception:  # noqa: BLE001 - constraint violations are the expected outcome
                    with lock:
                        pass

            threads = [threading.Thread(target=attempt, args=(n,)) for n in range(6)]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join()
            self.assertEqual(len(wins), 1)
            conn.execute("DROP TABLE p3_seat_test")

    def test_pg_dump_restore_roundtrip(self) -> None:
        if not shutil.which("pg_dump") or not shutil.which("pg_restore"):
            self.skipTest("pg_dump/pg_restore unavailable")
        import psycopg

        with psycopg.connect(PG_DSN, autocommit=True) as conn:
            conn.execute("DROP TABLE IF EXISTS p3_dump_test")
            conn.execute("CREATE TABLE p3_dump_test(id TEXT PRIMARY KEY, v TEXT NOT NULL)")
            conn.execute("INSERT INTO p3_dump_test VALUES('a','1')")
        dump = Path(tempfile.mkdtemp()) / "p3.dump"
        subprocess.run(["pg_dump", "--dbname", PG_DSN, "--format", "custom", "--table", "p3_dump_test",
                        "--file", str(dump)], check=True, timeout=120)
        self.assertTrue(dump.exists() and dump.stat().st_size > 0)
        with psycopg.connect(PG_DSN, autocommit=True) as conn:
            conn.execute("DROP TABLE p3_dump_test")
        try:
            subprocess.run(["pg_restore", "--dbname", PG_DSN, str(dump)], check=True, timeout=120)
        except subprocess.CalledProcessError:
            # Handle cross-version transaction_timeout warning error gracefully if data successfully restored
            pass
        with psycopg.connect(PG_DSN) as conn:
            row = conn.execute("SELECT v FROM p3_dump_test WHERE id='a'").fetchone()
            self.assertEqual(row[0], "1")
            with conn.cursor() as cur:
                cur.execute("DROP TABLE p3_dump_test")
                conn.commit()


class ConfigDatabaseSettingsTestCase(unittest.TestCase):
    """การตั้งค่าฐานข้อมูลและแคชระดับองค์กร (ขั้นตอน 2.4).

    repo-name = zmovie; user 'zmovie', ฐานข้อมูล zmovie_db, host zpostgressql:5432,
    เรดิส zredis:6379, รหัสผ่านอ่านจากไฟล์ลับ /run/secrets/...
    """

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.pg_file = Path(self.tmp.name) / "zmovie_postgres_password"
        self.redis_file = Path(self.tmp.name) / "zmovie_zredis_password"
        self._env_patch = mock.patch.dict(
            os.environ,
            {
                "REPONAME_POSTGRES_HOST": "zpostgressql",
                "REPONAME_POSTGRES_PORT": "5432",
                "REPONAME_POSTGRES_USER": "zmovie",
                "REPONAME_POSTGRES_DB": "zmovie_db",
                "REPONAME_POSTGRES_PASSWORD_FILE": str(self.pg_file),
                "REPONAME_REDIS_HOST": "zredis",
                "REPONAME_REDIS_PORT": "6379",
                "REPONAME_REDIS_PASSWORD_FILE": str(self.redis_file),
            },
            clear=False,
        )
        self._env_patch.start()

    def tearDown(self) -> None:
        self._env_patch.stop()
        self.tmp.cleanup()

    def test_read_secret_file_reads_existing_file(self) -> None:
        self.pg_file.write_text("  pg-secret-123  \n", encoding="utf-8")
        settings = Settings()
        self.assertEqual(settings.db_password, "pg-secret-123")

    def test_read_secret_file_returns_empty_when_missing(self) -> None:
        settings = Settings()
        self.assertEqual(settings.db_password, "")
        self.assertEqual(settings.redis_password, "")

    def test_database_dsn_builds_from_settings(self) -> None:
        self.pg_file.write_text("pg-secret-123", encoding="utf-8")
        settings = Settings()
        self.assertEqual(
            settings.database_dsn,
            "postgresql://zmovie:pg-secret-123@zpostgressql:5432/zmovie_db",
        )

    def test_database_dsn_uses_defaults_when_env_absent(self) -> None:
        self._env_patch.stop()
        try:
            for key in (
                "REPONAME_POSTGRES_HOST",
                "REPONAME_POSTGRES_PORT",
                "REPONAME_POSTGRES_USER",
                "REPONAME_POSTGRES_DB",
                "REPONAME_POSTGRES_PASSWORD_FILE",
                "REPONAME_REDIS_HOST",
                "REPONAME_REDIS_PORT",
                "REPONAME_REDIS_PASSWORD_FILE",
            ):
                os.environ.pop(key, None)
            settings = Settings()
            self.assertEqual(settings.db_host, "zpostgressql")
            self.assertEqual(settings.db_port, 5432)
            self.assertEqual(settings.db_user, "zmovie")
            self.assertEqual(settings.db_name, "zmovie_db")
            self.assertEqual(settings.redis_host, "zredis")
            self.assertEqual(settings.redis_port, 6379)
        finally:
            self._env_patch.start()

    def test_redis_url_without_password(self) -> None:
        settings = Settings()
        self.assertEqual(settings.redis_url, "redis://zredis:6379/0")

    def test_redis_url_with_password(self) -> None:
        self.redis_file.write_text("redis-secret-456", encoding="utf-8")
        settings = Settings()
        self.assertEqual(
            settings.redis_url, "redis://:redis-secret-456@zredis:6379/0"
        )

    def test_validate_database_settings_passes_on_loopback(self) -> None:
        # localhost ไม่ต้องมีไฟล์รหัสลับ (สภาพแวดล้อมพัฒนาใช้ SQLite)
        validate_database_settings(Settings(db_host="localhost"))

    def test_validate_database_settings_raises_on_missing_remote_password_file(self) -> None:
        # โฮสต์ระยะไกลแต่ไฟล์รหัสลับไม่มีต้องปฏิเสธการเริ่มระบบ
        with self.assertRaises(RuntimeError):
            validate_database_settings(Settings())


if __name__ == "__main__":
    unittest.main()
