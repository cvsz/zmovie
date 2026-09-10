from __future__ import annotations

import json
import mimetypes
import urllib.error
import urllib.request
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .providers import ComfyUIProvider


@dataclass(frozen=True)
class ZFlowI2VJob:
    """Provider-neutral image-to-video request used by zMovie product campaigns."""

    source_image: Path
    prompt: str
    negative_prompt: str = ""
    aspect_ratio: str = "9:16"
    duration_seconds: int = 5
    output_dir: Path = Path("data/zflow")
    project_id: str = "zflow"
    shot_id: str = "i2v"

    def validate(self) -> None:
        if not self.source_image.is_file():
            raise FileNotFoundError(f"source image not found: {self.source_image}")
        if self.aspect_ratio not in {"16:9", "9:16", "1:1", "21:9"}:
            raise ValueError(f"unsupported aspect ratio: {self.aspect_ratio}")
        if self.duration_seconds not in {5, 10, 20}:
            raise ValueError("duration_seconds must be one of 5, 10, 20")
        if not self.prompt.strip():
            raise ValueError("prompt must not be empty")


class ZFlowComfyUIProvider(ComfyUIProvider):
    """ComfyUI-compatible I2V provider with explicit source-image binding."""

    @staticmethod
    def _multipart_image(path: Path, boundary: str) -> bytes:
        filename = path.name.replace('"', "_")
        content_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"
        parts = [
            f"--{boundary}\r\n".encode(),
            f'Content-Disposition: form-data; name="image"; filename="{filename}"\r\n'.encode(),
            f"Content-Type: {content_type}\r\n\r\n".encode(),
            path.read_bytes(),
            b"\r\n",
            f"--{boundary}\r\n".encode(),
            b'Content-Disposition: form-data; name="type"\r\n\r\ninput\r\n',
            f"--{boundary}\r\n".encode(),
            b'Content-Disposition: form-data; name="overwrite"\r\n\r\ntrue\r\n',
            f"--{boundary}--\r\n".encode(),
        ]
        return b"".join(parts)

    def upload_input_image(self, path: Path) -> str:
        path = path.expanduser().resolve()
        if not path.is_file():
            raise FileNotFoundError(f"source image not found: {path}")
        boundary = "----zflow-" + uuid.uuid4().hex
        request = urllib.request.Request(
            self._base_url() + "/upload/image",
            data=self._multipart_image(path, boundary),
            method="POST",
            headers={**self._headers(), "Content-Type": f"multipart/form-data; boundary={boundary}"},
        )
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"ComfyUI image upload failed HTTP {exc.code}: {detail[:1200]}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"ComfyUI unavailable at {self._base_url()}: {exc.reason}") from exc
        if not isinstance(payload, dict) or not payload.get("name"):
            raise RuntimeError(f"ComfyUI image upload returned invalid response: {payload!r}")
        name = str(payload["name"])
        subfolder = str(payload.get("subfolder", "")).strip("/")
        return f"{subfolder}/{name}" if subfolder else name

    @staticmethod
    def _bind_image_fallback(workflow: dict[str, Any], image_name: str) -> int:
        changed = 0
        for node in workflow.values():
            if not isinstance(node, dict) or not isinstance(node.get("inputs"), dict):
                continue
            inputs = node["inputs"]
            title = str((node.get("_meta") or {}).get("title", "")).lower()
            class_type = str(node.get("class_type", "")).lower()
            if "image" not in inputs:
                continue
            if "loadimage" in class_type or any(token in title for token in ("input image", "source image", "reference image")):
                inputs["image"] = image_name
                changed += 1
        return changed

    def _load_workflow(self, prompt: str, negative_prompt: str, metadata: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
        workflow, values = super()._load_workflow(prompt, negative_prompt, metadata)
        image_name = str(metadata.get("input_image", "")).strip()
        if not image_name:
            raise RuntimeError("ZeaZFlow image-to-video requires metadata.input_image")

        workflow = self._replace_placeholders(workflow, {"INPUT_IMAGE": image_name, "SOURCE_IMAGE": image_name})
        node_ids = self._node_ids("ZMOVIE_COMFYUI_IMAGE_NODE_IDS")
        changed = self._set_input(workflow, node_ids, ("image",), image_name)
        changed += self._bind_image_fallback(workflow, image_name)
        serialized = json.dumps(workflow)
        if changed == 0 and image_name not in serialized:
            raise RuntimeError(
                "source image was not bound to the ComfyUI workflow; add {{INPUT_IMAGE}} "
                "to a LoadImage node or set ZMOVIE_COMFYUI_IMAGE_NODE_IDS"
            )
        values["INPUT_IMAGE"] = image_name
        return workflow, values

    def run_i2v(self, job: ZFlowI2VJob, *, job_id: str | None = None) -> dict[str, Any]:
        job.validate()
        resolved_job_id = job_id or uuid.uuid4().hex
        uploaded = self.upload_input_image(job.source_image)
        metadata = {
            "job_id": resolved_job_id,
            "project_id": job.project_id,
            "shot_id": job.shot_id,
            "duration_seconds": job.duration_seconds,
            "aspect_ratio": job.aspect_ratio,
            "mode": "image-to-video",
            "input_image": uploaded,
        }
        result = self.submit(
            prompt=job.prompt,
            negative_prompt=job.negative_prompt,
            output_dir=job.output_dir,
            metadata=metadata,
        )
        if result.get("kind") != "video":
            raise RuntimeError(f"I2V workflow completed without a video output: {result.get('output_path')}")
        return {**result, "input_image": uploaded, "job_id": resolved_job_id, "mode": "image-to-video"}


def product_ad_prompt(variant: int = 1, *, price_mode: str = "discount10") -> str:
    if price_mode == "full":
        price = "Final price card: THB 34,990. Do not claim a discount."
    elif price_mode == "discount10":
        price = (
            "Campaign price card: regular THB 34,990; exact 10% reduction THB 31,491. "
            "Use this only when the merchant authorizes the campaign."
        )
    else:
        raise ValueError("price_mode must be 'full' or 'discount10'")

    motions = {
        1: "slow premium orbit, controlled push-in, crisp spec cards",
        2: "fast gaming reveal, energetic parallax, sharp macro detail cuts",
        3: "minimal luxury product turntable, elegant light sweep, clean typography",
    }
    motion = motions.get(variant, motions[1])
    return (
        "Vertical 9:16 ecommerce video for Lenovo LOQ 15ARP10E, photorealistic and faithful to the source product image. "
        f"Motion language: {motion}. "
        "Dark premium gaming studio with subtle purple-magenta accents. Show Ryzen 7 170 8C/16T, RTX 4050 6GB, "
        "16GB DDR5-4800, 512GB PCIe 4 NVMe, 15.6-inch FHD IPS 144Hz 100% sRGB, Wi-Fi 6, HDMI 2.1, USB-C PD, "
        "and 2Y Premium Care Onsite as concise readable cards. "
        f"{price} End with a clean Thai purchase CTA. Preserve logo, ports, chassis geometry and screen proportions. "
        "No fabricated FPS, benchmarks, stock scarcity, gifts, discounts, or unsupported specifications."
    )
