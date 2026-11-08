from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

import main
from zmovie_platform.kids_factory import (
    KidsValidationError,
    build_captions_export,
    build_language_variant,
    build_safety_corpus,
    build_storyboard,
    derive_shorts,
    estimate_cost,
    export_episode_bundle,
    import_episode_bundle,
    render_deterministic_video,
    resolve_provider_route,
    run_episode_pipeline,
    suggest_marketing,
    synth_preview_wav,
    timeline_checksum,
    validate_channel,
    validate_media_upload,
    validate_music_track,
    validate_provider_route,
    validate_schedule_slot,
    validate_script,
    validate_timeline,
    validate_voice_profile,
)


class KidsFactoryExtendedDomainTests(unittest.TestCase):
    def test_script_and_timeline_validation(self):
        script = validate_script({
            "content_type": "nursery_rhyme",
            "body": {
                "concept": "Counting stars",
                "verses": "One star, two stars in the night",
                "chorus": "Twinkle twinkle bright",
            },
        })
        self.assertEqual(script["content_type"], "nursery_rhyme")

        timeline = validate_timeline({
            "tracks": {
                "video": [{"scene_id": "s1", "duration": 5.0}],
                "captions": [{"text": "Hello A"}],
            }
        })
        self.assertIn("video", timeline["tracks"])
        chk = timeline_checksum(timeline["tracks"])
        self.assertIsInstance(chk, str)
        self.assertEqual(len(chk), 64)

    def test_channel_and_voice_and_music(self):
        chan = validate_channel({
            "name": "Kids Explorer Channel",
            "platform": "youtube",
        })
        self.assertEqual(chan["name"], "Kids Explorer Channel")

        voice = validate_voice_profile({
            "name": "Sunny Voice",
            "language": "en",
            "speed": 1.0,
        })
        self.assertEqual(voice["name"], "Sunny Voice")

        music = validate_music_track({
            "title": "Gentle Playtime",
            "license": "CC-BY-4.0",
            "duration_seconds": 60.0,
        })
        self.assertEqual(music["title"], "Gentle Playtime")

    def test_provider_route_and_cost_estimation(self):
        val_route = validate_provider_route(
            capability="video",
            providers=["mock", "ffmpeg"],
        )
        self.assertEqual(val_route["capability"], "video")

        resolved = resolve_provider_route(
            capability="video",
            providers=["mock", "ffmpeg"],
        )
        self.assertEqual(resolved["capability"], "video")
        self.assertIsNotNone(resolved["primary"])

        cost = estimate_cost(num_scenes=5, duration_total=60.0, provider="mock")
        self.assertGreater(cost, 0.0)

    def test_captions_export_and_language_variant(self):
        scenes = [
            {
                "ordering": 1,
                "duration_seconds": 4.0,
                "captions": [{"text": "First scene caption", "start": 0.0, "end": 4.0}],
            },
            {
                "ordering": 2,
                "duration_seconds": 6.0,
                "captions": [{"text": "Second scene caption", "start": 4.0, "end": 10.0}],
            },
        ]
        srt = build_captions_export(scenes=scenes, format="srt")
        self.assertIn("First scene caption", srt["content"])

        vtt = build_captions_export(scenes=scenes, format="vtt")
        self.assertTrue(vtt["content"].startswith("WEBVTT"))

        variant = build_language_variant(
            parent={"title": "Greeting", "summary": "Intro", "language": "en"},
            language="th",
        )
        self.assertEqual(variant["language"], "th")
        self.assertEqual(variant["translation_status"], "needs_review")

    def test_media_upload_and_schedule_and_marketing(self):
        validate_media_upload(
            filename="icon.png",
            content_type="image/png",
            size_bytes=1024,
        )

        with self.assertRaises(KidsValidationError):
            validate_media_upload(
                filename="../../bad.exe",
                content_type="application/octet-stream",
                size_bytes=1024,
            )

        slot = validate_schedule_slot(
            slot_at="2027-11-10T10:00:00Z",
            timezone_name="UTC",
        )
        self.assertIn("2027-11-10", slot["slot_at"])

        mkt = suggest_marketing(episode={"title": "Panda Colors", "objectives": ["red", "blue"]})
        self.assertIn("titles", mkt)
        self.assertTrue(len(mkt["titles"]) > 0)

    def test_shorts_and_bundle_export_import_and_pipeline(self):
        parent_ep = {
            "id": "ep-parent-101",
            "title": "Adventures of Ollie",
            "target_age": "preschool",
            "content_type": "nursery_rhyme",
            "duration_sec": 45,
            "brand_name": "LumiKids",
        }
        short = derive_shorts(parent_episode=parent_ep)
        self.assertEqual(short["preset"], "portrait_1080x1920")
        self.assertEqual(short["aspect_ratio"], "9:16")
        self.assertEqual(short["parent_episode_id"], "ep-parent-101")

        bundle = export_episode_bundle(
            episode=parent_ep,
            characters=[{"name": "Ollie the Owl"}],
            script={"body": {"concept": "Flying"}},
        )
        self.assertEqual(bundle["format"], "kids-export-1")

        imp = import_episode_bundle(bundle=bundle, new_id="ep-restored-999")
        self.assertTrue(imp["ok"])
        self.assertEqual(imp["episode"]["title"], "Adventures of Ollie")
        self.assertEqual(imp["counts"]["characters"], 1)

        pipe = run_episode_pipeline(episode=parent_ep, budget_credits=10.0, num_scenes=3)
        self.assertTrue(pipe["ok"])
        self.assertEqual(len(pipe["checkpoints"]), 7)

        with self.assertRaises(KidsValidationError):
            # Budget blocked when budget < estimate
            run_episode_pipeline(episode=parent_ep, budget_credits=0.01, num_scenes=5)

    def test_synth_preview_and_render_video_and_corpus(self):
        wav = synth_preview_wav(text="Hello friendly panda", speed=1.0)
        self.assertTrue(wav.startswith(b"RIFF"))

        scenes = build_storyboard(script_body={"concept": "Shapes", "chorus": "Triangles circles"})
        corpus = build_safety_corpus(
            episode={"title": "Shapes Fun", "summary": "Intro"},
            script={"body": {"concept": "Shapes"}},
            scenes=scenes,
            timeline=None,
        )
        self.assertIn("Shapes", corpus)

        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = Path(tmpdir) / "sample_test.mp4"
            render_res = render_deterministic_video(
                scenes=scenes[:2],
                preset="landscape_1080p",
                title="Test LumiKids",
                out_path=out_path,
            )
            self.assertIn("sha256", render_res)


class KidsRoutesApiTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(main.app)

    def test_api_brand_validate(self):
        res = self.client.post(
            "/api/v2/kids/brands/validate",
            json={"slug": "starry-kids", "name": "Starry Kids", "language": "en", "age_band": "preschool"},
        )
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.json()["ok"])

    def test_api_channel_validate(self):
        res = self.client.post(
            "/api/v2/kids/channels/validate",
            json={"name": "LumiKids Channel", "platform": "youtube"},
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["channel"]["name"], "LumiKids Channel")

    def test_api_character_validate(self):
        res = self.client.post(
            "/api/v2/kids/characters/validate",
            json={"name": "Kiki Koala", "species": "koala", "role": "friend"},
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["character"]["name"], "Kiki Koala")

    def test_api_script_validate(self):
        res = self.client.post(
            "/api/v2/kids/scripts/validate",
            json={"content_type": "nursery_rhyme", "body": {"verses": "ABCDEFG"}},
        )
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.json()["ok"])

    def test_api_timeline_validate(self):
        res = self.client.post(
            "/api/v2/kids/timelines/validate",
            json={"tracks": {"video": [{"scene_id": "s1", "duration": 5.0}]}},
        )
        self.assertEqual(res.status_code, 200)
        self.assertIn("checksum", res.json())

    def test_api_voice_validate_and_preview(self):
        val_res = self.client.post(
            "/api/v2/kids/voices/validate",
            json={"name": "Nursery Narrator", "language": "en", "speed": 1.1},
        )
        self.assertEqual(val_res.status_code, 200)

        prev_res = self.client.post(
            "/api/v2/kids/voices/preview",
            json={"text": "Welcome to fun counting!", "speed": 1.0},
        )
        self.assertEqual(prev_res.status_code, 200)
        self.assertIn("base64", prev_res.json())

    def test_api_music_validate(self):
        res = self.client.post(
            "/api/v2/kids/music/validate",
            json={"title": "Sunny Day Melody", "license": "CC0", "duration_seconds": 45.0},
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["music"]["title"], "Sunny Day Melody")

    def test_api_providers_routes_validate(self):
        res = self.client.post(
            "/api/v2/kids/providers/routes/validate",
            json={"capability": "video", "providers": ["mock", "ffmpeg"]},
        )
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.json()["ok"])

    def test_api_schedules_slot_validate(self):
        res = self.client.post(
            "/api/v2/kids/schedules/slots/validate",
            json={"slot_at": "2027-05-01T12:00:00Z", "timezone_name": "UTC"},
        )
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.json()["ok"])

    def test_api_media_validate(self):
        res = self.client.post(
            "/api/v2/kids/media/validate",
            json={"filename": "cover.jpg", "content_type": "image/jpeg", "size_bytes": 4096},
        )
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.json()["valid"])

    def test_api_variants_draft(self):
        res = self.client.post(
            "/api/v2/kids/variants/draft",
            json={"parent": {"title": "Lumi Bear", "summary": "Bear adventures", "language": "en"}, "language": "th"},
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["variant"]["language"], "th")

    def test_api_marketing_suggest(self):
        res = self.client.post(
            "/api/v2/kids/marketing/suggest",
            json={"episode": {"title": "Happy Shapes"}, "brand_name": "LumiKids"},
        )
        self.assertEqual(res.status_code, 200)
        self.assertIn("suggestions", res.json())

    def test_api_safety_check(self):
        res = self.client.post(
            "/api/v2/kids/safety/check",
            json={"age_band": "preschool", "text": "Happy numbers and letters"},
        )
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.json()["passed"])

    def test_api_storyboard_generate(self):
        res = self.client.post(
            "/api/v2/kids/storyboard/generate",
            json={"title": "Counting Stars", "beats": [{"description": "One bright star"}], "num_scenes": 2},
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.json()["scenes"]), 2)

    def test_api_cost_estimate(self):
        res = self.client.get("/api/v2/kids/cost/estimate?num_scenes=4&duration_total=30&provider=mock")
        self.assertEqual(res.status_code, 200)
        self.assertIn("estimated_credits", res.json())

    def test_api_captions_export(self):
        res = self.client.post(
            "/api/v2/kids/captions/export",
            json={
                "scenes": [
                    {
                        "ordering": 1,
                        "duration_seconds": 5.0,
                        "captions": [{"text": "Hello world", "start": 0.0, "end": 5.0}],
                    }
                ],
                "format": "vtt",
            },
        )
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.json()["content"].startswith("WEBVTT"))

    def test_api_pipeline_and_shorts_and_bundle(self):
        ep = {
            "id": "ep-api-01",
            "title": "Alphabet Fun",
            "target_age": "preschool",
            "content_type": "counting_song",
            "duration_sec": 30,
        }
        pipe_res = self.client.post(
            "/api/v2/kids/episodes/pipeline",
            json={"episode": ep, "budget_credits": 20.0, "num_scenes": 3},
        )
        self.assertEqual(pipe_res.status_code, 200)
        self.assertTrue(pipe_res.json()["ok"])
        self.assertEqual(pipe_res.json()["approval_state"], "pending")

        short_res = self.client.post(
            "/api/v2/kids/episodes/shorts",
            json={"parent_episode": ep, "brand_name": "LumiKids"},
        )
        self.assertEqual(short_res.status_code, 200)
        self.assertEqual(short_res.json()["short_episode"]["preset"], "portrait_1080x1920")

        exp_res = self.client.post(
            "/api/v2/kids/episodes/bundle/export",
            json={"episode": ep, "characters": [{"name": "Leo Lion"}]},
        )
        self.assertEqual(exp_res.status_code, 200)
        bundle = exp_res.json()["bundle"]

        imp_res = self.client.post(
            "/api/v2/kids/episodes/bundle/import",
            json={"bundle": bundle, "new_id": "ep-imported-02"},
        )
        self.assertEqual(imp_res.status_code, 200)
        self.assertTrue(imp_res.json()["ok"])


if __name__ == "__main__":
    unittest.main()
