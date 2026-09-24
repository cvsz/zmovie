"""Tests for liveness/readiness probes."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from zmovie_platform import api_routes, migrations, storage


class OpsProbeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.old_db = storage.DB_PATH
        storage.DB_PATH = Path(self.tmp.name) / "zmovie.db"

    def tearDown(self) -> None:
        storage.DB_PATH = self.old_db
        self.tmp.cleanup()

    def test_livez_needs_no_db(self) -> None:
        self.assertEqual(api_routes.livez(), {"status": "alive"})

    def test_readyz_migrates_and_reports(self) -> None:
        result = api_routes.readyz()
        self.assertEqual(result["status"], "ready")
        self.assertIn("users", result)
        migrations.migrate()
        again = api_routes.readyz()
        self.assertEqual(again["status"], "ready")


if __name__ == "__main__":
    unittest.main()
