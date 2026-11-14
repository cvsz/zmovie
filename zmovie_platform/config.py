from __future__ import annotations

import ipaddress
import os
from dataclasses import dataclass, field


def _read_secret_file(path: str | None) -> str:
    """อ่านรหัสลับจากไฟล์ (Docker /run/secrets pattern).

    คืนค่าสตริงว่างเมื่อยังไม่มีไฟล์ (สภาพแวดล้อมเดบิเคชันยังไม่ได้ mount)
    เพื่อให้ระบบเริ่มต้นได้โดยไม่ล้มเหลว แต่วิธีการผลิตจริงต้องมีไฟล์นี้.
    """
    if not path:
        return ""
    try:
        with open(path, encoding="utf-8") as fh:
            return fh.read().strip()
    except (OSError, FileNotFoundError):
        return ""


@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv("ZMOVIE_APP_NAME", "zMovie")
    host: str = os.getenv("ZMOVIE_HOST", "127.0.0.1")
    port: int = int(os.getenv("ZMOVIE_PORT", "8080"))
    auth_enabled: bool = os.getenv("ZMOVIE_AUTH_ENABLED", "true").lower() not in {"0", "false", "no", "off"}
    cors_origins: tuple[str, ...] = tuple(item.strip() for item in os.getenv("ZMOVIE_CORS_ORIGINS", "").split(",") if item.strip())
    base_url: str = os.getenv("ZMOVIE_BASE_URL", "").rstrip("/")
    oauth_enabled: bool = os.getenv("ZMOVIE_OAUTH_ENABLED", "true").lower() not in {"0", "false", "no", "off"}
    # ------------------------------------------------------------------
    # ฐานข้อมูลและแคชระดับองค์กร (ขั้นตอน 2.4: repo-name = zmovie)
    # user 'zmovie' ถูกสร้างใน PostgreSQL ก่อน déploy; รหัสผ่านอ่านจาก
    # /run/secrets/zmovie_postgres_password และ /run/secrets/zmovie_zredis_password
    # ------------------------------------------------------------------
    db_host: str = os.getenv("REPONAME_POSTGRES_HOST", "zpostgressql")
    db_port: int = int(os.getenv("REPONAME_POSTGRES_PORT", "5432"))
    db_user: str = os.getenv("REPONAME_POSTGRES_USER", "zmovie")
    db_name: str = os.getenv("REPONAME_POSTGRES_DB", "zmovie_db")
    db_password: str = field(
        default_factory=lambda: _read_secret_file(os.getenv("REPONAME_POSTGRES_PASSWORD_FILE"))
    )
    redis_host: str = os.getenv("REPONAME_REDIS_HOST", "zredis")
    redis_port: int = int(os.getenv("REPONAME_REDIS_PORT", "6379"))
    redis_password: str = field(
        default_factory=lambda: _read_secret_file(os.getenv("REPONAME_REDIS_PASSWORD_FILE"))
    )

    @property
    def database_dsn(self) -> str:
        """สร้าง PostgreSQL DSN จากค่าตั้งค่าและรหัสลับที่อ่านจากไฟล์ลับ."""
        return f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"

    @property
    def redis_url(self) -> str:
        """สร้าง Redis URL จากค่าตั้งค่าและรหัสลับที่อ่านจากไฟล์ลับ."""
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/0"
        return f"redis://{self.redis_host}:{self.redis_port}/0"


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


def validate_database_settings(config: Settings = settings) -> None:
    """ตรวจสอบการตั้งค่าฐานข้อมูลระดับองค์กรก่อนใช้งานจริง.

    บนโฮสต์.loopback อนุญาตให้ข้ามได้ (สภาพแวดล้อมพัฒนาใช้ SQLite เป็นค่าเริ่มต้น)
    แต่เมื่อเชื่อมฐานข้อมูลระยะไกลต้องมีไฟล์รหัสลับอยู่จริง.
    """
    if is_loopback_host(config.db_host):
        return
    password_file = os.getenv("REPONAME_POSTGRES_PASSWORD_FILE", "/run/secrets/zmovie_postgres_password")
    try:
        with open(password_file, encoding="utf-8") as fh:
            if not fh.read().strip():
                raise RuntimeError(f"PostgreSQL password file {password_file} is empty")
    except (OSError, FileNotFoundError) as exc:
        raise RuntimeError(
            f"PostgreSQL password file {password_file} must exist before connecting to remote database {config.db_host}"
        ) from exc
    redis_file = os.getenv("REPONAME_REDIS_PASSWORD_FILE", "/run/secrets/zmovie_zredis_password")
    try:
        with open(redis_file, encoding="utf-8") as fh:
            if not fh.read().strip():
                raise RuntimeError(f"Redis password file {redis_file} is empty")
    except (OSError, FileNotFoundError) as exc:
        raise RuntimeError(
            f"Redis password file {redis_file} must exist before connecting to remote cache {config.redis_host}"
        ) from exc
