import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from zmovie_platform.providers import ComfyUIProvider


class ComfyUIProviderTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.workflow = self.root / "workflow_api.json"
        self.workflow.write_text(
            json.dumps(
                {
                    "1": {"inputs": {"text": "{{PROMPT}}"}, "class_type": "CLIPTextEncode", "_meta": {"title": "Positive Prompt"}},
                    "2": {"inputs": {"text": "{{NEGATIVE_PROMPT}}"}, "class_type": "CLIPTextEncode", "_meta": {"title": "Negative Prompt"}},
                    "3": {"inputs": {"seed": "{{SEED}}"}, "class_type": "RandomNoise"},
                    "4": {"inputs": {"width": "{{WIDTH}}", "height": "{{HEIGHT}}", "length": "{{FRAMES}}"}, "class_type": "VideoLatent"},
                    "5": {"inputs": {"filename_prefix": "{{PREFIX}}"}, "class_type": "SaveVideo"},
                }
            ),
            encoding="utf-8",
        )
        self.provider = ComfyUIProvider()

    def tearDown(self):
        self.tmp.cleanup()

    def test_workflow_placeholders_and_wan_frame_shape(self):
        env = {
            "ZMOVIE_COMFYUI_WORKFLOW": str(self.workflow),
            "ZMOVIE_COMFYUI_FPS": "16",
            "ZMOVIE_COMFYUI_FRAME_MULTIPLE": "4",
            "ZMOVIE_COMFYUI_FRAME_OFFSET": "1",
            "ZMOVIE_COMFYUI_SEED": "12345",
        }
        with mock.patch.dict(os.environ, env, clear=False):
            workflow, values = self.provider._load_workflow(
                "hero crosses the ballroom",
                "bad anatomy",
                {"job_id": "job_test", "project_id": "project_test", "shot_id": "shot_test", "duration_seconds": 5, "aspect_ratio": "16:9"},
            )
        self.assertEqual(workflow["1"]["inputs"]["text"], "hero crosses the ballroom")
        self.assertEqual(workflow["2"]["inputs"]["text"], "bad anatomy")
        self.assertEqual(workflow["3"]["inputs"]["seed"], 12345)
        self.assertEqual(workflow["4"]["inputs"]["width"], 1280)
        self.assertEqual(workflow["4"]["inputs"]["height"], 720)
        self.assertEqual((int(values["FRAMES"]) - 1) % 4, 0)
        self.assertIn("job_test", workflow["5"]["inputs"]["filename_prefix"])

    def test_node_id_injection_overrides_workflow_inputs(self):
        env = {
            "ZMOVIE_COMFYUI_WORKFLOW": str(self.workflow),
            "ZMOVIE_COMFYUI_POSITIVE_NODE_IDS": "1",
            "ZMOVIE_COMFYUI_NEGATIVE_NODE_IDS": "2",
            "ZMOVIE_COMFYUI_SEED_NODE_IDS": "3",
            "ZMOVIE_COMFYUI_FRAMES_NODE_IDS": "4",
            "ZMOVIE_COMFYUI_SIZE_NODE_IDS": "4",
            "ZMOVIE_COMFYUI_WIDTH": "720",
            "ZMOVIE_COMFYUI_HEIGHT": "1280",
            "ZMOVIE_COMFYUI_SEED": "9",
        }
        with mock.patch.dict(os.environ, env, clear=False):
            workflow, _ = self.provider._load_workflow(
                "positive",
                "negative",
                {"job_id": "job_nodes", "duration_seconds": 10, "aspect_ratio": "9:16"},
            )
        self.assertEqual(workflow["1"]["inputs"]["text"], "positive")
        self.assertEqual(workflow["2"]["inputs"]["text"], "negative")
        self.assertEqual(workflow["3"]["inputs"]["seed"], 9)
        self.assertEqual(workflow["4"]["inputs"]["width"], 720)
        self.assertEqual(workflow["4"]["inputs"]["height"], 1280)
        self.assertIsInstance(workflow["4"]["inputs"]["length"], int)

    def test_history_output_reference_collection(self):
        refs = []
        ComfyUIProvider._collect_output_refs(
            {"9": {"gifs": [{"filename": "movie.mp4", "subfolder": "zmovie", "type": "output"}]}},
            refs,
        )
        self.assertEqual(refs[0]["filename"], "movie.mp4")
        self.assertEqual(refs[0]["subfolder"], "zmovie")

    def test_existing_prompt_id_is_reconciled_without_resubmission(self):
        env = {"ZMOVIE_COMFYUI_WORKFLOW": str(self.workflow)}
        metadata = {
            "job_id": "job_resume",
            "duration_seconds": 5,
            "aspect_ratio": "16:9",
            "comfyui_prompt_id": "prompt-existing",
            "comfyui_client_id": "client-existing",
        }
        entry = {"outputs": {"9": {"gifs": [{"filename": "movie.mp4", "subfolder": "", "type": "output"}]}}}
        with (
            mock.patch.dict(os.environ, env, clear=False),
            mock.patch.object(self.provider, "_request_json") as request_json,
            mock.patch.object(self.provider, "_wait_for_history", return_value=entry) as wait_history,
            mock.patch.object(self.provider, "_download_outputs", return_value=(["movie.mp4"], "movie.mp4", "video")),
        ):
            result = self.provider.submit(
                prompt="product hero",
                negative_prompt="bad",
                output_dir=self.root / "out",
                metadata=metadata,
            )
        request_json.assert_not_called()
        wait_history.assert_called_once_with("prompt-existing")
        self.assertTrue(result["comfyui_reconciled"])
        self.assertEqual(result["comfyui_prompt_id"], "prompt-existing")


if __name__ == "__main__":
    unittest.main()
