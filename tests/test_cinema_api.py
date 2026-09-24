"""Smoke test: cinema-api service wiring (no network bind)."""
from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


def _load_service():
    path = Path(__file__).resolve().parent.parent / "services" / "cinema-api" / "app.py"
    spec = importlib.util.spec_from_file_location("cinema_api_app", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class CinemaApiSmokeTests(unittest.TestCase):
    def test_routes_registered(self) -> None:
        service = _load_service()

        paths = sorted({route.path for route in service.app.routes})
        for expected in (
            "/health",
            "/admin/seed",
            "/showtimes/{showtime_id}/availability",
            "/holds",
            "/reservations/confirm",
            "/reservations/cancel",
            "/tickets/check-in",
            "/admin/holds/sweep",
        ):
            self.assertIn(expected, paths)


if __name__ == "__main__":
    unittest.main()
