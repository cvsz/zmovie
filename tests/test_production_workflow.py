import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock

from zmovie_platform import production, storage
from zmovie_platform.repository import add_asset, new_job, save_job, save_project
from zmovie_platform.storyboard import create_storyboard


class ProductionWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.old_db = storage.DB_PATH
        storage.DB_PATH = self.root / "zmovie.db"
        self.media = self.root / "media"
        self.exports = self.root / "exports"
        self.publish = self.root / "publish"
        self.env = mock.patch.dict(
            "os.environ",
            {
                "ZMOVIE_MEDIA_ROOT": str(self.media),
                "ZMOVIE_EXPORT_ROOT": str(self.exports),
                "ZMOVIE_PUBLISH_ROOT": str(self.publish),
                "ZMOVIE_OBJECT_ROOT": str(self.root / "objects"),
            },
        )
        self.env.start()
        self.export_patch = mock.patch.object(production, "EXPORT_ROOT", self.exports)
        self.publish_patch = mock.patch.object(production, "PUBLISH_ROOT", self.publish)
        self.export_patch.start()
        self.publish_patch.start()
        self.project = create_storyboard(
            name="Production Test",
            concept="Hook the viewer. Demonstrate the product. End on a strong CTA.",
            genre="commercial",
            target_duration_seconds=30,
            scene_count=3,
        )
        save_project(self.project)

    def tearDown(self):
        self.publish_patch.stop()
        self.export_patch.stop()
        self.env.stop()
        storage.DB_PATH = self.old_db
        self.tmp.cleanup()

    @staticmethod
    def _ready_report(path: str):
        return {
            "ready": True,
            "reason": "ok",
            "path": path,
            "size_bytes": 128,
            "codec": "h264",
            "width": 1280,
            "height": 720,
            "duration_seconds": 10.0,
        }

    def test_mock_provider_is_never_production_provider(self):
        with self.assertRaises(RuntimeError):
            production.render_all_production(self.project.id, "mock", 2)

    def test_configured_comfyui_is_blocked_when_runtime_is_not_production_ready(self):
        specs = [
            {
                "id": "comfyui",
                "name": "ComfyUI / Local AI Renderer",
                "configured": True,
            }
        ]
        blocked_status = {
            "production_ready": False,
            "reasons": ["workflow_role_not_video:smoke", "accelerator_required"],
            "workflow_role": "smoke",
            "accelerated": False,
            "reachable": True,
        }
        with mock.patch.object(production, "provider_specs", return_value=specs), mock.patch.object(
            production, "_comfyui_production_status", return_value=blocked_status
        ):
            state = production.production_readiness(self.project.id)
            self.assertEqual(state["providers"], [])
            self.assertEqual(state["blocked_providers"][0]["id"], "comfyui")
            self.assertIn("accelerator_required", state["blocked_providers"][0]["reasons"])
            with self.assertRaisesRegex(RuntimeError, "configured but not production-ready"):
                production._require_production_provider("comfyui")

    def test_readiness_requires_valid_video_for_every_shot(self):
        shots = [shot for scene in self.project.scenes for shot in scene.shots]
        for shot in shots:
            job = new_job(self.project.id, shot.id, "comfyui")
            job.status = "completed"
            job.output_path = str(self.media / f"{shot.id}.mp4")
            save_job(job)
        with mock.patch.object(production, "production_video_report", side_effect=lambda path: self._ready_report(path)):
            state = production.production_readiness(self.project.id)
        self.assertTrue(state["render"]["ready"])
        self.assertTrue(state["assemble"]["ready"])
        self.assertFalse(state["final"]["ready"])
        self.assertEqual(state["render"]["completed_shots"], len(shots))
        self.assertEqual(state["render"]["invalid_outputs"], [])

    def test_readiness_reports_non_video_comfyui_outputs(self):
        shot = self.project.scenes[0].shots[0]
        job = new_job(self.project.id, shot.id, "comfyui")
        job.status = "completed"
        job.output_path = str(self.media / "preview.png")
        save_job(job)

        def report(path: str):
            if Path(path).suffix == ".png":
                return {"ready": False, "reason": "not_video_file", "path": path}
            return {"ready": False, "reason": "file_missing", "path": path}

        with mock.patch.object(production, "production_video_report", side_effect=report):
            state = production.production_readiness(self.project.id)
        invalid = state["render"]["invalid_outputs"]
        self.assertEqual(len(invalid), 1)
        self.assertEqual(invalid[0]["shot_id"], shot.id)
        self.assertEqual(invalid[0]["reason"], "not_video_file")
        self.assertEqual(invalid[0]["output_name"], "preview.png")

    def test_production_export_contains_final_media_metadata_and_checksums(self):
        final = self.media / self.project.id / "final.mp4"
        final.parent.mkdir(parents=True, exist_ok=True)
        final.write_bytes(b"production-video-placeholder")
        add_asset(self.project.id, "final", "final", str(final), {"production": True})

        with mock.patch.object(production, "production_video_report", side_effect=lambda path: self._ready_report(str(Path(path).resolve()))):
            archive = production.export_production_package(self.project.id)

        self.assertTrue(archive.is_file())
        with zipfile.ZipFile(archive) as handle:
            names = set(handle.namelist())
        self.assertIn("media/final.mp4", names)
        self.assertIn("manifest.json", names)
        self.assertIn("prompts.md", names)
        self.assertIn("package.json", names)
        self.assertIn("checksums.sha256", names)


if __name__ == "__main__":
    unittest.main()
