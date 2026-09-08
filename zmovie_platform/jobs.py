from __future__ import annotations

import concurrent.futures
from collections.abc import Callable
from typing import Any

_EXECUTOR = concurrent.futures.ThreadPoolExecutor(max_workers=4, thread_name_prefix="zmovie-job")


def submit(fn: Callable[..., Any], *args: Any, **kwargs: Any) -> concurrent.futures.Future[Any]:
    return _EXECUTOR.submit(fn, *args, **kwargs)
