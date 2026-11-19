"""Provider specification dataclass.

Extracted into its own module to avoid circular imports between
providers.py and individual provider modules.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ProviderSpec:
    id: str
    name: str
    modes: tuple[str, ...]
    durations: tuple[int, ...]
    aspect_ratios: tuple[str, ...]
    description: str
