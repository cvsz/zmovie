from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
import time
from typing import Any

from .storage import connect

PBKDF2_ROUNDS = 250_000
TOKEN_TTL_SECONDS = int(os.getenv("ZMOVIE_TOKEN_TTL", "86400"))


def _secret() -> bytes:
    value = os.getenv("ZMOVIE_SECRET_KEY", "").strip()
    if not value:
        # Safe local default for zero-config development; production installer writes a random secret.
        value = "zmovie-local-development-secret-change-me"
    return value.encode("utf-8")


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ROUNDS)
    return f"pbkdf2_sha256${PBKDF2_ROUNDS}${base64.urlsafe_b64encode(salt).decode()}${base64.urlsafe_b64encode(digest).decode()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        algorithm, rounds, salt_b64, digest_b64 = stored.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        salt = base64.urlsafe_b64decode(salt_b64.encode())
        expected = base64.urlsafe_b64decode(digest_b64.encode())
        actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, int(rounds))
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError):
        return False


def create_user(username: str, password: str, role: str = "admin") -> dict[str, Any]:
    username = username.strip().lower()
    if len(username) < 3:
        raise ValueError("username must contain at least 3 characters")
    if len(password) < 10:
        raise ValueError("password must contain at least 10 characters")
    with connect() as conn:
        cur = conn.execute("INSERT INTO users(username,password_hash,role) VALUES(?,?,?)", (username, hash_password(password), role))
        return {"id": cur.lastrowid, "username": username, "role": role}


def authenticate(username: str, password: str) -> dict[str, Any] | None:
    with connect() as conn:
        row = conn.execute("SELECT id,username,password_hash,role FROM users WHERE username=?", (username.strip().lower(),)).fetchone()
    if row is None or not verify_password(password, row["password_hash"]):
        return None
    return {"id": row["id"], "username": row["username"], "role": row["role"]}


def user_count() -> int:
    with connect() as conn:
        return int(conn.execute("SELECT COUNT(*) FROM users").fetchone()[0])


def issue_token(user: dict[str, Any]) -> str:
    payload = {"sub": user["username"], "role": user.get("role", "user"), "iat": int(time.time()), "exp": int(time.time()) + TOKEN_TTL_SECONDS}
    raw = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    body = base64.urlsafe_b64encode(raw).rstrip(b"=")
    sig = hmac.new(_secret(), body, hashlib.sha256).digest()
    return body.decode() + "." + base64.urlsafe_b64encode(sig).rstrip(b"=").decode()


def decode_token(token: str) -> dict[str, Any] | None:
    try:
        body_text, sig_text = token.split(".", 1)
        body = body_text.encode()
        expected = hmac.new(_secret(), body, hashlib.sha256).digest()
        sig = base64.urlsafe_b64decode(sig_text + "=" * (-len(sig_text) % 4))
        if not hmac.compare_digest(sig, expected):
            return None
        raw = base64.urlsafe_b64decode(body_text + "=" * (-len(body_text) % 4))
        payload = json.loads(raw.decode("utf-8"))
        if int(payload.get("exp", 0)) < int(time.time()):
            return None
        return payload
    except (ValueError, TypeError, json.JSONDecodeError):
        return None


def bootstrap_admin_from_env() -> bool:
    if user_count() > 0:
        return False
    username = os.getenv("ZMOVIE_ADMIN_USER", "admin").strip() or "admin"
    password = os.getenv("ZMOVIE_ADMIN_PASSWORD", "").strip()
    if not password:
        return False
    create_user(username, password, "admin")
    return True
