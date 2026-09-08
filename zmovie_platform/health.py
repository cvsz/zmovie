from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

from .providers import COMFYUI
from .storage import DB_PATH, ensure_database


def _path_status(path: Path) -> dict[str, object]:
    path.mkdir(parents=True, exist_ok=True)
    return {
        "path": str(path),
        "exists": path.exists(),
        "writable": os.access(path, os.W_OK),
    }


def _comfyui_status() -> dict[str, object]:
    configured = COMFYUI.configured()
    workflow_path = os.getenv("ZMOVIE_COMFYUI_WORKFLOW", "").strip()
    workflow_role = os.getenv("ZMOVIE_COMFYUI_WORKFLOW_ROLE", "generic").strip().lower() or "generic"
    result: dict[str, object] = {
        "configured": configured,
        "reachable": False,
        "workflow_valid": False,
        "nodes_available": False,
        "ready": False,
        "accelerated": False,
        "workflow_role": workflow_role,
        "url": os.getenv("ZMOVIE_COMFYUI_URL", "http://127.0.0.1:8188").strip(),
        "workflow": workflow_path,
    }

    # Probe the renderer independently from workflow configuration so operators
    # can distinguish "ComfyUI is down" from "ComfyUI is up but no workflow is
    # configured yet". Rendering readiness still requires both conditions.
    try:
        system_stats = COMFYUI._request_json("GET", "/system_stats", timeout=2.0)
        result["reachable"] = True
        if isinstance(system_stats, dict):
            system = system_stats.get("system")
            devices = system_stats.get("devices")
            if isinstance(system, dict):
                result["version"] = system.get("comfyui_version")
                result["python_version"] = system.get("python_version")
                result["pytorch_version"] = system.get("pytorch_version")
            if isinstance(devices, list):
                normalized_devices = [
                    {"name": item.get("name"), "type": item.get("type")}
                    for item in devices
                    if isinstance(item, dict)
                ]
                result["devices"] = normalized_devices
                result["accelerated"] = any(
                    str(item.get("type", "")).strip().lower() not in {"", "cpu"}
                    for item in normalized_devices
                )
    except Exception as exc:
        result["probe_error"] = str(exc)[:500]

    if not configured:
        result["error"] = "workflow_not_configured"
        return result

    try:
        workflow = json.loads(Path(workflow_path).expanduser().read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        result["error"] = f"workflow_invalid: {exc}"
        return result
    if not isinstance(workflow, dict) or not workflow:
        result["error"] = "workflow_invalid: API workflow must be a non-empty JSON object"
        return result
    result["workflow_valid"] = True

    if not result["reachable"]:
        result["error"] = result.get("probe_error", "comfyui_unreachable")
        return result

    try:
        required_node_types = sorted({
            str(node.get("class_type"))
            for node in workflow.values()
            if isinstance(node, dict) and node.get("class_type")
        })
        if required_node_types:
            object_info = COMFYUI._request_json("GET", "/object_info", timeout=5.0)
            available = set(object_info) if isinstance(object_info, dict) else set()
            missing = [name for name in required_node_types if name not in available]
            result["required_node_types"] = required_node_types
            result["missing_node_types"] = missing
            if missing:
                result["error"] = "missing_node_types"
                return result
        result["nodes_available"] = True
        result["ready"] = True
        result.pop("error", None)
        return result
    except Exception as exc:
        result["error"] = str(exc)[:500]
        return result


def health_report() -> dict[str, object]:
    ensure_database()
    media_root = Path(os.getenv("ZMOVIE_MEDIA_ROOT", "data/media"))
    export_root = Path(os.getenv("ZMOVIE_EXPORT_ROOT", "data/exports"))
    publish_root = Path(os.getenv("ZMOVIE_PUBLISH_ROOT", "data/publish"))
    ffmpeg = bool(shutil.which("ffmpeg"))
    ffprobe = bool(shutil.which("ffprobe"))
    comfyui = _comfyui_status()
    render_ready = bool(ffmpeg and ffprobe and comfyui.get("ready"))
    production_video_ready = bool(
        render_ready
        and comfyui.get("accelerated")
        and comfyui.get("workflow_role") == "video"
    )
    return {
        "status": "ok",
        "database": str(DB_PATH),
        "database_exists": DB_PATH.exists(),
        "media_root": str(media_root),
        "ffmpeg": ffmpeg,
        "ffprobe": ffprobe,
        "paths": {
            "media": _path_status(media_root),
            "exports": _path_status(export_root),
            "publish": _path_status(publish_root),
        },
        "comfyui": comfyui,
        "render_ready": render_ready,
        "production_video_ready": production_video_ready,
    }
