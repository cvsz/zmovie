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
        def fake_render(output: Path, *, duration: int = bilibili_launch_candidate.DEFAULT_DURATION):
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_bytes(b"not-a-real-video-but-a-managed-test-fixture")
            return {
                "codec": "h264",
                "width": 1280,
                "height": 720,
                "frame_rate": "24/1",
                "duration_seconds": float(duration),
                "size_bytes": output.stat().st_size,
                "audio_codec": "aac",
                "audio_sample_rate": 48000,
                "audio_channels": 2,
                "font_rendered": True,
                "soundtrack_generated": True,
                "soundtrack_source": "ffmpeg_synth",
                "voiceover_generated": True,
                "voiceover_provider": "edge-tts",
                "voiceover_voice": bilibili_launch_candidate.DEFAULT_TTS_VOICE,
                "voiceover_language": "th-TH",
                "voiceover_text": bilibili_launch_candidate.DEFAULT_VOICEOVER,
                "voice_first_mix": True,
                "music_gain": 0.055,
                "voice_gain": 1.75,
                "audio_mastering": "loudnorm I=-15 TP=-1.5 LRA=9",
            }

        with mock.patch.object(bilibili_launch_candidate, "_render_launch_video", side_effect=fake_render):
            result = bilibili_launch_candidate.create_launch_candidate()

        project_id = result["project_id"]
        project = get_project(project_id)
        self.assertIsNotNone(project)
        assert project is not None
        self.assertIn("ZeaZDev", project.name)
        self.assertIn("Bilibili", project.name)
        self.assertIn("Full Ads Production", project.name)
        self.assertNotIn("smoke", project.name.lower())
        self.assertNotIn("mock", project.name.lower())
        self.assertNotIn("test", project.name.lower())

        assets = list_assets(project_id, "final")
        self.assertEqual(len(assets), 1)
        self.assertTrue(Path(assets[0]["path"]).is_file())
        metadata = assets[0]["metadata"]
        self.assertEqual(metadata["source"], "ffmpeg_launch_candidate")
        self.assertTrue(metadata["production_candidate"])
        self.assertEqual(metadata["campaign"], "ZeaZDev × Bilibili")
        self.assertEqual(metadata["campaign_type"], "creator_publishing_ad")
        self.assertFalse(metadata["official_partnership_claimed"])
        self.assertFalse(metadata["ai_model_rendered"])
        self.assertIn("FFmpeg", metadata["disclosure"])
        self.assertIn("does not represent an official partnership", metadata["disclosure"])
        self.assertEqual(result["media"]["duration_seconds"], float(bilibili_launch_candidate.DEFAULT_DURATION))
        self.assertEqual(result["media"]["audio_codec"], "aac")
        self.assertEqual(result["media"]["audio_sample_rate"], 48000)
        self.assertEqual(result["media"]["audio_channels"], 2)
        self.assertTrue(result["media"]["soundtrack_generated"])
        self.assertTrue(result["media"]["voiceover_generated"])
        self.assertEqual(result["media"]["voiceover_provider"], "edge-tts")
        self.assertEqual(result["media"]["voiceover_language"], "th-TH")
        self.assertTrue(result["media"]["voice_first_mix"])
        self.assertIn("loudnorm", result["media"]["audio_mastering"])

    def test_edge_provider_uses_neural_voice_when_available(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with (
                mock.patch.dict(
                    "os.environ",
                    {
                        "ZMOVIE_TTS_PROVIDER": "edge",
                        "ZMOVIE_TTS_VOICE": bilibili_launch_candidate.DEFAULT_TTS_VOICE,
                        "ZMOVIE_TTS_ALLOW_LOCAL_FALLBACK": "false",
                    },
                    clear=False,
                ),
                mock.patch.object(bilibili_launch_candidate, "_edge_tts", return_value=True),
            ):
                result = bilibili_launch_candidate._render_voiceover(root, "สวัสดี")

        self.assertTrue(result["generated"])
        self.assertEqual(result["provider"], "edge-tts")
        self.assertEqual(result["voice"], bilibili_launch_candidate.DEFAULT_TTS_VOICE)
        self.assertEqual(result["language"], "th-TH")

    def test_edge_provider_fails_closed_without_local_opt_in(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with (
                mock.patch.dict(
                    "os.environ",
                    {
                        "ZMOVIE_TTS_PROVIDER": "edge",
                        "ZMOVIE_TTS_ALLOW_LOCAL_FALLBACK": "false",
                    },
                    clear=False,
                ),
                mock.patch.object(bilibili_launch_candidate, "_edge_tts", return_value=False),
                mock.patch.object(bilibili_launch_candidate, "_local_tts", return_value=(True, "espeak-ng")),
            ):
                with self.assertRaisesRegex(RuntimeError, "production render stopped"):
                    bilibili_launch_candidate._render_voiceover(root, "สวัสดี")

    def test_edge_provider_uses_local_only_when_explicitly_allowed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with (
                mock.patch.dict(
                    "os.environ",
                    {
                        "ZMOVIE_TTS_PROVIDER": "edge",
                        "ZMOVIE_TTS_ALLOW_LOCAL_FALLBACK": "true",
                    },
                    clear=False,
                ),
                mock.patch.object(bilibili_launch_candidate, "_edge_tts", return_value=False),
                mock.patch.object(bilibili_launch_candidate, "_local_tts", return_value=(True, "espeak-ng")),
            ):
                result = bilibili_launch_candidate._render_voiceover(root, "สวัสดี")

        self.assertTrue(result["generated"])
        self.assertEqual(result["provider"], "espeak-ng")
        self.assertEqual(result["voice"], "th")
        self.assertEqual(result["language"], "th-TH")


if __name__ == "__main__":
    unittest.main()
