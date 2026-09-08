from __future__ import annotations

from collections.abc import Callable
from typing import Any

_listeners: list[Callable[[str, dict[str, Any]], None]] = []


def subscribe(listener: Callable[[str, dict[str, Any]], None]) -> None:
    _listeners.append(listener)


def publish(name: str, payload: dict[str, Any]) -> None:
    for listener in tuple(_listeners):
        try:
            listener(name, payload)
        except Exception:
            continue
