from __future__ import annotations

import os
import shutil
from pathlib import Path

from .storage import DB_PATH, ensure_database


def health_report() -> dict[str, object]:
    ensure_database()
    media_root = Path(os.getenv("ZMOVIE_MEDIA_ROOT", "data/media"))
    media_root.mkdir(parents=True, exist_ok=True)
    return {
        "status": "ok",
        "database": str(DB_PATH),
        "database_exists": DB_PATH.exists(),
        "media_root": str(media_root),
        "ffmpeg": bool(shutil.which("ffmpeg")),
        "ffprobe": bool(shutil.which("ffprobe")),
    }
