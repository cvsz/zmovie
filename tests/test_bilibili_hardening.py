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


class _CapturePage:
    def __init__(self):
        self.url = "https://studio.bilibili.tv/"
        self.closed = False
        self.reloaded = False

    def reload(self, **_kwargs):
        self.reloaded = True

    def close(self):
        self.closed = True


class _CaptureContext:
    def __init__(self, page):
        self.pages = [page]
        self.saved = None

    def new_page(self):
        page = _CapturePage()
        self.pages.append(page)
        return page

    def storage_state(self, *, path, indexed_db=False):
        self.saved = (Path(path), indexed_db)
        Path(path).write_text('{"cookies":[],"origins":[]}', encoding="utf-8")
        return {"cookies": [], "origins": []}


class _CaptureBrowser:
    def __init__(self, context):
        self.contexts = [context]
        self.closed = False

    def close(self):
        self.closed = True


class _CaptureChromium:
    def __init__(self, browser):
        self.browser = browser
        self.endpoint = None
        self.timeout = None

    def connect_over_cdp(self, endpoint, timeout=0):
        self.endpoint = endpoint
        self.timeout = timeout
        return self.browser


class _CapturePlaywright:
    def __init__(self, chromium):
        self.chromium = chromium


class _CaptureManager:
    def __init__(self, playwright):
        self.playwright = playwright

    def __enter__(self):
        return self.playwright

    def __exit__(self, *_args):
        return False


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

    def test_devtools_active_port_builds_loopback_websocket(self):
        user_data = self.root / "Chrome User Data"
        user_data.mkdir()
        (user_data / "DevToolsActivePort").write_text(
            "9222\n/devtools/browser/example-token\n",
            encoding="utf-8",
        )
        self.assertEqual(
            hardened._devtools_ws_endpoint(user_data),
            "ws://127.0.0.1:9222/devtools/browser/example-token",
        )

    def test_capture_existing_chrome_saves_authenticated_storage_state(self):
        page = _CapturePage()
        context = _CaptureContext(page)
        browser = _CaptureBrowser(context)
        chromium = _CaptureChromium(browser)
        playwright = _CapturePlaywright(chromium)
        manager = _CaptureManager(playwright)
        target = self.root / "storage_state.json"

        with mock.patch.object(bilibili, "_playwright_import", return_value=lambda: manager), mock.patch.object(
            bilibili, "_logged_in", return_value=True
        ):
            result = hardened.capture_existing_chrome_session(
                target,
                cdp_endpoint="ws://127.0.0.1:9222/devtools/browser/example-token",
            )

        self.assertEqual(result, target.resolve())
        self.assertTrue(target.is_file())
        self.assertEqual(context.saved, (target.resolve(), True))
        self.assertEqual(chromium.endpoint, "ws://127.0.0.1:9222/devtools/browser/example-token")
        self.assertEqual(chromium.timeout, 30000)
        self.assertTrue(page.reloaded)
        self.assertTrue(browser.closed)

    def test_capture_existing_chrome_refuses_unauthenticated_profile(self):
        page = _CapturePage()
        context = _CaptureContext(page)
        browser = _CaptureBrowser(context)
        chromium = _CaptureChromium(browser)
        manager = _CaptureManager(_CapturePlaywright(chromium))

        with mock.patch.object(bilibili, "_playwright_import", return_value=lambda: manager), mock.patch.object(
            bilibili, "_logged_in", return_value=False
        ):
            with self.assertRaisesRegex(RuntimeError, "not authenticated"):
                hardened.capture_existing_chrome_session(
                    self.root / "bad-state.json",
                    cdp_endpoint="ws://127.0.0.1:9222/devtools/browser/example-token",
                )

        self.assertFalse((self.root / "bad-state.json").exists())
        self.assertTrue(browser.closed)

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
