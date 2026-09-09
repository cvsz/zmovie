from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import app


class AppTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        app.DATA_DIR = Path(self.tmp.name)
        app.DB_PATH = app.DATA_DIR / "zmovie.db"
        app.init_db()

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_health(self) -> None:
        payload = app.health()
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["service"], "zmovie")

    def test_api_docs_are_disabled_by_default(self) -> None:
        self.assertIsNone(app.app.docs_url)
        self.assertIsNone(app.app.redoc_url)
        self.assertIsNone(app.app.openapi_url)

    def test_generate_is_deterministic_with_seed(self) -> None:
        request = app.GenerateRequest(count=1, seed=42, save_history=False)
        first = app.generate(request)
        second = app.generate(request)
        self.assertEqual(first["results"][0]["main_prompt"], second["results"][0]["main_prompt"])

    def test_generate_saves_history(self) -> None:
        request = app.GenerateRequest(count=1, seed=7, save_history=True)
        generated = app.generate(request)
        self.assertIn("history_id", generated["results"][0])

        history = app.history(limit=20)
        self.assertEqual(history["count"], 1)
        self.assertEqual(history["items"][0]["seed"], 7)


if __name__ == "__main__":
    unittest.main()
