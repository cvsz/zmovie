from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock

from zmovie_platform import storage
from zmovie_platform.publishers import bilibili_launch_candidate
from zmovie_platform.repository import get_project, list_assets


class BilibiliLaunchCandidateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        storage.DB_PATH = self.root / "zmovie.db"
        bilibili_launch_candidate.MEDIA_ROOT = self.root / "media"

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_create_launch_candidate_registers_real_final_asset(self) -> None:
        def fake_render(output: Path, *, duration: int = 18):
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_bytes(b"not-a-real-video-but-a-managed-test-fixture")
            return {
                "codec": "h264",
                "width": 1280,
                "height": 720,
                "frame_rate": "24/1",
                "duration_seconds": float(duration),
                "size_bytes": output.stat().st_size,
                "font_rendered": True,
            }

        with mock.patch.object(bilibili_launch_candidate, "_render_launch_video", side_effect=fake_render):
            result = bilibili_launch_candidate.create_launch_candidate(duration=18)

        project_id = result["project_id"]
        project = get_project(project_id)
        self.assertIsNotNone(project)
        assert project is not None
        self.assertNotIn("smoke", project.name.lower())
        self.assertNotIn("mock", project.name.lower())
        self.assertNotIn("test", project.name.lower())

        assets = list_assets(project_id, "final")
        self.assertEqual(len(assets), 1)
        self.assertTrue(Path(assets[0]["path"]).is_file())
        self.assertEqual(assets[0]["metadata"]["source"], "ffmpeg_launch_candidate")
        self.assertTrue(assets[0]["metadata"]["production_candidate"])
        self.assertFalse(assets[0]["metadata"]["ai_model_rendered"])
        self.assertIn("FFmpeg", assets[0]["metadata"]["disclosure"])


if __name__ == "__main__":
    unittest.main()
