from __future__ import annotations

import threading
import time
from collections import Counter
from typing import Any

_lock = threading.Lock()
_counts: Counter[str] = Counter()
_started = time.time()


def increment(name: str, amount: int = 1) -> None:
    with _lock:
        _counts[name] += amount


def snapshot() -> dict[str, Any]:
    with _lock:
        counts = dict(_counts)
    return {"uptime_seconds": round(time.time() - _started, 3), "counters": counts}
