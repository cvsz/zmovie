import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from zmovie_platform.providers import COMFYUI, provider_specs


class ComfyUIProviderTests(unittest.TestCase):
    def test_workflow_placeholders_and_node_overrides(self):
        workflow = {
            "6": {
                "class_type": "CLIPTextEncode",
                "inputs": {"text": "old positive"},
                "_meta": {"title": "Positive Prompt"},
            },
            "7": {
                "class_type": "CLIPTextEncode",
                "inputs": {"text": "old negative"},
                "_meta": {"title": "Negative Prompt"},
            },
            "10": {
                "class_type": "VideoLatent",
                "inputs": {
                    "width": "{{WIDTH}}",
                    "height": "{{HEIGHT}}",
                    "length": "{{FRAMES}}",
                    "fps": "{{FPS}}",
                },
            },
            "11": {
                "class_type": "Sampler",
                "inputs": {"seed": "{{SEED}}", "label": "job={{JOB_ID}}"},
            },
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "workflow.json"
            path.write_text(json.dumps(workflow), encoding="utf-8")
            env = {
                "ZMOVIE_COMFYUI_WORKFLOW": str(path),
                "ZMOVIE_COMFYUI_FPS": "16",
                "ZMOVIE_COMFYUI_FRAME_MULTIPLE": "4",
                "ZMOVIE_COMFYUI_FRAME_OFFSET": "1",
            }
            with patch.dict(os.environ, env, clear=False):
                adapted, resolved = COMFYUI._load_workflow(
                    "cinematic positive prompt",
                    "bad anatomy",
                    {"job_id": "job-1", "project_id": "p-1", "shot_id": "s-1", "duration_seconds": 5, "aspect_ratio": "16:9"},
                )

        self.assertEqual(adapted["6"]["inputs"]["text"], "cinematic positive prompt")
        self.assertEqual(adapted["7"]["inputs"]["text"], "bad anatomy")
        self.assertEqual(adapted["10"]["inputs"]["width"], 1280)
        self.assertEqual(adapted["10"]["inputs"]["height"], 720)
        self.assertEqual(adapted["10"]["inputs"]["length"], 81)
        self.assertEqual(adapted["10"]["inputs"]["fps"], 16)
        self.assertIsInstance(adapted["11"]["inputs"]["seed"], int)
        self.assertEqual(adapted["11"]["inputs"]["label"], "job=job-1")
        self.assertEqual(resolved["FRAMES"], 81)

    def test_history_compatibility_shapes(self):
        prompt_id = "abc"
        legacy = {prompt_id: {"outputs": {"1": {"videos": [{"filename": "movie.mp4", "subfolder": "", "type": "output"}]}}}}
        entry = COMFYUI._history_entry(legacy, prompt_id)
        self.assertIsNotNone(entry)
        refs = []
        COMFYUI._collect_output_refs(entry["outputs"], refs)
        self.assertEqual(refs[0]["filename"], "movie.mp4")

        modern = {"history": [{"prompt_id": prompt_id, "outputs": {}}]}
        self.assertEqual(COMFYUI._history_entry(modern, prompt_id)["outputs"], {})

    def test_provider_capability_reports_configuration(self):
        with tempfile.TemporaryDirectory() as tmp:
            workflow = Path(tmp) / "workflow.json"
            workflow.write_text("{}", encoding="utf-8")
            with patch.dict(os.environ, {"ZMOVIE_COMFYUI_WORKFLOW": str(workflow)}, clear=False):
                specs = {item["id"]: item for item in provider_specs()}
                self.assertIn("comfyui", specs)
                self.assertTrue(specs["comfyui"]["configured"])


if __name__ == "__main__":
    unittest.main()
