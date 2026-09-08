from __future__ import annotations

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


SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
    "Content-Security-Policy": "default-src 'self'; img-src 'self' data:; media-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'; connect-src 'self'",
}
