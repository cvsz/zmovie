import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from zmovie_platform.providers import provider_specs
from zmovie_platform.sdcpp_provider import SDCPP


class StableDiffusionCppProviderTests(unittest.TestCase):
    def _fixture(self, root: Path) -> tuple[Path, Path]:
        cli = root / "sd-cli"
        cli.write_text(
            """#!/usr/bin/env bash
set -e
if [[ ${1:-} == --list-devices ]]; then
  echo 'vulkan0 AMD Radeon test device'
  echo 'cpu CPU'
  exit 0
fi
out=''
while [[ $# -gt 0 ]]; do
  if [[ $1 == -o ]]; then out=$2; shift 2; continue; fi
  shift
done
[[ -n $out ]]
printf 'fake-video-container' > "$out"
""",
            encoding="utf-8",
        )
        cli.chmod(0o755)
        model = root / "video-model.gguf"
        model.write_bytes(b"model")
        return cli, model

    @staticmethod
    def _which(name: str) -> str | None:
        if name == "ffmpeg":
            return "/usr/bin/ffmpeg"
        if name == "ffprobe":
            return "/usr/bin/ffprobe"
        return None

    def test_runtime_status_accepts_cpu_vulkan_video_bundle(self):
        with tempfile.TemporaryDirectory() as temp:
            cli, model = self._fixture(Path(temp))
            env = {
                "ZMOVIE_SDCPP_CLI": str(cli),
                "ZMOVIE_SDCPP_DIFFUSION_MODEL": str(model),
                "ZMOVIE_SDCPP_VIDEO_ENABLED": "true",
                "ZMOVIE_SDCPP_BACKEND": "auto",
            }
            with patch.dict(os.environ, env, clear=False), patch(
                "zmovie_platform.sdcpp_provider.shutil.which", side_effect=self._which
            ):
                status = SDCPP.runtime_status(probe_devices=True)
        self.assertTrue(status["production_ready"])
        self.assertTrue(status["vulkan_available"])
        self.assertTrue(status["cpu_available"])
        self.assertEqual(status["backend"], "auto")

    def test_submit_uses_managed_dynamic_output_and_returns_video(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            cli, model = self._fixture(root)
            output = root / "renders"
            env = {
                "ZMOVIE_SDCPP_CLI": str(cli),
                "ZMOVIE_SDCPP_DIFFUSION_MODEL": str(model),
                "ZMOVIE_SDCPP_VIDEO_ENABLED": "true",
                "ZMOVIE_SDCPP_BACKEND": "cpu",
                "ZMOVIE_SDCPP_OUTPUT_FORMAT": "avi",
                "ZMOVIE_SDCPP_FPS": "8",
            }
            with patch.dict(os.environ, env, clear=False), patch(
                "zmovie_platform.sdcpp_provider.shutil.which", side_effect=self._which
            ):
                result = SDCPP.submit(
                    prompt="a controlled cinematic test",
                    negative_prompt="artifacts",
                    output_dir=output,
                    metadata={
                        "job_id": "job_test",
                        "project_id": "prj_test",
                        "shot_id": "shot_test",
                        "duration_seconds": 5,
                        "aspect_ratio": "16:9",
                    },
                )
                target = Path(result["output_path"])
                self.assertTrue(target.is_file())
                self.assertEqual(target.parent, output / "job_test")
                self.assertEqual(target.suffix, ".avi")
                self.assertEqual(result["kind"], "video")
                self.assertEqual(result["backend"], "cpu")

    def test_video_mode_is_fail_closed_until_explicitly_enabled(self):
        with tempfile.TemporaryDirectory() as temp:
            cli, model = self._fixture(Path(temp))
            env = {
                "ZMOVIE_SDCPP_CLI": str(cli),
                "ZMOVIE_SDCPP_DIFFUSION_MODEL": str(model),
                "ZMOVIE_SDCPP_VIDEO_ENABLED": "false",
            }
            with patch.dict(os.environ, env, clear=False), patch(
                "zmovie_platform.sdcpp_provider.shutil.which", side_effect=self._which
            ):
                status = SDCPP.runtime_status(probe_devices=False)
        self.assertFalse(status["production_ready"])
        self.assertIn("video_mode_not_enabled", status["reasons"])

    def test_extra_args_cannot_override_zmovie_controlled_output_or_backend(self):
        with patch.dict(
            os.environ,
            {"ZMOVIE_SDCPP_EXTRA_ARGS_JSON": '["--backend","cpu"]'},
            clear=False,
        ):
            with self.assertRaises(RuntimeError):
                SDCPP._extra_arguments()
        with patch.dict(
            os.environ,
            {"ZMOVIE_SDCPP_EXTRA_ARGS_JSON": '["--output=/tmp/escape.avi"]'},
            clear=False,
        ):
            with self.assertRaises(RuntimeError):
                SDCPP._extra_arguments()

    def test_provider_registration_is_visible_to_catalog(self):
        ids = [item["id"] for item in provider_specs()]
        self.assertIn("sdcpp", ids)
        self.assertEqual(ids.count("sdcpp"), 1)


if __name__ == "__main__":
    unittest.main()
