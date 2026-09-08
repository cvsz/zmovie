from __future__ import annotations

import os
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from zmovie_platform import backup, health, storage


class BackupAndHealthTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.db_path = self.root / "zmovie.db"
        self._old_storage_db = storage.DB_PATH
        self._old_backup_db = backup.DB_PATH
        self._old_health_db = health.DB_PATH
        storage.DB_PATH = self.db_path
        backup.DB_PATH = self.db_path
        health.DB_PATH = self.db_path
        storage.ensure_database()

    def tearDown(self) -> None:
        storage.DB_PATH = self._old_storage_db
        backup.DB_PATH = self._old_backup_db
        health.DB_PATH = self._old_health_db
        self.tmp.cleanup()

    def test_backup_includes_committed_wal_data_and_restores(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA wal_autocheckpoint=0")
            conn.execute("CREATE TABLE IF NOT EXISTS backup_probe(value TEXT NOT NULL)")
            conn.execute("INSERT INTO backup_probe(value) VALUES('before-backup')")
            conn.commit()

        target = backup.create_backup(self.root / "backups")
        self.assertTrue(target.is_file())
        with sqlite3.connect(target) as conn:
            self.assertEqual(conn.execute("SELECT value FROM backup_probe").fetchone()[0], "before-backup")
            self.assertEqual(conn.execute("PRAGMA quick_check").fetchone()[0], "ok")

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM backup_probe")
            conn.execute("INSERT INTO backup_probe(value) VALUES('after-backup')")
            conn.commit()
        backup.restore_backup(target)
        with sqlite3.connect(self.db_path) as conn:
            self.assertEqual(conn.execute("SELECT value FROM backup_probe").fetchone()[0], "before-backup")

    def test_health_reports_comfyui_not_configured_without_failing_service(self) -> None:
        media = self.root / "media"
        exports = self.root / "exports"
        publish = self.root / "publish"
        env = {
            "ZMOVIE_MEDIA_ROOT": str(media),
            "ZMOVIE_EXPORT_ROOT": str(exports),
            "ZMOVIE_PUBLISH_ROOT": str(publish),
            "ZMOVIE_COMFYUI_WORKFLOW": "",
        }
        with patch.dict(os.environ, env, clear=False), patch.object(
            health.COMFYUI,
            "_request_json",
            side_effect=RuntimeError("offline"),
        ):
            report = health.health_report()
        self.assertEqual(report["status"], "ok")
        self.assertFalse(report["comfyui"]["configured"])
        self.assertFalse(report["comfyui"]["reachable"])
        self.assertFalse(report["comfyui"]["ready"])
        self.assertEqual(report["comfyui"]["error"], "workflow_not_configured")

    def test_health_reports_reachable_even_before_workflow_configuration(self) -> None:
        env = {
            "ZMOVIE_MEDIA_ROOT": str(self.root / "media"),
            "ZMOVIE_EXPORT_ROOT": str(self.root / "exports"),
            "ZMOVIE_PUBLISH_ROOT": str(self.root / "publish"),
            "ZMOVIE_COMFYUI_WORKFLOW": "",
            "ZMOVIE_COMFYUI_URL": "http://127.0.0.1:8188",
        }
        stats = {
            "system": {
                "comfyui_version": "0.34.0",
                "python_version": "3.14.4",
                "pytorch_version": "2.14.0+cpu",
            },
            "devices": [{"name": "cpu", "type": "cpu"}],
        }
        with patch.dict(os.environ, env, clear=False), patch.object(
            health.COMFYUI,
            "_request_json",
            return_value=stats,
        ):
            report = health.health_report()
        comfy = report["comfyui"]
        self.assertFalse(comfy["configured"])
        self.assertTrue(comfy["reachable"])
        self.assertFalse(comfy["ready"])
        self.assertEqual(comfy["version"], "0.34.0")
        self.assertEqual(comfy["devices"], [{"name": "cpu", "type": "cpu"}])
        self.assertEqual(comfy["error"], "workflow_not_configured")

    def test_health_reports_reachable_configured_comfyui(self) -> None:
        workflow = self.root / "workflow_api.json"
        workflow.write_text('{"1":{"inputs":{}}}', encoding="utf-8")
        env = {
            "ZMOVIE_MEDIA_ROOT": str(self.root / "media"),
            "ZMOVIE_EXPORT_ROOT": str(self.root / "exports"),
            "ZMOVIE_PUBLISH_ROOT": str(self.root / "publish"),
            "ZMOVIE_COMFYUI_WORKFLOW": str(workflow),
            "ZMOVIE_COMFYUI_URL": "http://127.0.0.1:8188",
        }
        with patch.dict(os.environ, env, clear=False), patch.object(
            health.COMFYUI,
            "_request_json",
            return_value={"system": {}},
        ):
            report = health.health_report()
        self.assertTrue(report["comfyui"]["configured"])
        self.assertTrue(report["comfyui"]["reachable"])
        self.assertTrue(report["comfyui"]["ready"])


if __name__ == "__main__":
    unittest.main()
