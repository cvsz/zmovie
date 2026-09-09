from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

from . import providers as provider_module
from .providers import PROVIDERS, ProviderSpec


def _flag(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() not in {"", "0", "false", "no", "off"}


class StableDiffusionCppProvider:
    """Local stable-diffusion.cpp video provider.

    The provider deliberately does not download model weights. Operators install
    the inference engine separately, configure a video-capable model bundle, and
    explicitly enable video mode. Runtime output still has to pass zMovie's
    ffprobe production-media gate before it can be assembled or published.
    """

    spec = ProviderSpec(
        id="sdcpp",
        name="stable-diffusion.cpp / CPU + Vulkan",
        modes=("text-to-video",),
        durations=(5, 10, 20),
        aspect_ratios=("16:9", "9:16", "1:1", "21:9"),
        description=(
            "Runs stable-diffusion.cpp sd-cli locally in vid_gen mode. Backend "
            "selection can prefer Vulkan/iGPU and fall back to CPU without CUDA."
        ),
    )

    MODEL_ARGS: tuple[tuple[str, str], ...] = (
        ("ZMOVIE_SDCPP_MODEL", "-m"),
        ("ZMOVIE_SDCPP_DIFFUSION_MODEL", "--diffusion-model"),
        ("ZMOVIE_SDCPP_HIGH_NOISE_DIFFUSION_MODEL", "--high-noise-diffusion-model"),
        ("ZMOVIE_SDCPP_VAE", "--vae"),
        ("ZMOVIE_SDCPP_AUDIO_VAE", "--audio-vae"),
        ("ZMOVIE_SDCPP_T5XXL", "--t5xxl"),
        ("ZMOVIE_SDCPP_LLM", "--llm"),
        ("ZMOVIE_SDCPP_CLIP_VISION", "--clip_vision"),
        ("ZMOVIE_SDCPP_EMBEDDINGS_CONNECTORS", "--embeddings-connectors"),
    )

    _LONG_DYNAMIC_FLAGS = {
        "--output",
        "--prompt",
        "--negative-prompt",
        "--width",
        "--height",
        "--video-frames",
        "--fps",
        "--backend",
        "--mode",
        "--seed",
    }
    _SHORT_DYNAMIC_FLAGS = ("-o", "-p", "-n", "-W", "-H", "-M", "-s")

    def _cli(self) -> str:
        configured = os.getenv("ZMOVIE_SDCPP_CLI", "").strip()
        if configured:
            if "/" in configured:
                candidate = Path(configured).expanduser()
                if candidate.is_file() and os.access(candidate, os.X_OK):
                    return str(candidate)
                return ""
            return shutil.which(configured) or ""
        return shutil.which("sd-cli") or ""

    def _backend(self) -> str:
        value = os.getenv("ZMOVIE_SDCPP_BACKEND", "auto").strip().lower() or "auto"
        if value not in {"auto", "cpu", "gpu"} and not value.startswith(("vulkan", "cuda", "metal", "sycl")):
            raise RuntimeError(f"unsupported ZMOVIE_SDCPP_BACKEND: {value}")
        return value

    @staticmethod
    def _model_path(raw: str) -> Path:
        return Path(raw).expanduser().resolve()

    def _model_arguments(self) -> tuple[list[str], list[str], bool]:
        args: list[str] = []
        missing: list[str] = []
        primary = False
        for env_name, flag in self.MODEL_ARGS:
            raw = os.getenv(env_name, "").strip()
            if not raw:
                continue
            path = self._model_path(raw)
            if not path.is_file():
                missing.append(env_name.removeprefix("ZMOVIE_SDCPP_").lower())
                continue
            if env_name in {"ZMOVIE_SDCPP_MODEL", "ZMOVIE_SDCPP_DIFFUSION_MODEL"}:
                primary = True
            args.extend((flag, str(path)))
        if not primary:
            missing.append("model_or_diffusion_model")
        return args, sorted(set(missing)), primary

    def _extra_arguments(self) -> list[str]:
        raw = os.getenv("ZMOVIE_SDCPP_EXTRA_ARGS_JSON", "").strip()
        if not raw:
            return []
        try:
            value = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise RuntimeError("ZMOVIE_SDCPP_EXTRA_ARGS_JSON must be valid JSON") from exc
        if not isinstance(value, list) or not all(isinstance(item, str) and item for item in value):
            raise RuntimeError("ZMOVIE_SDCPP_EXTRA_ARGS_JSON must be a JSON array of non-empty strings")
        for item in value:
            if item in self._LONG_DYNAMIC_FLAGS or any(item.startswith(flag + "=") for flag in self._LONG_DYNAMIC_FLAGS):
                raise RuntimeError(f"stable-diffusion.cpp extra args cannot override zMovie-controlled flag: {item}")
            if item in self._SHORT_DYNAMIC_FLAGS or any(
                item.startswith(flag) and item != flag for flag in self._SHORT_DYNAMIC_FLAGS
            ):
                raise RuntimeError(f"stable-diffusion.cpp extra args cannot override zMovie-controlled flag: {item}")
        return list(value)

    @staticmethod
    def _dimensions(aspect_ratio: str) -> tuple[int, int]:
        defaults = {
            "16:9": (832, 480),
            "9:16": (480, 832),
            "1:1": (512, 512),
            "21:9": (896, 384),
        }
        width, height = defaults.get(aspect_ratio, defaults["16:9"])
        if os.getenv("ZMOVIE_SDCPP_WIDTH", "").strip():
            width = int(os.environ["ZMOVIE_SDCPP_WIDTH"])
        if os.getenv("ZMOVIE_SDCPP_HEIGHT", "").strip():
            height = int(os.environ["ZMOVIE_SDCPP_HEIGHT"])
        if width < 64 or height < 64 or width > 4096 or height > 4096:
            raise RuntimeError("stable-diffusion.cpp dimensions must be between 64 and 4096 pixels")
        return width, height

    @staticmethod
    def _frames(duration: int, fps: int) -> int:
        raw = max(1, round(duration * fps))
        multiple = max(1, int(os.getenv("ZMOVIE_SDCPP_FRAME_MULTIPLE", "4")))
        offset = int(os.getenv("ZMOVIE_SDCPP_FRAME_OFFSET", "1"))
        remainder = (raw - offset) % multiple
        return raw if remainder == 0 else raw + (multiple - remainder)

    @staticmethod
    def _seed(prompt: str, job_id: str) -> int:
        configured = os.getenv("ZMOVIE_SDCPP_SEED", "").strip()
        if configured:
            return int(configured)
        digest = hashlib.sha256(f"{job_id}\0{prompt}".encode()).digest()
        return int.from_bytes(digest[:8], "big") & 0x7FFFFFFF

    def runtime_status(self, *, probe_devices: bool = True) -> dict[str, Any]:
        cli = self._cli()
        model_args, missing, primary = self._model_arguments()
        video_enabled = _flag("ZMOVIE_SDCPP_VIDEO_ENABLED", False)
        ffmpeg = bool(shutil.which("ffmpeg"))
        ffprobe = bool(shutil.which("ffprobe"))
        devices: list[str] = []
        probe_error = ""
        if cli and probe_devices:
            try:
                proc = subprocess.run(
                    [cli, "--list-devices"],
                    capture_output=True,
                    text=True,
                    timeout=15,
                    check=False,
                )
                text = "\n".join(part for part in (proc.stdout, proc.stderr) if part)
                devices = [line.strip()[:240] for line in text.splitlines() if line.strip()][:32]
                if proc.returncode != 0:
                    probe_error = f"list_devices_exit_{proc.returncode}"
            except (OSError, subprocess.TimeoutExpired) as exc:
                probe_error = type(exc).__name__
        lowered = " ".join(devices).lower()
        vulkan_available = "vulkan" in lowered
        cpu_available = "cpu" in lowered or bool(cli)
        production_ready = bool(
            cli
            and primary
            and not missing
            and video_enabled
            and ffmpeg
            and ffprobe
        )
        reasons: list[str] = []
        if not cli:
            reasons.append("sd_cli_missing")
        if not primary:
            reasons.append("video_model_not_configured")
        if missing and primary:
            reasons.append("model_files_missing:" + ",".join(missing))
        if not video_enabled:
            reasons.append("video_mode_not_enabled")
        if not ffmpeg:
            reasons.append("ffmpeg_required")
        if not ffprobe:
            reasons.append("ffprobe_required")
        if probe_error:
            reasons.append("device_probe_failed:" + probe_error)
        return {
            "configured": production_ready,
            "production_ready": production_ready,
            "cli_available": bool(cli),
            "video_enabled": video_enabled,
            "model_configured": primary,
            "model_files_valid": primary and not missing,
            "backend": self._backend(),
            "vulkan_available": vulkan_available,
            "cpu_available": cpu_available,
            "devices": devices,
            "ffmpeg": ffmpeg,
            "ffprobe": ffprobe,
            "reasons": reasons,
            "model_argument_count": len(model_args) // 2,
        }

    def configured(self) -> bool:
        return bool(self.runtime_status(probe_devices=False)["production_ready"])

    def submit(
        self,
        *,
        prompt: str,
        negative_prompt: str,
        output_dir: Path,
        metadata: dict[str, Any],
    ) -> dict[str, Any]:
        status = self.runtime_status(probe_devices=False)
        if not status["production_ready"]:
            raise RuntimeError(
                "stable-diffusion.cpp is not production-ready: "
                + ", ".join(str(item) for item in status["reasons"])
            )
        cli = self._cli()
        if not cli:
            raise RuntimeError("stable-diffusion.cpp sd-cli is unavailable")
        model_args, missing, _ = self._model_arguments()
        if missing:
            raise RuntimeError("stable-diffusion.cpp model files are missing")

        duration = max(1, int(metadata.get("duration_seconds", 5)))
        aspect = str(metadata.get("aspect_ratio", "16:9"))
        fps = max(1, min(60, int(os.getenv("ZMOVIE_SDCPP_FPS", "8"))))
        frames = self._frames(duration, fps)
        width, height = self._dimensions(aspect)
        seed = self._seed(prompt, str(metadata["job_id"]))
        output_format = os.getenv("ZMOVIE_SDCPP_OUTPUT_FORMAT", "avi").strip().lower() or "avi"
        if output_format not in {"avi", "webm"}:
            raise RuntimeError("ZMOVIE_SDCPP_OUTPUT_FORMAT must be avi or webm")

        job_dir = output_dir / str(metadata["job_id"])
        job_dir.mkdir(parents=True, exist_ok=True)
        target = job_dir / f"video.{output_format}"
        target.unlink(missing_ok=True)

        command = [
            cli,
            "-M",
            "vid_gen",
            *model_args,
            "-p",
            prompt,
            "-n",
            negative_prompt,
            "-W",
            str(width),
            "-H",
            str(height),
            "--video-frames",
            str(frames),
            "--fps",
            str(fps),
            "--backend",
            self._backend(),
            "-s",
            str(seed),
        ]
        params_backend = os.getenv("ZMOVIE_SDCPP_PARAMS_BACKEND", "").strip()
        if params_backend:
            command.extend(("--params-backend", params_backend))
        max_vram = os.getenv("ZMOVIE_SDCPP_MAX_VRAM", "").strip()
        if max_vram:
            command.extend(("--max-vram", max_vram))
        if _flag("ZMOVIE_SDCPP_AUTO_FIT", False):
            command.append("--auto-fit")
        command.extend(self._extra_arguments())
        command.extend(("-o", str(target)))

        timeout = max(60, int(os.getenv("ZMOVIE_SDCPP_TIMEOUT", "21600")))
        try:
            proc = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError(f"stable-diffusion.cpp render timed out after {timeout}s") from exc
        except OSError as exc:
            raise RuntimeError(f"failed to execute stable-diffusion.cpp: {exc}") from exc
        if proc.returncode != 0:
            detail = (proc.stderr or proc.stdout or "unknown sd-cli failure")[-1800:]
            raise RuntimeError(f"stable-diffusion.cpp exited {proc.returncode}: {detail}")
        if not target.is_file() or target.stat().st_size <= 0:
            raise RuntimeError("stable-diffusion.cpp completed without creating the requested video output")
        return {
            "status": "completed",
            "output_path": str(target),
            "kind": "video",
            "backend": self._backend(),
            "fps": fps,
            "frames": frames,
            "width": width,
            "height": height,
            "seed": seed,
            "engine": "stable-diffusion.cpp",
        }


SDCPP = StableDiffusionCppProvider()


def _register_provider() -> None:
    """Register without forcing the core providers module to depend on this optional engine."""
    PROVIDERS[SDCPP.spec.id] = SDCPP
    original = provider_module._configured
    if getattr(original, "_zmovie_sdcpp_extended", False):
        return

    def configured_with_sdcpp(provider_id: str) -> bool:
        if provider_id == SDCPP.spec.id:
            return SDCPP.configured()
        return original(provider_id)

    configured_with_sdcpp._zmovie_sdcpp_extended = True  # type: ignore[attr-defined]
    provider_module._configured = configured_with_sdcpp


_register_provider()
