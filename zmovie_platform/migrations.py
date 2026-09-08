from __future__ import annotations

from .storage import ensure_database


def migrate() -> None:
    """Apply idempotent schema initialization/migrations.

    The v2 schema intentionally uses CREATE TABLE/INDEX IF NOT EXISTS so current
    deployments can upgrade without destructive migrations.
    """
    ensure_database()
