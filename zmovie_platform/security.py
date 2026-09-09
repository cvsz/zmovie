from __future__ import annotations

import os
from pathlib import Path


def safe_project_path(root: Path, project_id: str, filename: str) -> Path:
    if not project_id.replace("_", "").isalnum():
        raise ValueError("invalid project id")
    clean = Path(filename).name
    target = (root / project_id / clean).resolve()
    base = (root / project_id).resolve()
    if base not in target.parents and target != base:
        raise ValueError("unsafe path")
    return target


_MANAGED_ROOTS = (
    ("ZMOVIE_MEDIA_ROOT", "data/media"),
    ("ZMOVIE_EXPORT_ROOT", "data/exports"),
    ("ZMOVIE_PUBLISH_ROOT", "data/publish"),
    ("ZMOVIE_OBJECT_ROOT", "data/objects"),
)


def managed_asset_roots() -> tuple[Path, ...]:
    return tuple(
        Path(os.getenv(name, default)).expanduser().resolve()
        for name, default in _MANAGED_ROOTS
    )


def validate_managed_asset_path(raw_path: str) -> Path:
    """Resolve an asset path and require it to remain below a managed root."""
    if not raw_path.strip():
        raise ValueError("asset path is required")
    try:
        candidate = Path(raw_path).expanduser().resolve()
    except (OSError, RuntimeError) as exc:
        raise ValueError("asset path cannot be resolved") from exc
    for root in managed_asset_roots():
        if candidate != root and root in candidate.parents:
            return candidate
    raise ValueError("asset path must be inside a managed media, export, publish, or object root")


SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
    "Content-Security-Policy": "default-src 'self'; img-src 'self' data:; media-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'; connect-src 'self'",
}
