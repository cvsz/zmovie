from __future__ import annotations

import shutil


def dependency_checks() -> dict[str, bool]:
    return {"ffmpeg": bool(shutil.which("ffmpeg")), "ffprobe": bool(shutil.which("ffprobe"))}
