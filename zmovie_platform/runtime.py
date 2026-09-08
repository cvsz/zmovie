from __future__ import annotations

import os

AUTH_ENABLED = os.getenv("ZMOVIE_AUTH_ENABLED", "true").strip().lower() not in {"0", "false", "no", "off"}
