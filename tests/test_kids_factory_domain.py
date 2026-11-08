from __future__ import annotations

import unittest

from zmovie_platform.kids_factory import (
    KidsValidationError,
    build_storyboard,
    kids_safety_check,
    mock_youtube_upload,
    prepare_youtube_metadata,
    storyboard_to_timeline,
    validate_brand,
    validate_character,
    validate_episode,
    validate_scene,
)


class KidsDomainTests(unittest.TestCase):
    def test_brand_validation_and_copyright_block(self):
        ok = validate_brand({"slug": "lumikids", "name": "LumiKids", "language": "en", "age_band": "preschool"})
        self.assertEqual(ok["name"], "LumiKids")
        with self.assertRaises(KidsValidationError):
            validate_brand({"slug": "cocomelon-clone", "name": "Cocomelon Clone"})
        with self.assertRaises(KidsValidationError):
            validate_brand({"slug": "x", "name": "x", "language": "xx"})

    def test_character_validation_and_safety(self):
        char = validate_character({
            "name": "Pimmy Panda",
            "role": "guide",
            "species": "panda",
            "personality": "gentle and curious",
            "visual_prompt": "cute cartoon panda",
        })
        self.assertEqual(char["name"], "Pimmy Panda")
        self.assertEqual(char["species"], "panda")
        with self.assertRaises(KidsValidationError):
            validate_character({"name": "Baby Shark Ripoff"})

    def test_episode_and_scene_validation(self):
        ep = validate_episode({
            "title": "Numbers with Pimmy",
            "target_age": "preschool",
            "content_type": "counting_song",
            "duration_sec": 30,
        })
        self.assertEqual(ep["title"], "Numbers with Pimmy")

        scene = validate_scene({
            "ordering": 1,
            "duration_seconds": 5,
            "visual_prompt": "Pimmy waves at the camera",
        })
        self.assertEqual(scene["ordering"], 1)
        self.assertEqual(scene["duration_seconds"], 5.0)

    def test_kids_safety_check(self):
        res = kids_safety_check(age_band="preschool", text="Learn colors and friendly shapes!")
        self.assertTrue(res["passed"])

        res_bad = kids_safety_check(age_band="preschool", text="scary horror violent monsters blood knife gun")
        self.assertFalse(res_bad["passed"])

    def test_build_storyboard_and_timeline(self):
        script_body = {
            "title": "Fun Counting",
            "beats": [
                {"description": "Hello kids!", "duration_sec": 5.0},
                {"description": "Counting one two three!", "duration_sec": 10.0},
            ]
        }
        scenes = build_storyboard(script_body=script_body, num_scenes=2)
        self.assertEqual(len(scenes), 2)

        timeline = storyboard_to_timeline(scenes, brand_name="LumiKids")
        self.assertIn("video", timeline)

    def test_youtube_metadata_and_mock_upload(self):
        meta = prepare_youtube_metadata(
            title="Numbers 1 to 10 for Toddlers",
            description="Fun animated educational counting song for children.",
        )
        self.assertEqual(meta["audience"], "madeForKids")
        self.assertEqual(meta["synthetic_disclosure"], True)

        upload = mock_youtube_upload(
            metadata=meta,
            idempotency_key="ep-test-key-001",
            sha256="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        )
        self.assertEqual(upload["status"], "uploaded_mock")
        self.assertTrue(upload["external_id"].startswith("mock-yt-"))


if __name__ == "__main__":
    unittest.main()
