from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from ..repository import delete_project, list_projects
from . import bilibili_launch_candidate as launch
from .bilibili import list_publish_jobs

PRODUCTION_DURATION_SECONDS = 30
PRODUCTION_VOICE = "th-TH-PremwadeeNeural"
PRODUCTION_TTS_RATE = launch.DEFAULT_TTS_RATE
PRODUCTION_MUSIC_GAIN = launch.DEFAULT_MUSIC_GAIN
PRODUCTION_PROFILE = "thai-30s-voice-music-v3"
VOICE_START_SECONDS = launch.DEFAULT_VOICE_START_SECONDS
MIN_MUSIC_OUTRO_SECONDS = 1.5
SAFE_SUPERSEDE_PUBLISH_STATUSES = {"prepared", "failed"}
_PROJECT_ID = re.compile(r"^prj_[A-Za-z0-9]+$")
APPROVED_VOICEOVER = (
    "พบกับ ซีมูฟวี่ จาก ซีแซดเดฟ แพลตฟอร์มผลิตวิดีโอแบบเซลฟ์โฮสต์ "
    "จากไอเดียสู่ผลงานพร้อมเผยแพร่ วางคอนเซ็ปต์ สร้างสตอรี่บอร์ด "
    "เรนเดอร์ ตรวจคุณภาพ และประกอบวิดีโอ ตรวจทานและอนุมัติก่อนเผยแพร่ผ่าน "
    "บิลิบิลิ ครีเอเตอร์ เซ็นเตอร์ ซีมูฟวี่ สร้าง เรนเดอร์ ตรวจสอบ และเผยแพร่ "
    "ในเวิร์กโฟลว์เดียว"
)


def _probe_duration(path: Path) -> float:
    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        raise RuntimeError("ffprobe is required for production generation")
    proc = subprocess.run(
        [
            ffprobe,
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(path),
        ],
        capture_output=True,
        text=True,
        timeout=30,
        check=True,
    )
    return float((proc.stdout or "0").strip() or 0)


def _enforce_production_tts() -> None:
    os.environ["ZMOVIE_TTS_PROVIDER"] = "edge"
    os.environ["ZMOVIE_TTS_VOICE"] = PRODUCTION_VOICE
    os.environ["ZMOVIE_TTS_ALLOW_LOCAL_FALLBACK"] = "false"


def _voice_preflight() -> float:
    with tempfile.TemporaryDirectory(prefix="zmovie-production-gen-") as tmp:
        result = launch._render_voiceover(Path(tmp), APPROVED_VOICEOVER)
        voice_path = Path(str(result["path"]))
        duration = _probe_duration(voice_path)

    maximum_voice_seconds = PRODUCTION_DURATION_SECONDS - VOICE_START_SECONDS - MIN_MUSIC_OUTRO_SECONDS
    if duration <= 0:
        raise RuntimeError("production voice preflight returned zero duration")
    if duration > maximum_voice_seconds:
        raise RuntimeError(
            "approved narration is too long for the 30-second production mix: "
            f"voice={duration:.3f}s, maximum={maximum_voice_seconds:.3f}s. "
            "Shorten the copy instead of speeding the Thai voice beyond the approved rate."
        )
    return duration


def _validate_result(result: dict[str, Any]) -> None:
    media = dict(result.get("media") or {})
    duration = float(media.get("duration_seconds") or 0)
    if abs(duration - PRODUCTION_DURATION_SECONDS) > 0.15:
        raise RuntimeError(f"production output duration mismatch: expected 30s, got {duration:.3f}s")
    if str(media.get("codec") or "") != "h264":
        raise RuntimeError(f"production video codec mismatch: {media.get('codec')!r}")
    if int(media.get("width") or 0) != 1280 or int(media.get("height") or 0) != 720:
        raise RuntimeError(f"production resolution mismatch: {media.get('width')}x{media.get('height')}")
    if str(media.get("audio_codec") or "") != "aac":
        raise RuntimeError(f"production audio codec mismatch: {media.get('audio_codec')!r}")
    if int(media.get("audio_sample_rate") or 0) != 48000:
        raise RuntimeError(f"production audio sample-rate mismatch: {media.get('audio_sample_rate')!r}")
    if int(media.get("audio_channels") or 0) != 2:
        raise RuntimeError(f"production audio channel mismatch: {media.get('audio_channels')!r}")
    if not bool(media.get("duration_locked")):
        raise RuntimeError("production render did not report duration_locked=true")
    if abs(float(media.get("voice_start_seconds") or 0) - VOICE_START_SECONDS) > 0.01:
        raise RuntimeError(
            "production voice-start mismatch: "
            f"expected {VOICE_START_SECONDS:.2f}s, got {float(media.get('voice_start_seconds') or 0):.3f}s"
        )
    if str(media.get("tts_rate") or "") != PRODUCTION_TTS_RATE:
        raise RuntimeError(
            f"production TTS rate mismatch: expected {PRODUCTION_TTS_RATE}, got {media.get('tts_rate')!r}"
        )
    if abs(float(media.get("music_gain") or 0) - PRODUCTION_MUSIC_GAIN) > 0.0001:
        raise RuntimeError(
            "production music-gain mismatch: "
            f"expected {PRODUCTION_MUSIC_GAIN:.3f}, got {float(media.get('music_gain') or 0):.3f}"
        )


