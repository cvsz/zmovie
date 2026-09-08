from __future__ import annotations

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
    result: dict[str, object] = {
        "configured": configured,
        "reachable": False,
        "ready": False,
        "url": os.getenv("ZMOVIE_COMFYUI_URL", "http://127.0.0.1:8188").strip(),
        "workflow": os.getenv("ZMOVIE_COMFYUI_WORKFLOW", "").strip(),
    }
    if not configured:
        result["error"] = "workflow_not_configured"
        return result
    try:
        COMFYUI._request_json("GET", "/system_stats", timeout=2.0)
    except Exception as exc:
        result["error"] = str(exc)[:500]
        return result
    result["reachable"] = True
    result["ready"] = True
    return result


def health_report() -> dict[str, object]:
    ensure_database()
    media_root = Path(os.getenv("ZMOVIE_MEDIA_ROOT", "data/media"))
    export_root = Path(os.getenv("ZMOVIE_EXPORT_ROOT", "data/exports"))
    publish_root = Path(os.getenv("ZMOVIE_PUBLISH_ROOT", "data/publish"))
    ffmpeg = bool(shutil.which("ffmpeg"))
    ffprobe = bool(shutil.which("ffprobe"))
    comfyui = _comfyui_status()
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
        "render_ready": bool(ffmpeg and ffprobe and comfyui.get("ready")),
    }
