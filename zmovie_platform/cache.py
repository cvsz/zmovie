from __future__ import annotations

from functools import lru_cache


@lru_cache(maxsize=256)
def normalize_style(value: str) -> str:
    return " ".join(value.strip().split())
