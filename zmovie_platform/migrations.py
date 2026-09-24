from __future__ import annotations

from .commerce.store import ensure_tables as ensure_commerce_tables
from .models import utcnow
from .storage import connect, ensure_database
from .studio_cinema import ensure_tables as ensure_cinema_import_tables
from .ticketing.store import ensure_tables as ensure_ticketing_tables

# Versioned migration ledger. Each entry is applied idempotently; rollback
# is performed by restoring the pre-migration backup (see runbooks).
MIGRATION_VERSIONS = ("v2-base", "cinema-imports", "commerce", "ticketing")


def _record_versions() -> list[str]:
    with connect() as conn:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS schema_migrations("
            "version TEXT PRIMARY KEY, applied_at TEXT NOT NULL)")
        for version in MIGRATION_VERSIONS:
            conn.execute(
                "INSERT INTO schema_migrations(version, applied_at) VALUES(?, ?)"
                " ON CONFLICT(version) DO NOTHING",
                (version, utcnow()))
        rows = conn.execute("SELECT version FROM schema_migrations ORDER BY version").fetchall()
        return [row["version"] for row in rows]


def migrate() -> None:
    """Apply idempotent schema initialization/migrations.

    The v2 schema intentionally uses CREATE TABLE/INDEX IF NOT EXISTS so current
    deployments can upgrade without destructive migrations.
    """
    ensure_database()
    ensure_cinema_import_tables()
    ensure_commerce_tables()
    ensure_ticketing_tables()
    _record_versions()


def applied_versions() -> list[str]:
    """Versions recorded in the migration ledger (empty DB -> [].)."""
    with connect() as conn:
        try:
            rows = conn.execute("SELECT version FROM schema_migrations ORDER BY version").fetchall()
        except Exception:  # noqa: BLE001 - missing table means nothing applied
            return []
        return [row["version"] for row in rows]
