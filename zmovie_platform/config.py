from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv("ZMOVIE_APP_NAME", "zMovie")
    host: str = os.getenv("ZMOVIE_HOST", "0.0.0.0")
    port: int = int(os.getenv("ZMOVIE_PORT", "8080"))
    auth_enabled: bool = os.getenv("ZMOVIE_AUTH_ENABLED", "true").lower() not in {"0", "false", "no", "off"}
    cors_origins: tuple[str, ...] = tuple(item.strip() for item in os.getenv("ZMOVIE_CORS_ORIGINS", "").split(",") if item.strip())


settings = Settings()
