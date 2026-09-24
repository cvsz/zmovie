"""Media pipeline: validated uploads, FFprobe gate, transcoding, posters.

Production hooks for the Studio-to-Cinema boundary (injectable there).
All filesystem writes stay under managed roots; failures raise so the
caller records retryable job states.
"""
from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

from . import object_store
from .media import MEDIA_ROOT, probe_media
from .repository import list_assets

ALLOWED_SUFFIXES = {".mp4", ".mov", ".mkv", ".webm"}
ALLOWED_MIME = {
    ".mp4": {"video/mp4", "application/octet-stream"},
    ".mov": {"video/quicktime", "application/octet-stream"},
    ".mkv": {"video/x-matroska", "application/octet-stream"},
    ".webm": {"video/webm", "application/octet-stream"},
}
POSTER_SUFFIXES = {".jpg", ".png"}


def max_upload_bytes() -> int:
    return int(os.getenv("ZMOVIE_UPLOAD_MAX_MB", "500")) * 1024 * 1024


def max_files_per_project() -> int:
    return int(os.getenv("ZMOVIE_UPLOAD_MAX_FILES", "50"))


def validate_upload(*, project_id: str, filename: str, size_bytes: int, content_type: str) -> str:
    """Validate an upload request. Returns the safe stored name."""
    if size_bytes <= 0:
        raise ValueError("empty upload")
    if size_bytes > max_upload_bytes():
        raise ValueError("upload exceeds size limit")
    suffix = Path(filename).suffix.lower()
    if suffix not in ALLOWED_SUFFIXES:
        raise ValueError("unsupported media type")
    if content_type and content_type not in ALLOWED_MIME[suffix]:
        raise ValueError("content-type does not match file type")
    if len(list_assets(project_id)) >= max_files_per_project():
        raise ValueError("project file quota exceeded")
    clean = Path(filename).name
    if not clean or clean in {".", ".."}:
        raise ValueError("invalid filename")
    return clean


def store_upload(*, project_id: str, filename: str, content: bytes) -> Path:
    """Validate + persist an upload under the object root. Returns the path."""
    clean = validate_upload(
        project_id=project_id, filename=filename,
        size_bytes=len(content), content_type="")
    # Re-check size on real bytes (never trust the declared size).
    if len(content) > max_upload_bytes():
        raise ValueError("upload exceeds size limit")
    return object_store.put(project_id, clean, content)


def probe_gate(path: str, *, min_seconds: float = 1.0, min_width: int = 128) -> dict[str, Any]:
    """FFprobe quality gate: real video stream + minimum duration/dimensions."""
    info = probe_media(path)
    if not info.get("exists"):
        return {"passed": False, "reason": "media file not found", "info": info}
    streams = (info.get("probe") or {}).get("streams", [])
    video = next((s for s in streams if s.get("codec_type") == "video"), None)
    if video is None:
        return {"passed": False, "reason": "no video stream", "info": info}
    try:
        duration = float((info.get("probe") or {}).get("format", {}).get("duration", 0) or 0)
    except (TypeError, ValueError):
        duration = 0.0
    width = int(video.get("width") or 0)
    if duration < min_seconds:
        return {"passed": False, "reason": f"too short ({duration:.2f}s)", "info": info}
    if width < min_width:
        return {"passed": False, "reason": f"too narrow ({width}px)", "info": info}
    return {"passed": True, "duration": duration, "width": width,
            "codec": video.get("codec_name", ""), "info": info}


def _ffmpeg() -> str:
    exe = shutil.which("ffmpeg")
    if not exe:
        raise RuntimeError("ffmpeg unavailable")
    return exe


def transcode_to_streaming(src: str, dst: str) -> dict[str, Any]:
    """Transcode to streaming-compatible H.264/AAC (raises on failure)."""
    ffmpeg = _ffmpeg()
    Path(dst).parent.mkdir(parents=True, exist_ok=True)
    proc = subprocess.run(
        [ffmpeg, "-y", "-i", src, "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
         "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", dst],
        capture_output=True, text=True, timeout=1800, check=False)
    if proc.returncode != 0 or not Path(dst).exists():
        raise RuntimeError((proc.stderr or "transcode failed")[-2000:])
    return {"ok": True, "output": dst}


def poster_frame(src: str, dst: str, *, at_seconds: float = 1.0) -> dict[str, Any]:
    """Extract a poster frame (raises on failure)."""
    ffmpeg = _ffmpeg()
    if Path(dst).suffix.lower() not in POSTER_SUFFIXES:
        raise ValueError("poster must be .jpg or .png")
    Path(dst).parent.mkdir(parents=True, exist_ok=True)
    proc = subprocess.run(
        [ffmpeg, "-y", "-ss", str(at_seconds), "-i", src, "-frames:v", "1", dst],
        capture_output=True, text=True, timeout=300, check=False)
    if proc.returncode != 0 or not Path(dst).exists():
        raise RuntimeError((proc.stderr or "poster failed")[-2000:])
    return {"ok": True, "output": dst}


def default_transcode_hook(media_path: str) -> dict[str, Any]:
    """Production transcode hook for studio_cinema.run_import (sidecar output)."""
    src = Path(media_path)
    dst = src.parent / (src.stem + ".streaming.mp4")
    return transcode_to_streaming(str(src), str(dst))


def default_poster_hook(media_path: str) -> dict[str, Any]:
    """Production poster hook for studio_cinema.run_import."""
    src = Path(media_path)
    dst = src.parent / (src.stem + ".poster.jpg")
    return poster_frame(str(src), str(dst))


def media_dir_for_project(project_id: str) -> Path:
    target = (MEDIA_ROOT / project_id).resolve()
    target.mkdir(parents=True, exist_ok=True)
    return target
