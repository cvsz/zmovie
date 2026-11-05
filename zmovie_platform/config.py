from __future__ import annotations

import ipaddress
import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv("ZMOVIE_APP_NAME", "zMovie")
    host: str = os.getenv("ZMOVIE_HOST", "127.0.0.1")
    port: int = int(os.getenv("ZMOVIE_PORT", "8080"))
    auth_enabled: bool = os.getenv("ZMOVIE_AUTH_ENABLED", "true").lower() not in {"0", "false", "no", "off"}
    cors_origins: tuple[str, ...] = tuple(item.strip() for item in os.getenv("ZMOVIE_CORS_ORIGINS", "").split(",") if item.strip())
    base_url: str = os.getenv("ZMOVIE_BASE_URL", "").rstrip("/")
    oauth_enabled: bool = os.getenv("ZMOVIE_OAUTH_ENABLED", "true").lower() not in {"0", "false", "no", "off"}


settings = Settings()


def is_loopback_host(host: str) -> bool:
    normalized = host.strip().lower()
    if normalized == "localhost":
        return True
    try:
        return ipaddress.ip_address(normalized).is_loopback
    except ValueError:
        return False


def validate_runtime_settings(config: Settings = settings) -> None:
    """ปฏิเสธการเริ่มระบบเมื่อ bind ออกนอก loopback โดยไม่มีการป้องกันที่กำหนด."""
    if is_loopback_host(config.host):
        return
    if not config.auth_enabled:
        raise RuntimeError("ZMOVIE_AUTH_ENABLED must be true when binding beyond loopback")
    secret = os.getenv("ZMOVIE_SECRET_KEY", "").strip()
    if len(secret) < 32:
        raise RuntimeError("ZMOVIE_SECRET_KEY must contain at least 32 characters when binding beyond loopback")
