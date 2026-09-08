from __future__ import annotations

import shutil
from datetime import datetime, timezone
from pathlib import Path

from .storage import DB_PATH, ensure_database


def create_backup(root: Path = Path("data/backups")) -> Path:
    ensure_database()
    root.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    target = root / f"zmovie-{stamp}.db"
    shutil.copy2(DB_PATH, target)
    return target


def restore_backup(source: Path) -> Path:
    if not source.exists() or not source.is_file():
        raise FileNotFoundError(source)
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    temp = DB_PATH.with_suffix(".restore.tmp")
    shutil.copy2(source, temp)
    temp.replace(DB_PATH)
    return DB_PATH
