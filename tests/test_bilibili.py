import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

from zmovie_platform import storage
from zmovie_platform.publishers import bilibili
from zmovie_platform.repository import add_asset, save_project
from zmovie_platform.storyboard import create_storyboard


class BilibiliPublisherTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.old_db = storage.DB_PATH
        self.old_publish_root = bilibili.PUBLISH_ROOT
        storage.DB_PATH = self.root / "zmovie.db"
        bilibili.PUBLISH_ROOT = self.root / "publish"
        self.project = create_storyboard(
            name="A" * 120,
            concept="A cinematic AI movie created for an automated publishing test.",
            genre="action",
            target_duration_seconds=20,
        )
        save_project(self.project)
        self.video = self.root / "final.mp4"
        self.video.write_bytes(b"fake-video")
        add_asset(self.project.id, "final", "assembled movie", str(self.video))

    def tearDown(self):
        storage.DB_PATH = self.old_db
        bilibili.PUBLISH_ROOT = self.old_publish_root
        self.tmp.cleanup()

    @staticmethod
    def _fake_cover(video: Path, output: Path) -> Path:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(b"fake-jpeg")
        return output.resolve()

    def test_prepare_enforces_creator_center_metadata_limits(self):
        with mock.patch.object(bilibili, "_cover_from_video", side_effect=self._fake_cover):
            job = bilibili.prepare_bilibili_publish(
                self.project.id,
                tags=[f"tag-{i}" for i in range(20)],
            )
        self.assertEqual(job["status"], "prepared")
        self.assertLessEqual(len(job["title"]), 100)
        self.assertLessEqual(len(job["description"]), 2000)
        self.assertLessEqual(len(job["tags"]), 10)
        self.assertTrue(Path(job["cover_path"]).is_file())
        self.assertIn("AI-generated", job["description"])

    def test_approval_gate_blocks_publish_until_approved(self):
        with mock.patch.object(bilibili, "_cover_from_video", side_effect=self._fake_cover):
            job = bilibili.prepare_bilibili_publish(self.project.id)
        with self.assertRaises(ValueError):
            bilibili.publish_bilibili_job(job["id"])

        approved = bilibili.approve_publish_job(job["id"])
        self.assertEqual(approved["status"], "approved")
        with mock.patch.object(
            bilibili,
            "_automate_publish",
            return_value={"status": "published", "published_url": "https://www.bilibili.tv/video/example", "metadata": {"submitted_at": "now"}},
        ):
            published = bilibili.publish_bilibili_job(job["id"])
        self.assertEqual(published["status"], "published")
        self.assertIn("bilibili.tv", published["published_url"])

    def test_schedule_window_matches_creator_center_constraints(self):
        fixed = datetime(2026, 9, 8, 12, 0, tzinfo=timezone.utc)
        with mock.patch.object(bilibili, "_now", return_value=fixed):
            accepted = bilibili._validate_schedule((fixed + timedelta(hours=3)).isoformat())
            self.assertTrue(accepted)
            with self.assertRaises(ValueError):
                bilibili._validate_schedule((fixed + timedelta(hours=1)).isoformat())
            with self.assertRaises(ValueError):
                bilibili._validate_schedule((fixed + timedelta(days=16)).isoformat())


if __name__ == "__main__":
    unittest.main()