def _is_production_candidate(item: dict[str, Any]) -> bool:
    project_id = str(item.get("id") or "")
    try:
        target_duration = int(item.get("target_duration_seconds") or 0)
    except (TypeError, ValueError):
        return False
    return bool(
        _PROJECT_ID.fullmatch(project_id)
        and str(item.get("owner") or "") == "zmovie-production"
        and str(item.get("name") or "") == launch.DEFAULT_NAME
        and str(item.get("concept") or "") == launch.DEFAULT_CONCEPT
        and target_duration == PRODUCTION_DURATION_SECONDS
    )


def _job_has_protected_publish_state(job: dict[str, Any]) -> bool:
    status = str(job.get("status") or "").strip().lower()
    metadata = dict(job.get("metadata") or {})
    if status not in SAFE_SUPERSEDE_PUBLISH_STATUSES:
        return True
    if str(job.get("published_url") or "").strip():
        return True
    return any(
        metadata.get(key)
        for key in (
            "approved_at",
            "submitted_at",
            "remote_confirmation",
            "remote_confirmed_at",
        )
    )


def _managed_roots() -> list[Path]:
    values = [
        os.getenv("ZMOVIE_MEDIA_ROOT", "data/media"),
        os.getenv("ZMOVIE_EXPORT_ROOT", "data/exports"),
        os.getenv("ZMOVIE_PUBLISH_ROOT", "data/publish"),
        os.getenv("ZMOVIE_OBJECT_ROOT", "data/objects"),
    ]
    roots: list[Path] = []
    seen: set[str] = set()
    for value in values:
        root = Path(value).expanduser().resolve()
        key = str(root)
        if key not in seen:
            seen.add(key)
            roots.append(root)
    return roots


def _remove_managed_project_dirs(project_id: str) -> dict[str, Any]:
    if not _PROJECT_ID.fullmatch(project_id):
        raise ValueError("refusing filesystem cleanup for an unsafe project id")
    removed: list[str] = []
    errors: list[str] = []
    for root in _managed_roots():
        target = root / project_id
        try:
            if target.is_symlink():
                target.unlink()
                removed.append(str(target))
            elif target.is_dir():
                shutil.rmtree(target)
                removed.append(str(target))
            elif target.exists():
                target.unlink()
                removed.append(str(target))
        except OSError as exc:
            errors.append(f"{target}: {exc}")
    return {"removed": removed, "errors": errors}


def _supersede_stale_candidates(current_project_id: str) -> dict[str, Any]:
    deleted: list[dict[str, Any]] = []
    preserved: list[dict[str, Any]] = []
    errors: list[str] = []

    for item in list_projects(limit=500):
        project_id = str(item.get("id") or "")
        if project_id == current_project_id or not _is_production_candidate(item):
            continue

        jobs = list_publish_jobs(project_id, limit=1000)
        protected_jobs = [job for job in jobs if _job_has_protected_publish_state(job)]
        if protected_jobs:
            preserved.append(
                {
                    "project_id": project_id,
                    "reason": "protected_publish_state",
                    "statuses": sorted({str(job.get("status") or "") for job in protected_jobs}),
                    "job_ids": sorted(str(job.get("id") or "") for job in protected_jobs),
                }
            )
            continue

        if not delete_project(project_id):
            errors.append(f"could not delete stale production project row: {project_id}")
            continue

        filesystem = _remove_managed_project_dirs(project_id)
        deleted.append(
            {
                "project_id": project_id,
                "publish_jobs_removed": len(jobs),
                "filesystem": filesystem,
            }
        )
        errors.extend(filesystem["errors"])

    return {
        "deleted": deleted,
        "preserved": preserved,
        "errors": errors,
        "cleanup_complete": not errors,
        "policy": "delete only exact-match stale candidates with no approved/submitted/published or other protected publish state",
    }


def create_production_candidate() -> dict[str, Any]:
    _enforce_production_tts()

    # Keep the stable renderer as the single source of truth while applying the
    # approved production narration and exact 1.2-second music intro.
    launch.DEFAULT_VOICEOVER = APPROVED_VOICEOVER
    launch.DEFAULT_VOICE_START_SECONDS = VOICE_START_SECONDS

    voice_duration = _voice_preflight()
    result = launch.create_launch_candidate(duration=PRODUCTION_DURATION_SECONDS)
    _validate_result(result)

    current_project_id = str(result.get("project_id") or "")
    cleanup = _supersede_stale_candidates(current_project_id)
    result["production_gen"] = {
        "profile": PRODUCTION_PROFILE,
        "approved_voiceover": APPROVED_VOICEOVER,
        "tts_provider": "edge",
        "tts_voice": PRODUCTION_VOICE,
        "tts_rate": PRODUCTION_TTS_RATE,
        "music_gain": PRODUCTION_MUSIC_GAIN,
        "voice_preflight_seconds": round(voice_duration, 3),
        "voice_start_seconds": VOICE_START_SECONDS,
        "minimum_music_outro_seconds": MIN_MUSIC_OUTRO_SECONDS,
        "target_duration_seconds": PRODUCTION_DURATION_SECONDS,
        "combined_voice_and_music": True,
        "supersede_cleanup": cleanup,
        "bilibili_upload_performed": False,
        "approval_performed": False,
    }
    return result


def main() -> int:
    try:
        print(json.dumps(create_production_candidate(), ensure_ascii=False, indent=2))
        return 0
    except Exception as exc:
        print(f"zMovie production-gen error: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
