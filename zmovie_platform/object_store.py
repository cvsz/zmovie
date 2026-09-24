from __future__ import annotations

import os
from pathlib import Path

OBJECT_ROOT = Path(os.getenv("ZMOVIE_OBJECT_ROOT", "data/objects"))


def put(project_id: str, name: str, content: bytes) -> Path:
    if not project_id.replace("_", "").replace("-", "").isalnum():
        raise ValueError("invalid project id")
    base = OBJECT_ROOT.expanduser().resolve()
    root = (base / project_id).resolve()
    if root != base and base not in root.parents:
        raise ValueError("unsafe project path")
    root.mkdir(parents=True, exist_ok=True)
    target = root / Path(name).name
    target.write_bytes(content)
    return target
