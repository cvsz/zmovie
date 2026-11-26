"""Hugging Face Inference API provider (free tier) for video generation.

Uses Hugging Face Inference API to generate video from open-weight models
such as CogVideoX, Stable Video Diffusion, etc. Free tier has rate limits
but requires no GPU management.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import httpx

from ._provider_spec import ProviderSpec


class HuggingFaceVideoProvider:
    """Hugging Face Inference API provider (free tier) for video generation."""

    spec = ProviderSpec(
        id="huggingface",
        name="Hugging Face Inference API (Free)",
        modes=("text-to-video", "image-to-video"),
        durations=(5, 10, 20),
        aspect_ratios=("16:9", "9:16", "1:1"),
        description=(
            "Generates video via Hugging Face Inference API using open-weight "
            "video models (CogVideoX, Stable Video Diffusion, etc.). Free tier "
            "requires ZMOVIE_HF_API_KEY and ZMOVIE_HF_MODEL."
        ),
    )

    def __init__(self) -> None:
        self.api_key = os.getenv("ZMOVIE_HF_API_KEY", "").strip()
        self.model = os.getenv("ZMOVIE_HF_MODEL", "").strip()
        self.api_base = os.getenv("ZMOVIE_HF_API_BASE", "https://api-inference.huggingface.co/models").strip()
        self.timeout = int(os.getenv("ZMOVIE_HF_TIMEOUT", "300"))

    def is_available(self) -> bool:
        return bool(self.api_key and self.model)

    def enabled(self) -> bool:
        return self.is_available()

    def submit(self, *, prompt: str, negative_prompt: str, output_dir: Path, metadata: dict[str, Any]) -> dict[str, Any]:
        if not self.enabled():
            raise RuntimeError(
                "Hugging Face provider is not enabled "
                "(ZMOVIE_HF_API_KEY and ZMOVIE_HF_MODEL required)"
            )

        headers = {"Authorization": f"Bearer {self.api_key}"}
        payload = {
            "inputs": prompt,
            "parameters": {
                "negative_prompt": negative_prompt,
                "num_inference_steps": int(metadata.get("num_inference_steps", 20)),
                "guidance_scale": float(metadata.get("guidance_scale", 7.5)),
                "width": int(metadata.get("width", 720)),
                "height": int(metadata.get("height", 1280)),
                "num_frames": int(metadata.get("num_frames", 49)),
                "fps": int(metadata.get("fps", 16)),
            },
        }

        output_dir.mkdir(parents=True, exist_ok=True)
        target = output_dir / f"{metadata.get('job_id', 'job')}.mp4"

        url = f"{self.api_base}/{self.model}"
        with httpx.Client(timeout=self.timeout) as client:
            resp = client.post(url, headers=headers, json=payload)
            if resp.status_code == 503:
                raise RuntimeError("Hugging Face model is loading, retry later")
            resp.raise_for_status()
            content = resp.content

        target.write_bytes(content)
        if not target.is_file() or target.stat().st_size == 0:
            raise RuntimeError("Hugging Face returned empty video output")

        return {
            "status": "completed",
            "output_path": str(target),
            "kind": "video",
            "outputs": [str(target)],
            "provider": "huggingface",
        }
