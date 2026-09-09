import tempfile
import unittest
from pathlib import Path
from unittest import mock

from zmovie_platform import auth, storage
from zmovie_platform.pipeline import run_end_to_end
from zmovie_platform.providers import provider_specs
from zmovie_platform.qc import inspect_project
from zmovie_platform.repository import get_project, list_jobs, save_project
from zmovie_platform.storyboard import create_storyboard, production_manifest


class PlatformTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.old_db = storage.DB_PATH
        storage.DB_PATH = Path(self.tmp.name) / "zmovie.db"

    def tearDown(self):
        storage.DB_PATH = self.old_db
        self.tmp.cleanup()

    def test_storyboard_persists_with_character_bible_and_qc(self):
        project = create_storyboard(
            name="Test Movie",
            concept="A protagonist enters a luxury hall. A threat escalates. The conflict ends on a controlled final image.",
            target_duration_seconds=40,
        )
        self.assertTrue(project.characters)
        self.assertTrue(project.scenes)
        self.assertTrue(project.scenes[0].shots)
        save_project(project)
        loaded = get_project(project.id)
        self.assertIsNotNone(loaded)
        assert loaded is not None
        self.assertEqual(loaded.name, "Test Movie")
        self.assertEqual(len(loaded.characters), len(project.characters))
        report = inspect_project(loaded)
        self.assertTrue(report["passed"])
        manifest = production_manifest(loaded)
        self.assertEqual(manifest["schema"], "zmovie.production-manifest/v1")
        self.assertGreater(len(manifest["render_order"]), 0)

    def test_local_auth_password_and_token(self):
        auth.create_user("admin", "correct-horse-battery-staple")
        self.assertEqual(auth.user_count(), 1)
        authenticated = auth.authenticate("admin", "correct-horse-battery-staple")
        self.assertIsNotNone(authenticated)
        assert authenticated is not None
        token = auth.issue_token(authenticated)
        payload = auth.decode_token(token)
        self.assertIsNotNone(payload)
        assert payload is not None
        self.assertEqual(payload["sub"], "admin")
        self.assertIsNone(auth.authenticate("admin", "wrong-password"))

    def test_provider_catalog_includes_local_comfyui_and_gateway(self):
        ids = {item["id"] for item in provider_specs()}
        self.assertIn("mock", ids)
        self.assertIn("comfyui", ids)
        self.assertIn("webhook", ids)

    def test_end_to_end_pipeline_without_external_inference(self):
        with mock.patch("zmovie_platform.providers.shutil.which", return_value=None):
            result = run_end_to_end(
                name="Dry Run",
                concept="Establish the hero. Escalate a cinematic confrontation. Resolve decisively.",
                target_duration_seconds=20,
                provider="mock",
            )
        self.assertTrue(result["qc"]["passed"])
        self.assertEqual(result["render"]["status"], "completed")
        self.assertEqual(result["assembly"]["status"], "manifest-only")
        project_id = result["project"]["id"]
        self.assertIsNotNone(get_project(project_id))
        jobs = list_jobs(project_id)
        self.assertGreater(len(jobs), 0)
        self.assertTrue(all(item["status"] == "completed" for item in jobs))


if __name__ == "__main__":
    unittest.main()
