import tempfile
import unittest
from pathlib import Path
from unittest import mock

from zmovie_platform import storage
from zmovie_platform.publishers import bilibili
from zmovie_platform.publishers import bilibili_confirm
from zmovie_platform.repository import add_asset, save_project
from zmovie_platform.storyboard import create_storyboard


class _Response:
    status = 200


class _Body:
    def inner_text(self, timeout=0):
        return "Public Bilibili video page"


class _Page:
    def __init__(self, url):
        self.url = url

    def goto(self, url, **_kwargs):
        self.url = url
        return _Response()

    def locator(self, _selector):
        return _Body()


class _Context:
    def __init__(self, url):
        self.url = url

    def new_page(self):
        return _Page(self.url)


class _Browser:
    def __init__(self):
        self.closed = False

    def close(self):
        self.closed = True


class _Playwright:
    pass


class _Manager:
    def __enter__(self):
        return _Playwright()

    def __exit__(self, *_args):
        return False


class BilibiliConfirmationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.old_db = storage.DB_PATH
        self.old_publish_root = bilibili.PUBLISH_ROOT
        storage.DB_PATH = self.root / "zmovie.db"
        bilibili.PUBLISH_ROOT = self.root / "publish"
        self.project = create_storyboard(
            name="Confirmation test",
            concept="A controlled public confirmation test.",
            genre="cinematic",
            target_duration_seconds=20,
        )
        save_project(self.project)
        self.video = self.root / "final.mp4"
        self.video.write_bytes(b"fake-video")
        add_asset(self.project.id, "final", "assembled movie", str(self.video))

        def fake_cover(_video, output):
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_bytes(b"fake-jpeg")
            return output.resolve()

        with mock.patch.object(bilibili, "_cover_from_video", side_effect=fake_cover):
            job = bilibili.prepare_bilibili_publish(self.project.id)
        bilibili.approve_publish_job(job["id"])
        self.job = bilibili._update_job(job["id"], status="submitted")
        self.state = self.root / "storage_state.json"
        self.state.write_text('{"cookies":[],"origins":[]}', encoding="utf-8")

    def tearDown(self):
        storage.DB_PATH = self.old_db
        bilibili.PUBLISH_ROOT = self.old_publish_root
        self.tmp.cleanup()

    def test_url_validation_requires_https_bilibili_video(self):
        self.assertTrue(bilibili_confirm._is_public_bilibili_video_url("https://www.bilibili.tv/video/123"))
        self.assertTrue(bilibili_confirm._is_public_bilibili_video_url("https://www.bilibili.tv/en/video/123"))
        self.assertFalse(bilibili_confirm._is_public_bilibili_video_url("http://www.bilibili.tv/video/123"))
        self.assertFalse(bilibili_confirm._is_public_bilibili_video_url("https://evil.example/video/123"))
        self.assertFalse(bilibili_confirm._is_public_bilibili_video_url("https://www.bilibili.tv/"))

    def test_confirm_publication_live_probe_sets_remote_confirmation(self):
        url = "https://www.bilibili.tv/en/video/2040000000"
        browser = _Browser()
        context = _Context(url)
        with mock.patch.object(bilibili, "_playwright_import", return_value=lambda: _Manager()), mock.patch.object(
            bilibili, "_browser_context", return_value=(browser, context)
        ):
            result = bilibili_confirm.confirm_publication(
                self.job["id"],
                url,
                state_path=self.state,
                probe=True,
            )
        self.assertEqual(result["status"], "published")
        self.assertEqual(result["published_url"], url)
        self.assertTrue(result["metadata"]["remote_confirmation"])
        self.assertEqual(result["metadata"]["remote_confirmation_source"], "public_url_probe")
        self.assertTrue(result["metadata"]["remote_confirmation_probe"]["reachable"])
        self.assertTrue(browser.closed)

    def test_confirm_refuses_non_submitted_job(self):
        prepared = bilibili._update_job(self.job["id"], status="approved")
        self.assertEqual(prepared["status"], "approved")
        with self.assertRaisesRegex(ValueError, "requires submitted/published status"):
            bilibili_confirm.confirm_publication(
                self.job["id"],
                "https://www.bilibili.tv/video/123",
                state_path=self.state,
                probe=False,
            )

    def test_confirm_is_idempotent_after_remote_confirmation(self):
        url = "https://www.bilibili.tv/video/123"
        first = bilibili_confirm.confirm_publication(
            self.job["id"],
            url,
            state_path=self.state,
            probe=False,
        )
        second = bilibili_confirm.confirm_publication(
            self.job["id"],
            url,
            state_path=self.state,
            probe=False,
        )
        self.assertEqual(first["status"], "published")
        self.assertEqual(second["published_url"], url)
        self.assertTrue(second["metadata"]["remote_confirmation"])


if __name__ == "__main__":
    unittest.main()
