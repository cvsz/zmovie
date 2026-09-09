from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from . import bilibili_launch_candidate as launch

PRODUCTION_DURATION_SECONDS = 30
PRODUCTION_VOICE = "th-TH-PremwadeeNeural"
PRODUCTION_TTS_RATE = "-15%"
VOICE_START_SECONDS = 0.85
MIN_MUSIC_OUTRO_SECONDS = 1.5
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

    maximum_voice_seconds = (
        PRODUCTION_DURATION_SECONDS - VOICE_START_SECONDS - MIN_MUSIC_OUTRO_SECONDS
    )
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
        raise RuntimeError(
            f"production output duration mismatch: expected 30s, got {duration:.3f}s"
        )
    if str(media.get("codec") or "") != "h264":
        raise RuntimeError(f"production video codec mismatch: {media.get('codec')!r}")
    if int(media.get("width") or 0) != 1280 or int(media.get("height") or 0) != 720:
        raise RuntimeError(
            f"production resolution mismatch: {media.get('width')}x{media.get('height')}"
        )
    if str(media.get("audio_codec") or "") != "aac":
        raise RuntimeError(f"production audio codec mismatch: {media.get('audio_codec')!r}")
    if int(media.get("audio_sample_rate") or 0) != 48000:
        raise RuntimeError(
            f"production audio sample-rate mismatch: {media.get('audio_sample_rate')!r}"
        )
    if int(media.get("audio_channels") or 0) != 2:
        raise RuntimeError(
            f"production audio channel mismatch: {media.get('audio_channels')!r}"
        )
    if not bool(media.get("duration_locked")):
        raise RuntimeError("production render did not report duration_locked=true")


def create_production_candidate() -> dict[str, Any]:
    _enforce_production_tts()

    # Keep the stable renderer as the single source of truth while applying the
    # approved production narration for this one-click profile.
    launch.DEFAULT_VOICEOVER = APPROVED_VOICEOVER

    voice_duration = _voice_preflight()
    result = launch.create_launch_candidate(duration=PRODUCTION_DURATION_SECONDS)
    _validate_result(result)

    result["production_gen"] = {
        "profile": "thai-30s-voice-music-v1",
        "approved_voiceover": APPROVED_VOICEOVER,
        "tts_provider": "edge",
        "tts_voice": PRODUCTION_VOICE,
        "tts_rate": PRODUCTION_TTS_RATE,
        "voice_preflight_seconds": round(voice_duration, 3),
        "voice_start_seconds": VOICE_START_SECONDS,
        "minimum_music_outro_seconds": MIN_MUSIC_OUTRO_SECONDS,
        "target_duration_seconds": PRODUCTION_DURATION_SECONDS,
        "combined_voice_and_music": True,
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
