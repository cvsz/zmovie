import tempfile
import unittest
from pathlib import Path

from zmovie_platform import storage
from zmovie_platform.content_storyboard import build_content_blueprint, create_content_storyboard
from zmovie_platform.repository import get_project


class ContentStoryboardTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.old_db = storage.DB_PATH
        storage.DB_PATH = Path(self.tmp.name) / "zmovie.db"

    def tearDown(self):
        storage.DB_PATH = self.old_db
        self.tmp.cleanup()

    def test_blueprint_builds_campaign_beats_and_cta(self):
        blueprint = build_content_blueprint(
            topic="Launch zMovie as a self-hosted creator production platform",
            audience="video creators",
            goal="conversion campaign",
            brand="ZeaZDev",
            call_to_action="Try zMovie",
            target_duration_seconds=60,
            seed=7,
        )
        self.assertEqual(blueprint["scene_count"], 3)
        self.assertEqual(blueprint["beats"][0]["title"], "Hook")
        self.assertIn("Try zMovie", blueprint["concept"])
        self.assertTrue(str(blueprint["title"]).startswith("ZeaZDev"))

    def test_one_click_storyboard_persists_generated_content(self):
        result = create_content_storyboard(
            topic="A premium launch film for zMovie",
            audience="independent creators",
            goal="product launch",
            brand="ZeaZDev",
            call_to_action="Create, render and publish with zMovie",
            target_duration_seconds=30,
            owner="admin",
            seed=11,
        )
        project = result["project"]
        self.assertTrue(project["id"].startswith("prj_"))
        self.assertEqual(project["owner"], "admin")
        self.assertEqual(project["scenes"][0]["title"], "Hook")
        self.assertTrue(project["scenes"][0]["shots"][0]["prompt"])
        self.assertTrue(result["qc"]["passed"])
        self.assertIsNotNone(get_project(project["id"]))


if __name__ == "__main__":
    unittest.main()
