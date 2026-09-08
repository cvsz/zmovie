from __future__ import annotations

from .health import health_report
from .providers import provider_specs


def capabilities() -> dict[str, object]:
    return {"health": health_report(), "providers": provider_specs(), "features": ["prompt-generator", "projects", "character-bible", "storyboard", "qc", "render-jobs", "asset-library", "ffmpeg-assembly", "production-export", "authentication", "audit"]}
