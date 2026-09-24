"""Tests for Studio-to-Cinema integration boundary (no auto-publish)."""
from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from zmovie_platform import migrations, storage, studio_cinema


class StudioCinemaTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.old_db = storage.DB_PATH
        self.old_media = os.environ.get("ZMOVIE_MEDIA_ROOT")
        self.old_token = os.environ.get("ZMOVIE_CINEMA_SERVICE_TOKEN")
        storage.DB_PATH = self.root / "zmovie.db"
        os.environ["ZMOVIE_MEDIA_ROOT"] = str(self.root / "media")
        os.environ["ZMOVIE_EXPORT_ROOT"] = str(self.root / "exports")
        os.environ["ZMOVIE_PUBLISH_ROOT"] = str(self.root / "publish")
        os.environ["ZMOVIE_OBJECT_ROOT"] = str(self.root / "objects")
        os.environ["ZMOVIE_CINEMA_SERVICE_TOKEN"] = "test-service-token"
        migrations.migrate()
        studio_cinema.ensure_tables()
        media_root = Path(os.environ["ZMOVIE_MEDIA_ROOT"])
        media_root.mkdir(parents=True, exist_ok=True)
        self.media = media_root / "final.mp4"
        self.media.write_bytes(b"\x00" * 1024)

    def tearDown(self) -> None:
        storage.DB_PATH = self.old_db
        if self.old_media is None:
            os.environ.pop("ZMOVIE_MEDIA_ROOT", None)
        else:
            os.environ["ZMOVIE_MEDIA_ROOT"] = self.old_media
        for name in ("ZMOVIE_EXPORT_ROOT", "ZMOVIE_PUBLISH_ROOT", "ZMOVIE_OBJECT_ROOT"):
            os.environ.pop(name, None)
        if self.old_token is None:
            os.environ.pop("ZMOVIE_CINEMA_SERVICE_TOKEN", None)
        else:
            os.environ["ZMOVIE_CINEMA_SERVICE_TOKEN"] = self.old_token
        self.tmp.cleanup()

    def test_request_never_auto_publishes(self) -> None:
        record = studio_cinema.request_import(
            project_id="prj-1", production_run_id="run-1", media_path=str(self.media),
            idempotency_key="idem-key-001", actor="tester",
        )
        self.assertNotEqual(record["status"], "published")
        self.assertIn(record["status"], {"qc_passed"})

    def test_duplicate_idempotency_returns_same_record(self) -> None:
        first = studio_cinema.request_import(
            project_id="prj-1", production_run_id="run-1", media_path=str(self.media),
            idempotency_key="idem-dup-002", actor="tester",
        )
        second = studio_cinema.request_import(
            project_id="prj-1", production_run_id="run-1", media_path=str(self.media),
            idempotency_key="idem-dup-002", actor="tester",
        )
        self.assertEqual(first["id"], second["id"])
        self.assertEqual(len(studio_cinema.list_imports(project_id="prj-1")), 1)

    def test_missing_media_rejected(self) -> None:
        with self.assertRaises(ValueError):
            studio_cinema.request_import(
                project_id="prj-1", production_run_id="run-1",
                media_path=str(self.root / "media" / "missing.mp4"),
                idempotency_key="idem-miss-003", actor="tester",
            )

    def test_failed_transcoding_recorded(self) -> None:
        record = studio_cinema.request_import(
            project_id="prj-1", production_run_id="run-1", media_path=str(self.media),
            idempotency_key="idem-fail-004", actor="tester",
        )
        studio_cinema.confirm_rights(
            import_id=record["id"], actor="tester",
            confirmation={"owner_verified": True, "rights_holder": "Studio", "license_expires": "2030-01-01", "age_rating": "13+"},
        )
        studio_cinema.approve_import(import_id=record["id"], actor="admin", decision="approved")

        def bad_transcode(_: str) -> dict:
            return {"ok": False, "error": "ffmpeg exploded"}

        failed = studio_cinema.run_import(import_id=record["id"], actor="svc", transcode_hook=bad_transcode)
        self.assertEqual(failed["status"], "transcode_failed")
        self.assertIn("ffmpeg", failed["last_error"])

    def test_rejected_publication_never_publishes(self) -> None:
        record = studio_cinema.request_import(
            project_id="prj-1", production_run_id="run-1", media_path=str(self.media),
            idempotency_key="idem-rej-005", actor="tester",
        )
        studio_cinema.confirm_rights(
            import_id=record["id"], actor="tester",
            confirmation={"owner_verified": True, "rights_holder": "Studio", "license_expires": "2030-01-01", "age_rating": "13+"},
        )
        decided = studio_cinema.approve_import(import_id=record["id"], actor="admin", decision="rejected", reason="rights unclear")
        self.assertEqual(decided["status"], "rejected")
        with self.assertRaises(ValueError):
            studio_cinema.run_import(import_id=record["id"], actor="svc")

    def test_full_happy_path_requires_all_gates(self) -> None:
        record = studio_cinema.request_import(
            project_id="prj-1", production_run_id="run-1", media_path=str(self.media),
            idempotency_key="idem-happy-006", actor="tester",
        )
        studio_cinema.confirm_rights(
            import_id=record["id"], actor="tester",
            confirmation={"owner_verified": True, "rights_holder": "Studio", "license_expires": "2030-01-01", "age_rating": "13+"},
        )
        studio_cinema.approve_import(import_id=record["id"], actor="admin", decision="approved")
        running = studio_cinema.run_import(
            import_id=record["id"], actor="svc",
            transcode_hook=lambda _: {"ok": True}, poster_hook=lambda _: {"ok": True},
        )
        self.assertEqual(running["status"], "editorial_review")
        published = studio_cinema.editorial_decide(
            import_id=record["id"], actor="editor", publish=True, cinema_film_ref="film-123", note="ok"
        )
        self.assertEqual(published["status"], "published")

    def test_service_token_fail_closed(self) -> None:
        self.assertTrue(studio_cinema.verify_service_token("test-service-token"))
        self.assertFalse(studio_cinema.verify_service_token("wrong"))
        self.assertFalse(studio_cinema.verify_service_token(None))
        os.environ["ZMOVIE_CINEMA_SERVICE_TOKEN"] = ""
        self.assertFalse(studio_cinema.verify_service_token("test-service-token"))


if __name__ == "__main__":
    unittest.main()
