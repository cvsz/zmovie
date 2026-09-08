from __future__ import annotations

import json
import os
import shutil
import subprocess
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol


@dataclass(frozen=True)
class ProviderSpec:
    id: str
    name: str
    modes: tuple[str, ...]
    durations: tuple[int, ...]
    aspect_ratios: tuple[str, ...]
    description: str


class VideoProvider(Protocol):
    spec: ProviderSpec

    def submit(self, *, prompt: str, negative_prompt: str, output_dir: Path, metadata: dict[str, Any]) -> dict[str, Any]: ...


class MockProvider:
    spec = ProviderSpec(
        id="mock",
        name="Local Mock / Production Dry Run",
        modes=("text-to-video",),
        durations=(5, 10, 20),
        aspect_ratios=("16:9", "9:16", "1:1"),
        description="Creates a deterministic placeholder MP4 when ffmpeg is available; otherwise writes render metadata. No external API required.",
    )

    def submit(self, *, prompt: str, negative_prompt: str, output_dir: Path, metadata: dict[str, Any]) -> dict[str, Any]:
        output_dir.mkdir(parents=True, exist_ok=True)
        job_id = str(metadata["job_id"])
        duration = int(metadata.get("duration_seconds", 5))
        target = output_dir / f"{job_id}.mp4"
        meta_path = output_dir / f"{job_id}.json"
        meta_path.write_text(json.dumps({"prompt": prompt, "negative_prompt": negative_prompt, **metadata}, ensure_ascii=False, indent=2), encoding="utf-8")
        ffmpeg = shutil.which("ffmpeg")
        if not ffmpeg:
            return {"status": "completed", "output_path": str(meta_path), "kind": "metadata", "note": "ffmpeg unavailable"}
        command = [
            ffmpeg, "-y", "-f", "lavfi", "-i", f"color=c=black:s=1280x720:d={duration}",
            "-vf", "drawtext=text='zMovie render placeholder':fontcolor=white:fontsize=42:x=(w-text_w)/2:y=(h-text_h)/2",
            "-r", "24", "-pix_fmt", "yuv420p", str(target),
        ]
        proc = subprocess.run(command, capture_output=True, text=True, timeout=max(60, duration * 4))
        if proc.returncode != 0:
            # Some ffmpeg builds lack drawtext. Retry without it.
            command = [ffmpeg, "-y", "-f", "lavfi", "-i", f"color=c=black:s=1280x720:d={duration}", "-r", "24", "-pix_fmt", "yuv420p", str(target)]
            proc = subprocess.run(command, capture_output=True, text=True, timeout=max(60, duration * 4))
        if proc.returncode != 0:
            raise RuntimeError(proc.stderr[-1000:])
        return {"status": "completed", "output_path": str(target), "kind": "video"}


class GenericWebhookProvider:
    spec = ProviderSpec(
        id="webhook",
        name="Generic HTTP Video Provider",
        modes=("text-to-video", "image-to-video"),
        durations=(5, 10, 20),
        aspect_ratios=("16:9", "9:16", "1:1"),
        description="Submits JSON to ZMOVIE_PROVIDER_WEBHOOK. Useful for Wan/Kling/Veo gateways or a self-hosted renderer.",
    )

    def submit(self, *, prompt: str, negative_prompt: str, output_dir: Path, metadata: dict[str, Any]) -> dict[str, Any]:
        endpoint = os.getenv("ZMOVIE_PROVIDER_WEBHOOK", "").strip()
        if not endpoint:
            raise RuntimeError("ZMOVIE_PROVIDER_WEBHOOK is not configured")
        token = os.getenv("ZMOVIE_PROVIDER_TOKEN", "").strip()
        payload = json.dumps({"prompt": prompt, "negative_prompt": negative_prompt, **metadata}).encode("utf-8")
        request = urllib.request.Request(endpoint, data=payload, method="POST", headers={"Content-Type": "application/json"})
        if token:
            request.add_header("Authorization", f"Bearer {token}")
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                data = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"provider HTTP {exc.code}: {body[:1000]}") from exc
        if not isinstance(data, dict):
            raise RuntimeError("provider response must be a JSON object")
        return data


PROVIDERS: dict[str, VideoProvider] = {
    "mock": MockProvider(),
    "webhook": GenericWebhookProvider(),
}


def get_provider(provider_id: str) -> VideoProvider:
    try:
        return PROVIDERS[provider_id]
    except KeyError as exc:
        raise ValueError(f"unknown provider: {provider_id}") from exc


def provider_specs() -> list[dict[str, Any]]:
    return [
        {
            "id": p.spec.id,
            "name": p.spec.name,
            "modes": list(p.spec.modes),
            "durations": list(p.spec.durations),
            "aspect_ratios": list(p.spec.aspect_ratios),
            "description": p.spec.description,
        }
        for p in PROVIDERS.values()
    ]
