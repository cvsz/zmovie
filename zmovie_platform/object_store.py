from __future__ import annotations

import os
from pathlib import Path

OBJECT_ROOT = Path(os.getenv("ZMOVIE_OBJECT_ROOT", "data/objects"))


def put(project_id: str, name: str, content: bytes) -> Path:
    root = (OBJECT_ROOT / project_id).resolve()
    root.mkdir(parents=True, exist_ok=True)
    target = root / Path(name).name
    target.write_bytes(content)
    return target
