from __future__ import annotations

import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

from .storage import DB_PATH, ensure_database


def _verify_database(path: Path) -> None:
    with closing(sqlite3.connect(path)) as conn:
        result = conn.execute("PRAGMA quick_check").fetchone()
        if result is None or str(result[0]).lower() != "ok":
            raise RuntimeError(f"SQLite integrity check failed for {path}: {result}")
        violations = conn.execute("PRAGMA foreign_key_check").fetchall()
        if violations:
            raise RuntimeError(f"SQLite foreign-key check failed for {path}: {violations[:10]}")


def create_backup(root: Path = Path("data/backups")) -> Path:
    """Create a transactionally consistent SQLite backup, including WAL data."""

    ensure_database()
    root.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    target = root / f"zmovie-{stamp}.db"
    temp = target.with_suffix(".tmp")
    temp.unlink(missing_ok=True)

    try:
        with closing(sqlite3.connect(DB_PATH)) as source, closing(sqlite3.connect(temp)) as destination:
            source.backup(destination)
            destination.commit()
        _verify_database(temp)
        temp.replace(target)
    finally:
        temp.unlink(missing_ok=True)

    return target


def restore_backup(source: Path) -> Path:
    """Restore a verified SQLite backup through SQLite's online backup API."""

    source = source.expanduser().resolve()
    if not source.exists() or not source.is_file():
        raise FileNotFoundError(source)
    _verify_database(source)

    ensure_database()
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(source)) as backup_conn, closing(sqlite3.connect(DB_PATH)) as destination:
        backup_conn.backup(destination)
        destination.commit()
    _verify_database(DB_PATH)
    return DB_PATH
