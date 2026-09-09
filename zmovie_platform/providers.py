from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
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
        proc = subprocess.run(command, capture_output=True, text=True, timeout=max(60, duration * 4), check=False)
        if proc.returncode != 0:
            command = [ffmpeg, "-y", "-f", "lavfi", "-i", f"color=c=black:s=1280x720:d={duration}", "-r", "24", "-pix_fmt", "yuv420p", str(target)]
            proc = subprocess.run(command, capture_output=True, text=True, timeout=max(60, duration * 4), check=False)
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
            raise TypeError("provider response must be a JSON object")
        return data


class ComfyUIProvider:
    """Native self-hosted ComfyUI provider using its API-format workflow contract.

    The workflow must be exported from ComfyUI using the API-format export and
    stored on the zMovie host. String placeholders such as ``{{PROMPT}}`` are
    substituted recursively before the workflow is queued.
    """

    spec = ProviderSpec(
        id="comfyui",
        name="ComfyUI / Local AI Renderer",
        modes=("text-to-video", "image-to-video"),
        durations=(5, 10, 20),
        aspect_ratios=("16:9", "9:16", "1:1", "21:9"),
        description="Queues an API-format workflow on a self-hosted ComfyUI server, waits for execution history, downloads generated outputs, and registers the primary result in zMovie.",
    )

    VIDEO_EXTENSIONS = (".mp4", ".webm", ".mov", ".mkv", ".avi", ".gif", ".webp")
    IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".webp")

    def _base_url(self) -> str:
        value = os.getenv("ZMOVIE_COMFYUI_URL", "http://127.0.0.1:8188").strip().rstrip("/")
        parsed = urllib.parse.urlsplit(value)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise RuntimeError("ZMOVIE_COMFYUI_URL must be an http(s) URL")
        return value

    def _workflow_path(self) -> Path:
        value = os.getenv("ZMOVIE_COMFYUI_WORKFLOW", "").strip()
        if not value:
            raise RuntimeError("ZMOVIE_COMFYUI_WORKFLOW is not configured; export a ComfyUI workflow in API format and set its path")
        path = Path(value).expanduser()
        if not path.is_file():
            raise RuntimeError(f"ComfyUI workflow not found: {path}")
        return path

    def configured(self) -> bool:
        value = os.getenv("ZMOVIE_COMFYUI_WORKFLOW", "").strip()
        return bool(value and Path(value).expanduser().is_file())

    def _headers(self) -> dict[str, str]:
        headers = {"Accept": "application/json"}
        token = os.getenv("ZMOVIE_COMFYUI_TOKEN", "").strip()
        if token:
            headers["Authorization"] = f"Bearer {token}"
        extra = os.getenv("ZMOVIE_COMFYUI_HEADERS_JSON", "").strip()
        if extra:
            try:
                parsed = json.loads(extra)
            except json.JSONDecodeError as exc:
                raise RuntimeError("ZMOVIE_COMFYUI_HEADERS_JSON must be valid JSON") from exc
            if not isinstance(parsed, dict) or not all(isinstance(k, str) and isinstance(v, str) for k, v in parsed.items()):
                raise RuntimeError("ZMOVIE_COMFYUI_HEADERS_JSON must be a JSON object of string headers")
            headers.update(parsed)
        return headers

    def _request_json(self, method: str, path: str, payload: dict[str, Any] | None = None, timeout: float = 30) -> Any:
        body = None
        headers = self._headers()
        if payload is not None:
            body = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"
        request = urllib.request.Request(self._base_url() + path, data=body, method=method, headers=headers)
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                raw = response.read()
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"ComfyUI HTTP {exc.code} for {path}: {detail[:1200]}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"ComfyUI unavailable at {self._base_url()}: {exc.reason}") from exc
        try:
            return json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"ComfyUI returned non-JSON data for {path}") from exc

    @staticmethod
    def _dimensions(aspect_ratio: str) -> tuple[int, int]:
        defaults = {"16:9": (1280, 720), "9:16": (720, 1280), "1:1": (1024, 1024), "21:9": (1344, 576)}
        width, height = defaults.get(aspect_ratio, defaults["16:9"])
        if os.getenv("ZMOVIE_COMFYUI_WIDTH", "").strip():
            width = int(os.environ["ZMOVIE_COMFYUI_WIDTH"])
        if os.getenv("ZMOVIE_COMFYUI_HEIGHT", "").strip():
            height = int(os.environ["ZMOVIE_COMFYUI_HEIGHT"])
        return width, height

    @staticmethod
    def _frames(duration: int, fps: int) -> int:
        raw = max(1, round(duration * fps))
        multiple = max(1, int(os.getenv("ZMOVIE_COMFYUI_FRAME_MULTIPLE", "4")))
        offset = int(os.getenv("ZMOVIE_COMFYUI_FRAME_OFFSET", "1"))
        remainder = (raw - offset) % multiple
        return raw if remainder == 0 else raw + (multiple - remainder)

    @staticmethod
    def _seed(prompt: str, job_id: str) -> int:
        configured = os.getenv("ZMOVIE_COMFYUI_SEED", "").strip()
        if configured:
            return int(configured)
        digest = hashlib.sha256(f"{job_id}\0{prompt}".encode()).digest()
        return int.from_bytes(digest[:8], "big") & ((1 << 63) - 1)

    @staticmethod
    def _replace_placeholders(value: Any, values: dict[str, Any]) -> Any:
        if isinstance(value, dict):
            return {k: ComfyUIProvider._replace_placeholders(v, values) for k, v in value.items()}
        if isinstance(value, list):
            return [ComfyUIProvider._replace_placeholders(v, values) for v in value]
        if not isinstance(value, str):
            return value
        for key, replacement in values.items():
            marker = "{{" + key + "}}"
            if value == marker:
                return replacement
            value = value.replace(marker, str(replacement))
        return value

    @staticmethod
    def _node_ids(name: str) -> list[str]:
        return [part.strip() for part in os.getenv(name, "").split(",") if part.strip()]

    @staticmethod
    def _set_input(workflow: dict[str, Any], node_ids: list[str], keys: tuple[str, ...], value: Any) -> int:
        changed = 0
        for node_id in node_ids:
            node = workflow.get(node_id)
            if not isinstance(node, dict):
                continue
            inputs = node.get("inputs")
            if not isinstance(inputs, dict):
                continue
            key = next((candidate for candidate in keys if candidate in inputs), keys[0])
            inputs[key] = value
            changed += 1
        return changed

    def _load_workflow(self, prompt: str, negative_prompt: str, metadata: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
        try:
            workflow = json.loads(self._workflow_path().read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise RuntimeError("ComfyUI workflow must be valid API-format JSON") from exc
        if not isinstance(workflow, dict) or not workflow:
            raise RuntimeError("ComfyUI API workflow must be a non-empty JSON object")

        duration = max(1, int(metadata.get("duration_seconds", 5)))
        aspect = str(metadata.get("aspect_ratio", "16:9"))
        fps = max(1, int(os.getenv("ZMOVIE_COMFYUI_FPS", "16")))
        width, height = self._dimensions(aspect)
        frames = self._frames(duration, fps)
        seed = self._seed(prompt, str(metadata["job_id"]))
        prefix = os.getenv("ZMOVIE_COMFYUI_FILENAME_PREFIX", "zmovie").strip() or "zmovie"
        prefix = f"{prefix}_{metadata['job_id']}"
        values: dict[str, Any] = {
            "PROMPT": prompt,
            "NEGATIVE_PROMPT": negative_prompt,
            "SEED": seed,
            "WIDTH": width,
            "HEIGHT": height,
            "FRAMES": frames,
            "FPS": fps,
            "DURATION_SECONDS": duration,
            "ASPECT_RATIO": aspect,
            "PREFIX": prefix,
            "JOB_ID": str(metadata["job_id"]),
            "PROJECT_ID": str(metadata.get("project_id", "")),
            "SHOT_ID": str(metadata.get("shot_id", "")),
        }
        workflow = self._replace_placeholders(workflow, values)

        self._set_input(workflow, self._node_ids("ZMOVIE_COMFYUI_POSITIVE_NODE_IDS"), ("text",), prompt)
        self._set_input(workflow, self._node_ids("ZMOVIE_COMFYUI_NEGATIVE_NODE_IDS"), ("text",), negative_prompt)
        self._set_input(workflow, self._node_ids("ZMOVIE_COMFYUI_SEED_NODE_IDS"), ("seed", "noise_seed"), seed)
        self._set_input(workflow, self._node_ids("ZMOVIE_COMFYUI_FRAMES_NODE_IDS"), ("length", "frames", "num_frames", "video_length"), frames)
        self._set_input(workflow, self._node_ids("ZMOVIE_COMFYUI_SIZE_NODE_IDS"), ("width",), width)
        for node_id in self._node_ids("ZMOVIE_COMFYUI_SIZE_NODE_IDS"):
            node = workflow.get(node_id)
            if isinstance(node, dict) and isinstance(node.get("inputs"), dict):
                node["inputs"]["height"] = height

        # Safe convenience fallback: prompt nodes explicitly titled Positive/Negative.
        for node in workflow.values():
            if not isinstance(node, dict) or not isinstance(node.get("inputs"), dict):
                continue
            title = str((node.get("_meta") or {}).get("title", "")).lower()
            inputs = node["inputs"]
            if "text" in inputs and "positive" in title:
                inputs["text"] = prompt
            elif "text" in inputs and "negative" in title:
                inputs["text"] = negative_prompt

        return workflow, values

    @staticmethod
    def _history_entry(payload: Any, prompt_id: str) -> dict[str, Any] | None:
        if not isinstance(payload, dict):
            return None
        direct = payload.get(prompt_id)
        if isinstance(direct, dict):
            return direct
        if isinstance(payload.get("history"), list):
            for item in payload["history"]:
                if isinstance(item, dict) and str(item.get("prompt_id")) == prompt_id:
                    return item
        if str(payload.get("prompt_id", "")) == prompt_id and ("outputs" in payload or "status" in payload):
            return payload
        return None

    @staticmethod
    def _raise_history_error(entry: dict[str, Any]) -> None:
        status = entry.get("status")
        if isinstance(status, dict):
            if str(status.get("status_str", "")).lower() in {"error", "failed"}:
                raise RuntimeError(f"ComfyUI execution failed: {json.dumps(status, ensure_ascii=False)[:1200]}")
            messages = status.get("messages")
            if isinstance(messages, list):
                for message in messages:
                    if isinstance(message, (list, tuple)) and message and str(message[0]).lower() in {"execution_error", "error"}:
                        raise RuntimeError(f"ComfyUI execution failed: {json.dumps(message, ensure_ascii=False)[:1200]}")

    def _wait_for_history(self, prompt_id: str) -> dict[str, Any]:
        timeout = max(10, int(os.getenv("ZMOVIE_COMFYUI_TIMEOUT", "3600")))
        interval = max(0.25, float(os.getenv("ZMOVIE_COMFYUI_POLL_INTERVAL", "2")))
        deadline = time.monotonic() + timeout
        last_error: Exception | None = None
        while time.monotonic() < deadline:
            try:
                payload = self._request_json("GET", "/history/" + urllib.parse.quote(prompt_id, safe=""), timeout=30)
                entry = self._history_entry(payload, prompt_id)
                if entry is not None:
                    self._raise_history_error(entry)
                    return entry
            except RuntimeError as exc:
                last_error = exc
                if "HTTP 404" not in str(exc):
                    raise
            time.sleep(interval)
        suffix = f"; last error: {last_error}" if last_error else ""
        raise RuntimeError(f"ComfyUI job {prompt_id} timed out after {timeout}s{suffix}")

    @staticmethod
    def _collect_output_refs(value: Any, found: list[dict[str, str]]) -> None:
        if isinstance(value, dict):
            if isinstance(value.get("filename"), str):
                found.append({
                    "filename": value["filename"],
                    "subfolder": str(value.get("subfolder", "")),
                    "type": str(value.get("type", "output")),
                })
            for nested in value.values():
                ComfyUIProvider._collect_output_refs(nested, found)
        elif isinstance(value, list):
            for nested in value:
                ComfyUIProvider._collect_output_refs(nested, found)

    def _download_output(self, ref: dict[str, str], target: Path) -> None:
        query = urllib.parse.urlencode(ref)
        request = urllib.request.Request(self._base_url() + "/view?" + query, headers=self._headers(), method="GET")
        try:
            with urllib.request.urlopen(request, timeout=300) as response:
                with target.open("wb") as handle:
                    shutil.copyfileobj(response, handle)
        except (urllib.error.HTTPError, urllib.error.URLError) as exc:
            raise RuntimeError(f"failed to download ComfyUI output {ref['filename']}: {exc}") from exc

    def _download_outputs(self, entry: dict[str, Any], output_dir: Path, job_id: str) -> tuple[list[str], str, str]:
        refs: list[dict[str, str]] = []
        self._collect_output_refs(entry.get("outputs", {}), refs)
        unique: list[dict[str, str]] = []
        seen: set[tuple[str, str, str]] = set()
        for ref in refs:
            key = (ref["filename"], ref["subfolder"], ref["type"])
            if key not in seen:
                seen.add(key)
                unique.append(ref)
        if not unique:
            raise RuntimeError("ComfyUI completed but no downloadable output files were reported")

        job_dir = output_dir / job_id
        job_dir.mkdir(parents=True, exist_ok=True)
        paths: list[str] = []
        primary: Path | None = None
        primary_kind = "file"
        for index, ref in enumerate(unique, start=1):
            source_name = Path(ref["filename"]).name
            suffix = Path(source_name).suffix.lower() or ".bin"
            target = job_dir / f"{index:02d}_{source_name}"
            self._download_output(ref, target)
            paths.append(str(target))
            if primary is None and suffix in self.VIDEO_EXTENSIONS:
                primary, primary_kind = target, "video"
        if primary is None:
            for path in map(Path, paths):
                if path.suffix.lower() in self.IMAGE_EXTENSIONS:
                    primary, primary_kind = path, "image"
                    break
        if primary is None:
            primary = Path(paths[0])
        return paths, str(primary), primary_kind

    def submit(self, *, prompt: str, negative_prompt: str, output_dir: Path, metadata: dict[str, Any]) -> dict[str, Any]:
        output_dir.mkdir(parents=True, exist_ok=True)
        workflow, resolved = self._load_workflow(prompt, negative_prompt, metadata)
        client_id = str(uuid.uuid4())
        response = self._request_json("POST", "/prompt", {"prompt": workflow, "client_id": client_id}, timeout=60)
        if not isinstance(response, dict) or not response.get("prompt_id"):
            raise RuntimeError(f"ComfyUI did not return prompt_id: {json.dumps(response, ensure_ascii=False)[:1200]}")
        prompt_id = str(response["prompt_id"])
        entry = self._wait_for_history(prompt_id)
        outputs, primary, kind = self._download_outputs(entry, output_dir, str(metadata["job_id"]))
        return {
            "status": "completed",
            "output_path": primary,
            "kind": kind,
            "outputs": outputs,
            "comfyui_prompt_id": prompt_id,
            "comfyui_client_id": client_id,
            "comfyui_url": self._base_url(),
            "render_parameters": {k.lower(): v for k, v in resolved.items() if k in {"SEED", "WIDTH", "HEIGHT", "FRAMES", "FPS", "DURATION_SECONDS", "ASPECT_RATIO"}},
        }


COMFYUI = ComfyUIProvider()

PROVIDERS: dict[str, VideoProvider] = {
    "mock": MockProvider(),
    "webhook": GenericWebhookProvider(),
    "comfyui": COMFYUI,
}


def get_provider(provider_id: str) -> VideoProvider:
    try:
        return PROVIDERS[provider_id]
    except KeyError as exc:
        raise ValueError(f"unknown provider: {provider_id}") from exc


def _configured(provider_id: str) -> bool:
    if provider_id == "mock":
        return True
    if provider_id == "webhook":
        return bool(os.getenv("ZMOVIE_PROVIDER_WEBHOOK", "").strip())
    if provider_id == "comfyui":
        return COMFYUI.configured()
    return False


def provider_specs() -> list[dict[str, Any]]:
    return [
        {
            "id": p.spec.id,
            "name": p.spec.name,
            "modes": list(p.spec.modes),
            "durations": list(p.spec.durations),
            "aspect_ratios": list(p.spec.aspect_ratios),
            "description": p.spec.description,
            "configured": _configured(p.spec.id),
        }
        for p in PROVIDERS.values()
    ]
