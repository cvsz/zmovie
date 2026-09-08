import tempfile
import unittest
from pathlib import Path
from unittest import mock

from zmovie_platform import storage
from zmovie_platform.publishers import bilibili
from zmovie_platform.publishers import bilibili_hardened as hardened
from zmovie_platform.repository import add_asset, save_project
from zmovie_platform.storyboard import create_storyboard


class _HiddenFileInput:
    def __init__(self):
        self.files = []

    def count(self):
        return 1

    @property
    def first(self):
        return self

    def is_visible(self):
        return False

    def set_input_files(self, path):
        self.files.append(path)


class _Page:
    def __init__(self, locator):
        self._locator = locator

    def locator(self, _selector):
        return self._locator


class BilibiliHardeningTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.old_db = storage.DB_PATH
        self.old_publish_root = bilibili.PUBLISH_ROOT
        storage.DB_PATH = self.root / "zmovie.db"
        bilibili.PUBLISH_ROOT = self.root / "publish"
        self.project = create_storyboard(
            name="Hardened publisher test",
            concept="A controlled publication workflow test.",
            genre="cinematic",
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

    def _approved_job(self):
        with mock.patch.object(bilibili, "_cover_from_video", side_effect=self._fake_cover):
            job = hardened.prepare_bilibili_publish(self.project.id)
        return hardened.approve_publish_job(job["id"])

    def test_hidden_video_input_is_supported(self):
        hidden = _HiddenFileInput()
        hardened._set_video(_Page(hidden), "/tmp/video.mp4")
        self.assertEqual(hidden.files, ["/tmp/video.mp4"])

    def test_missing_session_is_not_authenticated(self):
        status = hardened.session_status(self.root / "missing-state.json")
        self.assertFalse(status["configured"])
        self.assertFalse(status["authenticated"])
        self.assertFalse(status["checked"])

    def test_headless_login_fails_before_browser_launch(self):
        with mock.patch.dict("os.environ", {"DISPLAY": "", "WAYLAND_DISPLAY": ""}, clear=False):
            with self.assertRaisesRegex(RuntimeError, "requires a visible GUI display"):
                hardened._require_interactive_display()

    def test_successful_submit_without_public_url_stays_submitted(self):
        job = self._approved_job()
        fake = {
            "status": "published",
            "published_url": "",
            "metadata": {"submitted_at": "now"},
        }
        with mock.patch.object(hardened, "_LEGACY_AUTOMATE", return_value=fake):
            result = hardened.publish_bilibili_job(job["id"])
        self.assertEqual(result["status"], "submitted")
        self.assertEqual(result["published_url"], "")
        self.assertFalse(result["metadata"]["remote_confirmation"])

    def test_public_video_url_is_remote_confirmation(self):
        job = self._approved_job()
        fake = {
            "status": "published",
            "published_url": "https://www.bilibili.tv/video/example",
            "metadata": {"submitted_at": "now"},
        }
        with mock.patch.object(hardened, "_LEGACY_AUTOMATE", return_value=fake):
            result = hardened.publish_bilibili_job(job["id"])
        self.assertEqual(result["status"], "published")
        self.assertTrue(result["metadata"]["remote_confirmation"])
        self.assertIn("/video/", result["published_url"])


if __name__ == "__main__":
    unittest.main()
