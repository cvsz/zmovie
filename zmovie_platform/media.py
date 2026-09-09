from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

from .models import Project

MEDIA_ROOT = Path(os.getenv("ZMOVIE_MEDIA_ROOT", "data/media"))


def ffmpeg_available() -> bool:
    return shutil.which("ffmpeg") is not None


def assemble_project(project: Project, clips: list[str], *, output_name: str | None = None) -> dict[str, Any]:
    MEDIA_ROOT.mkdir(parents=True, exist_ok=True)
    project_dir = MEDIA_ROOT / project.id
    project_dir.mkdir(parents=True, exist_ok=True)
    valid = [Path(item).resolve() for item in clips if item and Path(item).exists() and Path(item).suffix.lower() in {".mp4", ".mov", ".mkv", ".webm"}]
    if not valid:
        manifest = project_dir / "assembly.json"
        manifest.write_text(json.dumps({"project_id": project.id, "clips": clips, "status": "no-video-clips"}, indent=2), encoding="utf-8")
        return {"status": "manifest-only", "output_path": str(manifest), "clip_count": 0, "ffmpeg": ffmpeg_available()}
    if not ffmpeg_available():
        manifest = project_dir / "assembly.json"
        manifest.write_text(json.dumps({"project_id": project.id, "clips": [str(p) for p in valid], "status": "ffmpeg-unavailable"}, indent=2), encoding="utf-8")
        return {"status": "manifest-only", "output_path": str(manifest), "clip_count": len(valid), "ffmpeg": False}
    output = project_dir / (output_name or "final.mp4")
    concat = project_dir / "concat.txt"
    # concat demuxer file paths must be escaped for single quotes.
    lines = ["file '" + str(path).replace("'", "'\\''") + "'" for path in valid]
    concat.write_text("\n".join(lines) + "\n", encoding="utf-8")
    ffmpeg = shutil.which("ffmpeg")
    assert ffmpeg
    copy_cmd = [ffmpeg, "-y", "-f", "concat", "-safe", "0", "-i", str(concat), "-c", "copy", str(output)]
    proc = subprocess.run(copy_cmd, capture_output=True, text=True, timeout=1800, check=False)
    if proc.returncode != 0:
        # Normalize mixed provider outputs to a broadly compatible delivery format.
        transcode_cmd = [
            ffmpeg, "-y", "-f", "concat", "-safe", "0", "-i", str(concat),
            "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(output),
        ]
        proc = subprocess.run(transcode_cmd, capture_output=True, text=True, timeout=3600, check=False)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr[-2000:])
    return {"status": "completed", "output_path": str(output), "clip_count": len(valid), "ffmpeg": True}


def probe_media(path: str) -> dict[str, Any]:
    ffprobe = shutil.which("ffprobe")
    target = Path(path)
    if not target.exists():
        return {"exists": False, "path": path}
    info: dict[str, Any] = {"exists": True, "path": str(target), "size_bytes": target.stat().st_size}
    if not ffprobe:
        return info
    proc = subprocess.run(
        [ffprobe, "-v", "quiet", "-print_format", "json", "-show_format", "-show_streams", str(target)],
        capture_output=True, text=True, timeout=30, check=False,
    )
    if proc.returncode == 0:
        try:
            info["probe"] = json.loads(proc.stdout)
        except json.JSONDecodeError:
            pass
    return info
