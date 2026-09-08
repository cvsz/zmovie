from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

from . import bilibili as legacy
from ..repository import get_project

_VIDEO_EXTENSIONS = {".mp4", ".mov", ".mkv", ".webm", ".m4v"}
_SUBTITLE_EXTENSIONS = {".srt", ".vtt", ".ass"}
_NON_PRODUCTION_MARKERS = ("smoke", "mock", "test", "dry run", "dry-run")


def _root_from_env(name: str, default: str) -> Path:
    return Path(os.getenv(name, default)).expanduser().resolve()


def _is_within(path: Path, roots: list[Path]) -> bool:
    resolved = path.expanduser().resolve()
    for root in roots:
        try:
            resolved.relative_to(root)
            return True
        except ValueError:
            continue
    return False


def _probe_video(path: Path) -> dict[str, Any]:
    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        raise RuntimeError("ffprobe is required for Bilibili publication preflight")
    proc = subprocess.run(
        [
            ffprobe,
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=codec_name,width,height,r_frame_rate:format=duration,size",
            "-of",
            "json",
            str(path),
        ],
        capture_output=True,
        text=True,
        timeout=60,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"ffprobe rejected final video: {proc.stderr[-800:]}")
    try:
        data = json.loads(proc.stdout or "{}")
    except json.JSONDecodeError as exc:
        raise RuntimeError("ffprobe returned invalid JSON") from exc
    streams = list(data.get("streams") or [])
    if not streams:
        raise RuntimeError("final video has no readable video stream")
    stream = streams[0]
    width = int(stream.get("width") or 0)
    height = int(stream.get("height") or 0)
    if width <= 0 or height <= 0:
        raise RuntimeError("final video has invalid dimensions")
    try:
        duration = float((data.get("format") or {}).get("duration") or 0)
    except (TypeError, ValueError):
        duration = 0.0
    if duration <= 0:
        raise RuntimeError("final video has invalid duration")
    return {
        "codec": str(stream.get("codec_name") or ""),
        "width": width,
        "height": height,
        "frame_rate": str(stream.get("r_frame_rate") or ""),
        "duration_seconds": duration,
        "size_bytes": int((data.get("format") or {}).get("size") or path.stat().st_size),
    }


def preflight_publish_job(job_id: str, *, allow_non_production_name: bool = False) -> dict[str, Any]:
    job = legacy.get_publish_job(job_id)
    if job is None:
        raise ValueError("publish job not found")
    if job.get("platform") != "bilibili_tv":
        raise ValueError("publish job is not a Bilibili job")
    if job.get("status") != "approved":
        raise ValueError(f"preflight requires approved status, got {job.get('status')}")

    project = get_project(str(job.get("project_id") or ""))
    if project is None:
        raise ValueError("publish job project not found")
    identity = f"{project.name} {project.concept}".lower()
    marker = next((item for item in _NON_PRODUCTION_MARKERS if item in identity), "")
    if marker and not allow_non_production_name:
        raise RuntimeError(
            f"project looks non-production ({marker!r} marker); refuse real publication unless explicitly overridden"
        )

    media_root = _root_from_env("ZMOVIE_MEDIA_ROOT", "data/media")
    publish_root = _root_from_env("ZMOVIE_PUBLISH_ROOT", "data/publish")

    video = Path(str(job.get("video_path") or "")).expanduser().resolve()
    cover = Path(str(job.get("cover_path") or "")).expanduser().resolve()
    subtitle_text = str(job.get("subtitle_path") or "").strip()
    subtitle = Path(subtitle_text).expanduser().resolve() if subtitle_text else None

    if not video.is_file() or video.suffix.lower() not in _VIDEO_EXTENSIONS:
        raise RuntimeError(f"final video is missing or unsupported: {video}")
    if not _is_within(video, [media_root]):
        raise RuntimeError(f"final video is outside ZMOVIE_MEDIA_ROOT: {video}")
    if not cover.is_file() or cover.suffix.lower() not in {".jpg", ".jpeg", ".png", ".webp"}:
        raise RuntimeError(f"cover is missing or unsupported: {cover}")
    if not _is_within(cover, [publish_root, media_root]):
        raise RuntimeError(f"cover is outside approved media/publish roots: {cover}")
    if subtitle is not None:
        if not subtitle.is_file() or subtitle.suffix.lower() not in _SUBTITLE_EXTENSIONS:
            raise RuntimeError(f"subtitle is missing or unsupported: {subtitle}")
        if not _is_within(subtitle, [publish_root, media_root]):
            raise RuntimeError(f"subtitle is outside approved media/publish roots: {subtitle}")

    video_probe = _probe_video(video)
    return {
        "ready": True,
        "job_id": job_id,
        "project_id": project.id,
        "project_name": project.name,
        "status": job.get("status"),
        "video_path": str(video),
        "cover_path": str(cover),
        "subtitle_path": str(subtitle) if subtitle is not None else "",
        "media_root": str(media_root),
        "publish_root": str(publish_root),
        "video": video_probe,
        "approval_recorded": bool((job.get("metadata") or {}).get("approved_at")),
        "auto_publish": legacy.AUTO_PUBLISH,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Fail-closed preflight for a real Bilibili publication")
    parser.add_argument("--job", required=True)
    parser.add_argument("--allow-non-production-name", action="store_true")
    args = parser.parse_args(argv)
    try:
        print(
            json.dumps(
                preflight_publish_job(
                    args.job,
                    allow_non_production_name=args.allow_non_production_name,
                ),
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0
    except Exception as exc:
        print(f"Bilibili preflight error: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
