"""Tests for the media pipeline (real ffmpeg evidence, synthetic media)."""
from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from zmovie_platform import auth, media_pipeline, migrations, storage


def _make_clip(path: Path, seconds: int = 2) -> None:
    proc = subprocess.run(
        ["ffmpeg", "-y", "-f", "lavfi", "-i", f"testsrc=size=320x240:rate=10:duration={seconds}",
         "-pix_fmt", "yuv420p", str(path)],
        capture_output=True, text=True, timeout=120, check=False)
    assert proc.returncode == 0 and path.exists(), proc.stderr[-500:]


class MediaPipelineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tmp = tempfile.TemporaryDirectory()
        cls.old_db = storage.DB_PATH
        storage.DB_PATH = Path(cls.tmp.name) / "zmovie.db"
        migrations.migrate()
        auth.create_user("uploader1", "uploader1-password-long", "user")
        cls.token = auth.issue_token({"username": "uploader1", "role": "user"})
        cls.work = Path(cls.tmp.name) / "work"
        cls.work.mkdir()
        _make_clip(cls.work / "clip.mp4")
        (cls.work / "note.txt").write_text("not a video")

    @classmethod
    def tearDownClass(cls) -> None:
        storage.DB_PATH = cls.old_db
        cls.tmp.cleanup()

    def test_validate_upload(self) -> None:
        ok = media_pipeline.validate_upload(
            project_id="prj1", filename="clip.mp4", size_bytes=100, content_type="video/mp4")
        self.assertEqual(ok, "clip.mp4")
        with self.assertRaises(ValueError):
            media_pipeline.validate_upload(
                project_id="prj1", filename="evil.exe", size_bytes=100, content_type="video/mp4")
        with self.assertRaises(ValueError):
            media_pipeline.validate_upload(
                project_id="prj1", filename="clip.mp4", size_bytes=10 ** 12, content_type="video/mp4")
        with self.assertRaises(ValueError):
            media_pipeline.validate_upload(
                project_id="prj1", filename="clip.mp4", size_bytes=100, content_type="text/html")
        # traversal filename is neutralized, project traversal rejected
        self.assertEqual(media_pipeline.validate_upload(
            project_id="prj1", filename="../../clip.mp4", size_bytes=100, content_type=""), "clip.mp4")

    def test_probe_gate_real_media(self) -> None:
        passed = media_pipeline.probe_gate(str(self.work / "clip.mp4"))
        self.assertTrue(passed["passed"], passed.get("reason", ""))
        self.assertGreaterEqual(passed["width"], 128)
        missing = media_pipeline.probe_gate(str(self.work / "absent.mp4"))
        self.assertFalse(missing["passed"])
        not_video = media_pipeline.probe_gate(str(self.work / "note.txt"))
        self.assertFalse(not_video["passed"])

    def test_transcode_and_poster_real(self) -> None:
        out = self.work / "clip.streaming.mp4"
        result = media_pipeline.transcode_to_streaming(str(self.work / "clip.mp4"), str(out))
        self.assertTrue(result["ok"] and out.exists())
        gated = media_pipeline.probe_gate(str(out))
        self.assertTrue(gated["passed"], gated.get("reason", ""))
        poster = self.work / "clip.poster.jpg"
        presult = media_pipeline.poster_frame(str(self.work / "clip.mp4"), str(poster))
        self.assertTrue(presult["ok"] and poster.exists())

    def test_upload_endpoint(self) -> None:
        import main

        client = TestClient(main.app)
        headers = {"Authorization": f"Bearer {self.token}"}
        # project owned by uploader1
        created = client.post("/api/v2/projects", headers=headers, json={
            "name": "upload-probe", "concept": "probe project for upload tests"})
        self.assertEqual(created.status_code, 200)
        pid = created.json()["project"]["id"]
        with open(self.work / "clip.mp4", "rb") as f:
            resp = client.post(f"/api/v2/projects/{pid}/uploads", headers=headers,
                              files={"file": ("clip.mp4", f, "video/mp4")})
        self.assertEqual(resp.status_code, 200)
        bad = client.post(f"/api/v2/projects/{pid}/uploads", headers=headers,
                          files={"file": ("evil.exe", b"MZ", "video/mp4")})
        self.assertEqual(bad.status_code, 400)
        anon = client.post(f"/api/v2/projects/{pid}/uploads",
                           files={"file": ("clip.mp4", b"0", "video/mp4")})
        self.assertEqual(anon.status_code, 401)
        client.delete(f"/api/v2/projects/{pid}", headers=headers)


if __name__ == "__main__":
    unittest.main()
