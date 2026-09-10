from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from zmovie_platform import runtime_ops, storage


class RuntimeOpsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.original_db = storage.DB_PATH
        self.original_ops_db = runtime_ops.DB_PATH
        self.original_backup = runtime_ops.BACKUP_ROOT
        self.original_data = runtime_ops.DATA_ROOT
        storage.DB_PATH = root / "zmovie.db"
        runtime_ops.DB_PATH = storage.DB_PATH
        runtime_ops.BACKUP_ROOT = root / "backups"
        runtime_ops.DATA_ROOT = root
        storage.ensure_database()

    def tearDown(self) -> None:
        storage.DB_PATH = self.original_db
        runtime_ops.DB_PATH = self.original_ops_db
        runtime_ops.BACKUP_ROOT = self.original_backup
        runtime_ops.DATA_ROOT = self.original_data
        self.tmp.cleanup()

    def test_backup_is_verified_and_listed(self) -> None:
        result = runtime_ops.backup_database()
        self.assertEqual(result["status"], "completed")
        self.assertGreater(result["size_bytes"], 0)
        listing = runtime_ops.backups()
        self.assertEqual(listing["count"], 1)
        status = runtime_ops.backup_status()
        self.assertTrue(status["database_exists"])
        self.assertEqual(status["backup_count"], 1)

    def test_watchdog_does_not_require_renderer_model(self) -> None:
        report = runtime_ops.watchdog_run()
        self.assertIn("database_ok", report["status"])
        self.assertTrue(report["status"]["database_ok"])
        self.assertNotIn("renderer_unready", report["actions"])

    def test_upgrade_readiness_blocks_active_job(self) -> None:
        from zmovie_platform.worker_queue import enqueue

        enqueue("production_render", project_id="prj_test")
        report = runtime_ops.upgrade_readiness()
        self.assertTrue(report["safe"], "queued work is safe to preserve across upgrade; only active leases block")


if __name__ == "__main__":
    unittest.main()
