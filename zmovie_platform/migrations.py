from __future__ import annotations

from .storage import ensure_database
from .studio_cinema import ensure_tables as ensure_cinema_import_tables


def migrate() -> None:
    """Apply idempotent schema initialization/migrations.

    The v2 schema intentionally uses CREATE TABLE/INDEX IF NOT EXISTS so current
    deployments can upgrade without destructive migrations.
    """
    ensure_database()
    ensure_cinema_import_tables()
