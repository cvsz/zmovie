from __future__ import annotations

import os
import unittest
from unittest import mock

from zmovie_platform.publishers import bilibili_launch_candidate as launch
from zmovie_platform.publishers import production_gen


class ProductionGenTests(unittest.TestCase):
    def setUp(self) -> None:
        self.original_voiceover = launch.DEFAULT_VOICEOVER
        self.original_voice_start = launch.DEFAULT_VOICE_START_SECONDS

    def tearDown(self) -> None:
        launch.DEFAULT_VOICEOVER = self.original_voiceover
        launch.DEFAULT_VOICE_START_SECONDS = self.original_voice_start

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
                "voice_start_seconds": 1.2,
            },
        }

    @staticmethod
    def stale_project(project_id: str = "prj_old") -> dict:
        return {
            "id": project_id,
            "owner": "zmovie-production",
            "name": launch.DEFAULT_NAME,
            "concept": launch.DEFAULT_CONCEPT,
            "target_duration_seconds": 30,
        }

    def test_create_production_candidate_locks_30s_thai_profile(self) -> None:
        cleanup = {"deleted": [], "preserved": [], "errors": [], "cleanup_complete": True}
        with (
            mock.patch.object(production_gen, "_voice_preflight", return_value=24.25),
            mock.patch.object(launch, "create_launch_candidate", return_value=self.valid_result()) as create,
            mock.patch.object(production_gen, "_supersede_stale_candidates", return_value=cleanup) as supersede,
        ):
            result = production_gen.create_production_candidate()

        create.assert_called_once_with(duration=30)
        supersede.assert_called_once_with("prj_prod")
        self.assertEqual(launch.DEFAULT_VOICEOVER, production_gen.APPROVED_VOICEOVER)
        self.assertEqual(launch.DEFAULT_VOICE_START_SECONDS, 1.2)
        self.assertIn("ซีมูฟวี่", production_gen.APPROVED_VOICEOVER)
        self.assertIn("เวิร์กโฟลว์เดียว", production_gen.APPROVED_VOICEOVER)
        profile = result["production_gen"]
        self.assertEqual(profile["profile"], "thai-30s-voice-music-v2")
        self.assertEqual(profile["target_duration_seconds"], 30)
        self.assertTrue(profile["combined_voice_and_music"])
        self.assertFalse(profile["bilibili_upload_performed"])
        self.assertFalse(profile["approval_performed"])
        self.assertEqual(profile["tts_voice"], "th-TH-PremwadeeNeural")
        self.assertEqual(profile["tts_rate"], "-15%")
        self.assertEqual(profile["voice_preflight_seconds"], 24.25)
        self.assertEqual(profile["voice_start_seconds"], 1.2)
        self.assertEqual(profile["supersede_cleanup"], cleanup)
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

    def test_validate_result_rejects_wrong_voice_start(self) -> None:
        result = self.valid_result()
        result["media"]["voice_start_seconds"] = 0.85
        with self.assertRaisesRegex(RuntimeError, "voice-start mismatch"):
            production_gen._validate_result(result)

    def test_supersede_removes_only_unapproved_exact_match_candidate(self) -> None:
        stale = self.stale_project()
        prepared_job = {"id": "pub_old", "status": "prepared", "published_url": "", "metadata": {}}
        filesystem = {"removed": ["/tmp/prj_old"], "errors": []}
        with (
            mock.patch.object(production_gen, "list_projects", return_value=[stale]),
            mock.patch.object(production_gen, "list_publish_jobs", return_value=[prepared_job]),
            mock.patch.object(production_gen, "delete_project", return_value=True) as delete,
            mock.patch.object(production_gen, "_remove_managed_project_dirs", return_value=filesystem),
        ):
            result = production_gen._supersede_stale_candidates("prj_new")

        delete.assert_called_once_with("prj_old")
        self.assertTrue(result["cleanup_complete"])
        self.assertEqual(result["deleted"][0]["project_id"], "prj_old")
        self.assertEqual(result["deleted"][0]["publish_jobs_removed"], 1)
        self.assertEqual(result["preserved"], [])

    def test_supersede_preserves_approved_or_submitted_candidate(self) -> None:
        stale = self.stale_project()
        protected_jobs = [
            {
                "id": "pub_approved",
                "status": "failed",
                "published_url": "",
                "metadata": {"approved_at": "now"},
            },
            {
                "id": "pub_submitted",
                "status": "submitted",
                "published_url": "",
                "metadata": {"submitted_at": "now"},
            },
        ]
        with (
            mock.patch.object(production_gen, "list_projects", return_value=[stale]),
            mock.patch.object(production_gen, "list_publish_jobs", return_value=protected_jobs),
            mock.patch.object(production_gen, "delete_project") as delete,
        ):
            result = production_gen._supersede_stale_candidates("prj_new")

        delete.assert_not_called()
        self.assertEqual(result["deleted"], [])
        self.assertEqual(result["preserved"][0]["project_id"], "prj_old")
        self.assertIn("submitted", result["preserved"][0]["statuses"])

    def test_supersede_ignores_non_matching_project(self) -> None:
        other = self.stale_project("prj_other")
        other["owner"] = "someone-else"
        with (
            mock.patch.object(production_gen, "list_projects", return_value=[other]),
            mock.patch.object(production_gen, "list_publish_jobs") as jobs,
            mock.patch.object(production_gen, "delete_project") as delete,
        ):
            result = production_gen._supersede_stale_candidates("prj_new")

        jobs.assert_not_called()
        delete.assert_not_called()
        self.assertTrue(result["cleanup_complete"])


if __name__ == "__main__":
    unittest.main()
