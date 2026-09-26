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

from zmovie_platform import migrations, storage

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
        subprocess.run(["pg_restore", "--dbname", PG_DSN, str(dump)], check=True, timeout=120)
        with psycopg.connect(PG_DSN) as conn:
            row = conn.execute("SELECT v FROM p3_dump_test WHERE id='a'").fetchone()
            self.assertEqual(row[0], "1")
            with conn.cursor() as cur:
                cur.execute("DROP TABLE p3_dump_test")
                conn.commit()


if __name__ == "__main__":
    unittest.main()
