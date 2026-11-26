"""Cloud free video provider via generic webhook (e.g. Colab/Kaggle ComfyUI).

Sends render requests to a self-hosted ComfyUI running on a free cloud GPU
(Google Colab, Kaggle Kernels, etc.) exposed through ngrok or similar tunneling.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import httpx

from ._provider_spec import ProviderSpec


class CloudWebhookProvider:
    """Cloud video provider via generic webhook (Colab/Kaggle ComfyUI)."""

    spec = ProviderSpec(
        id="cloud-webhook",
        name="Cloud Free Video (Webhook)",
        modes=("text-to-video", "image-to-video"),
        durations=(5, 10, 20),
        aspect_ratios=("16:9", "9:16", "1:1"),
        description=(
            "Submits render jobs to a self-hosted ComfyUI on a free cloud GPU "
            "(Google Colab, Kaggle Kernels) exposed via webhook. Requires "
            "ZMOVIE_PROVIDER_WEBHOOK to be set."
        ),
    )

    def __init__(self) -> None:
        self.endpoint = os.getenv("ZMOVIE_PROVIDER_WEBHOOK", "").strip()
        self.token = os.getenv("ZMOVIE_PROVIDER_TOKEN", "").strip()
        self.timeout = int(os.getenv("ZMOVIE_PROVIDER_TIMEOUT", "300"))

    def is_available(self) -> bool:
        return bool(self.endpoint)

    def enabled(self) -> bool:
        return self.is_available()

    def submit(self, *, prompt: str, negative_prompt: str, output_dir: Path, metadata: dict[str, Any]) -> dict[str, Any]:
        if not self.enabled():
            raise RuntimeError("Cloud webhook provider is not enabled (ZMOVIE_PROVIDER_WEBHOOK not set)")

        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        payload = {
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "output_dir": str(output_dir),
            "metadata": metadata,
        }

        with httpx.Client(timeout=self.timeout) as client:
            resp = client.post(self.endpoint, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()

        if not isinstance(data, dict) or not data.get("output_path"):
            raise RuntimeError(f"Cloud webhook returned invalid response: {data!r}")

        return {
            "status": "completed",
            "output_path": str(data["output_path"]),
            "kind": str(data.get("kind", "video")),
            "outputs": data.get("outputs", []),
            "provider": "cloud-webhook",
        }
