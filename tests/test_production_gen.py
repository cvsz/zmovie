from __future__ import annotations

import os
import unittest
from unittest import mock

from zmovie_platform.publishers import bilibili_launch_candidate as launch
from zmovie_platform.publishers import production_gen


class ProductionGenTests(unittest.TestCase):
    def setUp(self) -> None:
        self.original_voiceover = launch.DEFAULT_VOICEOVER

    def tearDown(self) -> None:
        launch.DEFAULT_VOICEOVER = self.original_voiceover

    @staticmethod
    def valid_result() -> dict:
        return {
            "status": "created",
            "project_id": "prj_prod",
            "final_asset": {"path": "/tmp/final.mp4"},
            "media": {
                "codec": "h264",
                "width": 1280,
                "height": 720,
                "frame_rate": "24/1",
                "duration_seconds": 30.0,
                "audio_codec": "aac",
                "audio_sample_rate": 48000,
                "audio_channels": 2,
                "duration_locked": True,
            },
        }

    def test_create_production_candidate_locks_30s_thai_profile(self) -> None:
        with (
            mock.patch.object(production_gen, "_voice_preflight", return_value=24.25),
            mock.patch.object(launch, "create_launch_candidate", return_value=self.valid_result()) as create,
        ):
            result = production_gen.create_production_candidate()

        create.assert_called_once_with(duration=30)
        self.assertEqual(launch.DEFAULT_VOICEOVER, production_gen.APPROVED_VOICEOVER)
        self.assertIn("ซีมูฟวี่", production_gen.APPROVED_VOICEOVER)
        self.assertIn("เวิร์กโฟลว์เดียว", production_gen.APPROVED_VOICEOVER)
        profile = result["production_gen"]
        self.assertEqual(profile["profile"], "thai-30s-voice-music-v1")
        self.assertEqual(profile["target_duration_seconds"], 30)
        self.assertTrue(profile["combined_voice_and_music"])
        self.assertFalse(profile["bilibili_upload_performed"])
        self.assertFalse(profile["approval_performed"])
        self.assertEqual(profile["tts_voice"], "th-TH-PremwadeeNeural")
        self.assertEqual(profile["tts_rate"], "-15%")
        self.assertEqual(profile["voice_preflight_seconds"], 24.25)
        self.assertEqual(os.environ["ZMOVIE_TTS_PROVIDER"], "edge")
        self.assertEqual(os.environ["ZMOVIE_TTS_ALLOW_LOCAL_FALLBACK"], "false")

    def test_validate_result_rejects_non_30_second_output(self) -> None:
        result = self.valid_result()
        result["media"]["duration_seconds"] = 29.0
        with self.assertRaisesRegex(RuntimeError, "duration mismatch"):
            production_gen._validate_result(result)

    def test_validate_result_rejects_missing_duration_lock(self) -> None:
        result = self.valid_result()
        result["media"]["duration_locked"] = False
        with self.assertRaisesRegex(RuntimeError, "duration_locked"):
            production_gen._validate_result(result)


if __name__ == "__main__":
    unittest.main()
