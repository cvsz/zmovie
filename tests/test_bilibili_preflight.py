import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from zmovie_platform import storage
from zmovie_platform.publishers import bilibili, bilibili_preflight
from zmovie_platform.repository import add_asset, save_project
from zmovie_platform.storyboard import create_storyboard


class BilibiliPreflightTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.media = self.root / "media"
        self.publish = self.root / "publish"
        self.media.mkdir()
        self.publish.mkdir()
        self.old_db = storage.DB_PATH
        self.old_publish_root = bilibili.PUBLISH_ROOT
        storage.DB_PATH = self.root / "zmovie.db"
        bilibili.PUBLISH_ROOT = self.publish

    def tearDown(self):
        storage.DB_PATH = self.old_db
        bilibili.PUBLISH_ROOT = self.old_publish_root
        self.tmp.cleanup()

    def _approved_job(self, *, name="Real movie", concept="Production release"):
        project = create_storyboard(
            name=name,
            concept=concept,
            genre="cinematic",
            target_duration_seconds=20,
        )
        save_project(project)
        video = self.media / f"{project.id}.mp4"
        video.write_bytes(b"fake-video")
        add_asset(project.id, "final", "assembled movie", str(video))

        def fake_cover(_video, output):
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_bytes(b"fake-jpeg")
            return output.resolve()

        with mock.patch.object(bilibili, "_cover_from_video", side_effect=fake_cover):
            job = bilibili.prepare_bilibili_publish(project.id)
        return bilibili.approve_publish_job(job["id"])

    def _env(self):
        return {
            "ZMOVIE_MEDIA_ROOT": str(self.media),
            "ZMOVIE_PUBLISH_ROOT": str(self.publish),
        }

    def test_real_approved_job_passes_path_and_media_preflight(self):
        job = self._approved_job()
        probe = {
            "codec": "h264",
            "width": 1280,
            "height": 720,
            "frame_rate": "24/1",
            "duration_seconds": 10.0,
            "size_bytes": 1000,
        }
        with mock.patch.dict(os.environ, self._env(), clear=False), mock.patch.object(
            bilibili_preflight, "_probe_video", return_value=probe
        ):
            result = bilibili_preflight.preflight_publish_job(job["id"])
        self.assertTrue(result["ready"])
        self.assertEqual(result["status"], "approved")
        self.assertEqual(result["video"]["codec"], "h264")
        self.assertTrue(result["approval_recorded"])

    def test_smoke_project_is_rejected_by_default(self):
        job = self._approved_job(name="Production pipeline smoke", concept="mock integration test")
        with mock.patch.dict(os.environ, self._env(), clear=False):
            with self.assertRaisesRegex(RuntimeError, "looks non-production"):
                bilibili_preflight.preflight_publish_job(job["id"])

    def test_video_outside_media_root_is_rejected(self):
        project = create_storyboard(
            name="Real movie",
            concept="Production release",
            genre="cinematic",
            target_duration_seconds=20,
        )
        save_project(project)
        outside = self.root / "outside.mp4"
        outside.write_bytes(b"fake-video")
        add_asset(project.id, "final", "assembled movie", str(outside))

        def fake_cover(_video, output):
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_bytes(b"fake-jpeg")
            return output.resolve()

        with mock.patch.object(bilibili, "_cover_from_video", side_effect=fake_cover):
            job = bilibili.prepare_bilibili_publish(project.id)
        bilibili.approve_publish_job(job["id"])
        with mock.patch.dict(os.environ, self._env(), clear=False):
            with self.assertRaisesRegex(RuntimeError, "outside ZMOVIE_MEDIA_ROOT"):
                bilibili_preflight.preflight_publish_job(job["id"])


if __name__ == "__main__":
    unittest.main()
